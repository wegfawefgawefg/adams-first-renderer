from __future__ import annotations

from pathlib import Path

from afr.linalg.mat4 import Mat4
from afr.linalg.vec2 import Vec2
from afr.linalg.vec3 import Vec3
from afr.models.mtl import load_mtl
from afr.scene import Material, Mesh, Primitive, SceneData


def _parse_index(s: str, n: int) -> int:
    # OBJ indices are 1-based; negative indices are relative to end.
    i = int(s)
    if i < 0:
        return n + i
    return i - 1


def load_obj(path: str | Path) -> SceneData:
    """Load a minimal subset of Wavefront OBJ (+MTL).

    Supports:
    - v, vt
    - f with v/vt or v
    - mtllib (best-effort resolution)
    - usemtl (splits into primitives by material)
    """
    p = Path(path)
    base_dir = p.parent
    proj_root = p.resolve().parents[2]
    tex_dir = proj_root / "assets" / "textures"
    mtl_dir = proj_root / "assets" / "materials"

    positions: list[Vec3] = []
    uvs: list[Vec2] = []

    materials: dict[str, Material] = {}
    current_mtl = "default"

    # Per material group we build a separate mesh with unified indexing.
    groups: dict[str, dict] = {}

    def group(name: str) -> dict:
        g = groups.get(name)
        if g is None:
            g = {
                "v": [],  # positions
                "vt": [],  # uvs
                "idx": [],  # triangle indices
                "map": {},  # (pi, ti) -> new index
            }
            groups[name] = g
        return g

    for raw in p.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if not parts:
            continue
        cmd = parts[0]
        args = parts[1:]

        if cmd == "mtllib" and args:
            mtl_name = args[-1]
            # Try relative to OBJ first, then assets/materials.
            cand = base_dir / mtl_name
            if not cand.exists():
                cand = mtl_dir / mtl_name
            if cand.exists():
                materials.update(load_mtl(cand, extra_texture_dirs=[base_dir, tex_dir, mtl_dir]))
            continue

        if cmd == "usemtl" and args:
            current_mtl = " ".join(args)
            continue

        if cmd == "v" and len(args) >= 3:
            positions.append(Vec3(float(args[0]), float(args[1]), float(args[2])))
            continue

        if cmd == "vt" and len(args) >= 2:
            # OBJ v is usually bottom-up; we keep as-is for now.
            uvs.append(Vec2(float(args[0]), float(args[1])))
            continue

        if cmd == "f" and len(args) >= 3:
            # Triangulate polygon by fan.
            verts = []
            for tok in args:
                # token like v/vt/vn or v/vt or v
                fields = tok.split("/")
                vi = _parse_index(fields[0], len(positions))
                ti = _parse_index(fields[1], len(uvs)) if len(fields) >= 2 and fields[1] else None
                verts.append((vi, ti))

            g = group(current_mtl)
            for i in range(1, len(verts) - 1):
                tri = (verts[0], verts[i], verts[i + 1])
                out_idx = []
                for (vi, ti) in tri:
                    key = (vi, ti)
                    mi = g["map"].get(key)
                    if mi is None:
                        mi = len(g["v"])
                        g["map"][key] = mi
                        g["v"].append(positions[vi])
                        if ti is not None and ti < len(uvs):
                            g["vt"].append(uvs[ti])
                        else:
                            g["vt"].append(Vec2(0.0, 0.0))
                    out_idx.append(mi)
                g["idx"].append((out_idx[0], out_idx[1], out_idx[2]))
            continue

    prims: list[Primitive] = []
    for mtl_name, g in groups.items():
        mat = materials.get(mtl_name) or Material(name=mtl_name)
        mesh = Mesh(
            positions=g["v"],
            uvs=g["vt"] if g["vt"] else None,
            indices=g["idx"],
        )
        prims.append(Primitive(mesh=mesh, material=mat, local_to_world=Mat4.identity()))

    return SceneData(primitives=prims)

