from __future__ import annotations

from pathlib import Path

from afr.linalg.mat4 import Mat4
from afr.linalg.vec2 import Vec2
from afr.scene import Material, Mesh, Primitive, SceneData
from afr.models.model import Model


def load_afrmodel(path: str | Path) -> SceneData:
    """Load .afrmodel and convert to engine Mesh/Primitive.

    Note: .afrmodel stores UVs per-face. For simplicity we unindex into a
    per-vertex UV stream so the renderer can use per-vertex attributes.
    """
    m = Model.load(path)

    out_pos = []
    out_uv = []
    out_idx = []

    if m.uvs and len(m.uvs) == len(m.faces):
        for fi, (i1, i2, i3) in enumerate(m.faces):
            uv1, uv2, uv3 = m.uvs[fi]
            base = len(out_pos)
            out_pos.extend([m.verts[i1], m.verts[i2], m.verts[i3]])
            out_uv.extend([uv1, uv2, uv3])
            out_idx.append((base + 0, base + 1, base + 2))
    else:
        out_pos = m.verts
        out_uv = None
        out_idx = m.faces

    mesh = Mesh(positions=out_pos, uvs=out_uv, indices=out_idx)
    prim = Primitive(mesh=mesh, material=Material(name=Path(path).stem), local_to_world=Mat4.identity())
    return SceneData(primitives=[prim])

