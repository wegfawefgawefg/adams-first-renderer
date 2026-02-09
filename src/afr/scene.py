from __future__ import annotations

from dataclasses import dataclass, field

from afr.linalg.mat4 import Mat4
from afr.linalg.vec2 import Vec2
from afr.linalg.vec3 import Vec3


@dataclass
class Texture:
    # For now, just wrap a pygame.Surface (kept as object to avoid importing pygame everywhere).
    surface: object


@dataclass
class Material:
    name: str = "default"
    base_color: Vec3 = Vec3(1.0, 1.0, 1.0)  # 0..1
    base_color_tex: Texture | None = None


@dataclass
class Mesh:
    positions: list[Vec3]
    uvs: list[Vec2] | None
    indices: list[tuple[int, int, int]]  # triangle list


@dataclass
class Primitive:
    mesh: Mesh
    material: Material
    local_to_world: Mat4 = field(default_factory=Mat4.identity)
    # Backface culling configuration.
    # Many real assets (especially OBJ) may have inconsistent winding; when in
    # doubt, set cull_backfaces=False for that primitive.
    cull_backfaces: bool = True
    # Front-face winding in NDC (y up). glTF convention is CCW.
    front_face_ccw: bool = True


@dataclass
class SceneData:
    primitives: list[Primitive]
