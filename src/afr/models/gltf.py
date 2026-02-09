from __future__ import annotations

import base64
import json
import struct
from dataclasses import dataclass
from pathlib import Path

import pygame

from afr.linalg.mat4 import Mat4
from afr.linalg.vec2 import Vec2
from afr.linalg.vec3 import Vec3
from afr.models.model import Model


_COMPONENT_FMT = {
    5120: ("b", 1),   # BYTE
    5121: ("B", 1),   # UNSIGNED_BYTE
    5122: ("h", 2),   # SHORT
    5123: ("H", 2),   # UNSIGNED_SHORT
    5125: ("I", 4),   # UNSIGNED_INT
    5126: ("f", 4),   # FLOAT
}

_TYPE_COUNT = {
    "SCALAR": 1,
    "VEC2": 2,
    "VEC3": 3,
    "VEC4": 4,
    "MAT2": 4,
    "MAT3": 9,
    "MAT4": 16,
}


def _quat_to_mat4(q) -> Mat4:
    # glTF quaternion is [x, y, z, w]
    x, y, z, w = (float(q[0]), float(q[1]), float(q[2]), float(q[3]))
    xx = x * x
    yy = y * y
    zz = z * z
    xy = x * y
    xz = x * z
    yz = y * z
    wx = w * x
    wy = w * y
    wz = w * z

    # 3x3 rotation matrix (row-major)
    r00 = 1.0 - 2.0 * (yy + zz)
    r01 = 2.0 * (xy - wz)
    r02 = 2.0 * (xz + wy)
    r10 = 2.0 * (xy + wz)
    r11 = 1.0 - 2.0 * (xx + zz)
    r12 = 2.0 * (yz - wx)
    r20 = 2.0 * (xz - wy)
    r21 = 2.0 * (yz + wx)
    r22 = 1.0 - 2.0 * (xx + yy)

    return Mat4(
        [
            r00, r01, r02, 0.0,
            r10, r11, r12, 0.0,
            r20, r21, r22, 0.0,
            0.0, 0.0, 0.0, 1.0,
        ]
    )


def _node_local_mat(node: dict) -> Mat4:
    if "matrix" in node:
        m = [float(x) for x in node["matrix"]]
        # glTF matrix is column-major; our Mat4 is row-major.
        # Convert by transposing.
        return Mat4(
            [
                m[0], m[4], m[8], m[12],
                m[1], m[5], m[9], m[13],
                m[2], m[6], m[10], m[14],
                m[3], m[7], m[11], m[15],
            ]
        )

    t = node.get("translation", [0.0, 0.0, 0.0])
    r = node.get("rotation", [0.0, 0.0, 0.0, 1.0])
    s = node.get("scale", [1.0, 1.0, 1.0])

    mt = Mat4.translate(t[0], t[1], t[2])
    mr = _quat_to_mat4(r)
    ms = Mat4.scale(s[0], s[1], s[2])
    return mt @ mr @ ms


def _load_buffer(uri: str, base_dir: Path) -> bytes:
    if uri.startswith("data:"):
        # data:application/octet-stream;base64,...
        _, b64 = uri.split(",", 1)
        return base64.b64decode(b64)
    return (base_dir / uri).read_bytes()


def _read_accessor(gltf: dict, buffers: list[bytes], accessor_idx: int) -> list:
    acc = gltf["accessors"][accessor_idx]
    bv = gltf["bufferViews"][acc["bufferView"]]
    buf = buffers[bv["buffer"]]

    comp_type = acc["componentType"]
    fmt, comp_size = _COMPONENT_FMT[comp_type]
    ncomp = _TYPE_COUNT[acc["type"]]
    count = int(acc["count"])

    byte_offset = int(bv.get("byteOffset", 0)) + int(acc.get("byteOffset", 0))
    stride = int(bv.get("byteStride", comp_size * ncomp))

    out = []
    for i in range(count):
        off = byte_offset + i * stride
        vals = struct.unpack_from("<" + fmt * ncomp, buf, off)
        out.append(vals)
    return out


def _load_image_surface(img_uri: str, base_dir: Path):
    p = base_dir / img_uri
    surf = pygame.image.load(str(p))
    if pygame.display.get_surface() is not None:
        surf = surf.convert_alpha()
    return surf


