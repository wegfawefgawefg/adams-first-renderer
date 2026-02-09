from __future__ import annotations

from dataclasses import dataclass

from afr.linalg.mat4 import Mat4
from afr.linalg.vec2 import Vec2
from afr.linalg.vec3 import Vec3
from afr.scene import Mesh, Material, Primitive
from afr.primitives import triangle_filled_z, triangle_textured_z


@dataclass
class Camera:
    pos: Vec3
    target: Vec3
    up: Vec3 = Vec3(0.0, 1.0, 0.0)

    def view(self) -> Mat4:
        return Mat4.look_at(self.pos, self.target, self.up)


@dataclass
class PointLight:
    pos: Vec3
    color: Vec3 = Vec3(1.0, 1.0, 1.0)  # 0..1
    intensity: float = 1.0


@dataclass
class Scene:
    lights: list[PointLight]
    ambient: float = 0.15


def ndc_to_screen(ndc: Vec3, w: int, h: int) -> Vec3:
    # Map NDC [-1,1] to pixel coords [0,w-1] and [0,h-1].
    x = (ndc.x * 0.5 + 0.5) * (w - 1)
    # Pygame's y axis is down; flip so +Y is up in world.
    y = (1.0 - (ndc.y * 0.5 + 0.5)) * (h - 1)
    return Vec3(x, y, ndc.z)


def ortho_for_surface(
    w: int, h: int, half_height: float, near: float = 0.1, far: float = 100.0
) -> Mat4:
    aspect = (w / h) if h else 1.0
    half_width = half_height * aspect
    return Mat4.ortho(-half_width, half_width, -half_height, half_height, near, far)


def shade_flat(scene: Scene, normal_ws: Vec3, pos_ws: Vec3) -> Vec3:
    n = normal_ws.norm()
    s = Vec3.splat(float(scene.ambient))
    for light in scene.lights:
        ldir = (light.pos - pos_ws).norm()
        ndotl = max(0.0, n.dot(ldir)) * float(light.intensity)
        s = s + (light.color * ndotl)
    # clamp >= 0 (let it go above 1.0 if you want "hot" lights later)
    return s.clamp(0.0, 1e9)


def draw_model(
    surface,
    mesh: Mesh,
    material: Material,
    model_mat: Mat4,
    view_mat: Mat4,
    proj_mat: Mat4,
    *,
    scene: Scene | None = None,
    zbuf: list[float] | None = None,
) -> None:
    sw = surface.get_width()
    sh = surface.get_height()
    if zbuf is None:
        zbuf = [float("inf")] * (sw * sh)

    viewproj = proj_mat @ view_mat
    verts_ms = mesh.positions
    verts_ws = [model_mat @ v for v in verts_ms]
    verts_ndc = [viewproj @ v for v in verts_ws]
    verts_ss = [ndc_to_screen(v, sw, sh) for v in verts_ndc]

    tex_surface = material.base_color_tex.surface if material.base_color_tex else None
    use_tex = tex_surface is not None and mesh.uvs is not None
    use_scene = scene is not None

    for (i1, i2, i3) in mesh.indices:
        p1s, p2s, p3s = verts_ss[i1], verts_ss[i2], verts_ss[i3]

        # Flat normal in world space for now.
        if use_scene:
            p1w, p2w, p3w = verts_ws[i1], verts_ws[i2], verts_ws[i3]
            n = (p2w - p1w).cross(p3w - p1w).norm()
            c = (p1w + p2w + p3w) * (1.0 / 3.0)
            shade = shade_flat(scene, n, c)
        else:
            shade = Vec3.splat(1.0)

        if use_tex:
            uv1, uv2, uv3 = mesh.uvs[i1], mesh.uvs[i2], mesh.uvs[i3]
            shade = shade * material.base_color
            triangle_textured_z(
                surface, p1s, p2s, p3s, uv1, uv2, uv3, tex_surface, zbuf, shade=shade
            )
        else:
            col = (shade * material.base_color).clamp(0.0, 1.0)
            c255 = (int(255 * col.x), int(255 * col.y), int(255 * col.z), 255)
            triangle_filled_z(surface, p1s, p2s, p3s, c255, zbuf)


def draw_primitive(
    surface,
    prim: Primitive,
    world_mat: Mat4,
    view_mat: Mat4,
    proj_mat: Mat4,
    *,
    scene: Scene | None = None,
    zbuf: list[float] | None = None,
) -> None:
    draw_model(
        surface,
        prim.mesh,
        prim.material,
        world_mat @ prim.local_to_world,
        view_mat,
        proj_mat,
        scene=scene,
        zbuf=zbuf,
    )
