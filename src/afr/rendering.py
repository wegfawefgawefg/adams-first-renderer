from __future__ import annotations

from dataclasses import dataclass

from afr.linalg.mat4 import Mat4
from afr.linalg.vec2 import Vec2
from afr.linalg.vec3 import Vec3
from afr.models.model import Model
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


def shade_flat(scene: Scene, normal_ws: Vec3, pos_ws: Vec3) -> float:
    n = normal_ws.norm()
    s = float(scene.ambient)
    for light in scene.lights:
        ldir = (light.pos - pos_ws).norm()
        s += max(0.0, n.dot(ldir)) * float(light.intensity)
    # clamp 0..1-ish (let it go above 1.0 if you want "hot" lights later)
    return max(0.0, s)


def draw_model(
    surface,
    model: Model,
    model_mat: Mat4,
    view_mat: Mat4,
    proj_mat: Mat4,
    *,
    scene: Scene | None = None,
    texture=None,
    zbuf: list[float] | None = None,
) -> None:
    sw = surface.get_width()
    sh = surface.get_height()
    if zbuf is None:
        zbuf = [float("inf")] * (sw * sh)

    viewproj = proj_mat @ view_mat
    verts_ms = model.verts
    verts_ws = [model_mat @ v for v in verts_ms]
    verts_ndc = [viewproj @ v for v in verts_ws]
    verts_ss = [ndc_to_screen(v, sw, sh) for v in verts_ndc]

    use_tex = texture is not None and model.uvs and len(model.uvs) == len(model.faces)
    use_scene = scene is not None

    for fi, (i1, i2, i3) in enumerate(model.faces):
        p1s, p2s, p3s = verts_ss[i1], verts_ss[i2], verts_ss[i3]

        # Flat normal in world space for now.
        if use_scene:
            p1w, p2w, p3w = verts_ws[i1], verts_ws[i2], verts_ws[i3]
            n = (p2w - p1w).cross(p3w - p1w).norm()
            c = (p1w + p2w + p3w) * (1.0 / 3.0)
            shade = shade_flat(scene, n, c)
        else:
            shade = 1.0

        if use_tex:
            uv1, uv2, uv3 = model.uvs[fi]
            triangle_textured_z(
                surface, p1s, p2s, p3s, uv1, uv2, uv3, texture, zbuf, shade=shade
            )
        else:
            # grayscale from shade for now if no texture
            g = max(0, min(255, int(255 * min(shade, 1.0))))
            triangle_filled_z(surface, p1s, p2s, p3s, (g, g, g, 255), zbuf)