@dataclass
class Primitive:
    model: Model
    texture: object | None
    local_mat: Mat4

    def __iter__(self):
        yield self.model
        yield self.texture
        yield self.local_mat


def load_gltf_scene(path: str | Path) -> list[Primitive]:
    """Load a subset of glTF 2.0 (enough to view textured static meshes).

    Supports:
    - .gltf JSON with external .bin
    - node hierarchy with TRS or matrix
    - mesh primitives with POSITION, TEXCOORD_0, and indices
    - baseColorTexture images (png/jpg)
    """
    p = Path(path)
    base_dir = p.parent
    gltf = json.loads(p.read_text(encoding="utf-8"))

    buffers = [_load_buffer(b["uri"], base_dir) for b in gltf.get("buffers", [])]

    # Load textures (image surfaces) referenced by materials.
    images = gltf.get("images", [])
    textures = gltf.get("textures", [])
    materials = gltf.get("materials", [])

    image_surfaces: list[object | None] = [None] * len(images)

    def tex_for_material(mat_idx: int) -> object | None:
        if mat_idx is None or mat_idx < 0 or mat_idx >= len(materials):
            return None
        mat = materials[mat_idx]
        pbr = mat.get("pbrMetallicRoughness", {})
        bct = pbr.get("baseColorTexture")
        if not bct:
            return None
        tex_idx = int(bct.get("index", -1))
        if tex_idx < 0 or tex_idx >= len(textures):
            return None
        src_idx = int(textures[tex_idx].get("source", -1))
        if src_idx < 0 or src_idx >= len(images):
            return None
        if image_surfaces[src_idx] is None:
            uri = images[src_idx].get("uri")
            if uri is None:
                return None
            image_surfaces[src_idx] = _load_image_surface(uri, base_dir)
        return image_surfaces[src_idx]

    # Traverse the scene graph and collect primitives.
    nodes = gltf.get("nodes", [])
    meshes = gltf.get("meshes", [])
    scenes = gltf.get("scenes", [])
    scene_idx = int(gltf.get("scene", 0))
    root_nodes = scenes[scene_idx].get("nodes", []) if scenes else list(range(len(nodes)))

    prims: list[Primitive] = []

    def visit(node_idx: int, parent_mat: Mat4):
        node = nodes[node_idx]
        local = _node_local_mat(node)
        world = parent_mat @ local

        mesh_idx = node.get("mesh")
        if mesh_idx is not None:
            mesh = meshes[int(mesh_idx)]
            for prim in mesh.get("primitives", []):
                attrs = prim.get("attributes", {})
                pos_idx = attrs.get("POSITION")
                uv_idx = attrs.get("TEXCOORD_0")
                ind_idx = prim.get("indices")
                if pos_idx is None or ind_idx is None:
                    continue

                positions = _read_accessor(gltf, buffers, int(pos_idx))
                uvs = _read_accessor(gltf, buffers, int(uv_idx)) if uv_idx is not None else None
                indices = _read_accessor(gltf, buffers, int(ind_idx))

                verts = [Vec3(x, y, z) for (x, y, z) in positions]
                faces = []
                face_uvs = []

                # indices accessor is SCALAR; may be uint/ushort.
                flat = [int(i[0]) for i in indices]
                for i in range(0, len(flat), 3):
                    i1, i2, i3 = flat[i], flat[i + 1], flat[i + 2]
                    faces.append((i1, i2, i3))
                    if uvs is not None:
                        u1, v1 = uvs[i1]
                        u2, v2 = uvs[i2]
                        u3, v3 = uvs[i3]
                        face_uvs.append((Vec2(u1, v1), Vec2(u2, v2), Vec2(u3, v3)))

                model = Model(verts=verts, faces=faces, uvs=face_uvs if face_uvs else [])
                tex = tex_for_material(prim.get("material", -1))
                prims.append(Primitive(model=model, texture=tex, local_mat=world))

        for child in node.get("children", []):
            visit(int(child), world)

    ident = Mat4.identity()
    for n in root_nodes:
        visit(int(n), ident)

    return prims
