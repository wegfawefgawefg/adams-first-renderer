from __future__ import annotations

from dataclasses import dataclass

from afr.linalg.mat4 import Mat4
from afr.linalg.vec2 import Vec2
from afr.linalg.vec3 import Vec3
from afr.linalg.vec4 import Vec4
from afr.scene import Mesh, Material, Primitive
from afr.primitives import triangle_filled_z, triangle_textured_z

BACKFACE_CULL = True


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


@dataclass
class _ClipVert:
    clip: Vec4
    uv: Vec2 | None = None


def _clip_poly_against_plane(poly: list[_ClipVert], dist_fn) -> list[_ClipVert]:
    """Sutherland–Hodgman clipper for a convex polygon against one clip plane.

    `dist_fn(v.clip)` should return >= 0 for inside.
    """
    if not poly:
        return []

    out: list[_ClipVert] = []
    prev = poly[-1]
    prev_d = float(dist_fn(prev.clip))
    prev_in = prev_d >= 0.0

    for cur in poly:
        cur_d = float(dist_fn(cur.clip))
        cur_in = cur_d >= 0.0

        if prev_in and cur_in:
            # In -> In: keep current.
            out.append(cur)
        elif prev_in and not cur_in:
            # In -> Out: add intersection.
            denom = (prev_d - cur_d)
            if denom != 0.0:
                t = prev_d / denom
                iclip = prev.clip + (cur.clip - prev.clip) * t
                if prev.uv is not None and cur.uv is not None:
                    iuv = prev.uv + (cur.uv - prev.uv) * t
                else:
                    iuv = None
                out.append(_ClipVert(iclip, iuv))
        elif (not prev_in) and cur_in:
            # Out -> In: add intersection then current.
            denom = (prev_d - cur_d)
            if denom != 0.0:
                t = prev_d / denom
                iclip = prev.clip + (cur.clip - prev.clip) * t
                if prev.uv is not None and cur.uv is not None:
                    iuv = prev.uv + (cur.uv - prev.uv) * t
                else:
                    iuv = None
                out.append(_ClipVert(iclip, iuv))
            out.append(cur)
        else:
            # Out -> Out: nothing.
            pass

        prev = cur
        prev_d = cur_d
        prev_in = cur_in

    return out


def _clip_triangle(poly: list[_ClipVert]) -> list[_ClipVert]:
    """Clip a triangle (as a 3-vertex polygon) against the full clip volume."""
    # OpenGL-style clip volume:
    #   -w <= x <= w
    #   -w <= y <= w
    #   -w <= z <= w
    planes = [
        lambda c: c.x + c.w,  # left
        lambda c: -c.x + c.w,  # right
        lambda c: c.y + c.w,  # bottom
        lambda c: -c.y + c.w,  # top
        lambda c: c.z + c.w,  # near
        lambda c: -c.z + c.w,  # far
    ]

    out = poly
    for p in planes:
        out = _clip_poly_against_plane(out, p)
        if len(out) < 3:
            return []
    return out


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
    cull_backfaces: bool = True,
    front_face_ccw: bool = True,
) -> None:
    sw = surface.get_width()
    sh = surface.get_height()
    if zbuf is None:
        zbuf = [float("inf")] * (sw * sh)

    viewproj = proj_mat @ view_mat
    verts_ms = mesh.positions
    verts_ws = [model_mat @ v for v in verts_ms]

    # Clip-space coordinates (no perspective divide yet).
    verts_clip = [viewproj @ Vec4(v.x, v.y, v.z, 1.0) for v in verts_ws]

    tex_surface = material.base_color_tex.surface if material.base_color_tex else None
    use_tex = tex_surface is not None and mesh.uvs is not None
    use_scene = scene is not None

    for (i1, i2, i3) in mesh.indices:
        if use_tex:
            uv1, uv2, uv3 = mesh.uvs[i1], mesh.uvs[i2], mesh.uvs[i3]
        else:
            uv1 = uv2 = uv3 = None

        poly = _clip_triangle(
            [
                _ClipVert(verts_clip[i1], uv1),
                _ClipVert(verts_clip[i2], uv2),
                _ClipVert(verts_clip[i3], uv3),
            ]
        )
        if len(poly) < 3:
            continue

        # Flat normal in world space for now.
        if use_scene:
            p1w, p2w, p3w = verts_ws[i1], verts_ws[i2], verts_ws[i3]
            n = (p2w - p1w).cross(p3w - p1w).norm()
            c = (p1w + p2w + p3w) * (1.0 / 3.0)
            shade = shade_flat(scene, n, c)
        else:
            shade = Vec3.splat(1.0)

        # Triangulate the clipped polygon (fan).
        v0 = poly[0]
        for k in range(1, len(poly) - 1):
            va = v0
            vb = poly[k]
            vc = poly[k + 1]

            # Perspective divide for each vertex -> NDC.
            if va.clip.w == 0.0 or vb.clip.w == 0.0 or vc.clip.w == 0.0:
                continue

            a_ndc = va.clip.to_vec3(perspective_divide=True)
            b_ndc = vb.clip.to_vec3(perspective_divide=True)
            c_ndc = vc.clip.to_vec3(perspective_divide=True)

            # Backface culling in NDC (before the Y-flip in ndc_to_screen).
            # Convention: CCW triangles are front-facing unless overridden.
            if BACKFACE_CULL and cull_backfaces:
                area = (b_ndc.x - a_ndc.x) * (c_ndc.y - a_ndc.y) - (b_ndc.y - a_ndc.y) * (
                    c_ndc.x - a_ndc.x
                )
                if front_face_ccw:
                    if area <= 0.0:
                        continue
                else:
                    if area >= 0.0:
                        continue

            p1s = ndc_to_screen(a_ndc, sw, sh)
            p2s = ndc_to_screen(b_ndc, sw, sh)
            p3s = ndc_to_screen(c_ndc, sw, sh)

            if use_tex:
                if va.uv is None or vb.uv is None or vc.uv is None:
                    continue
                tri_shade = shade * material.base_color
                triangle_textured_z(
                    surface,
                    p1s,
                    p2s,
                    p3s,
                    va.uv,
                    vb.uv,
                    vc.uv,
                    tex_surface,
                    zbuf,
                    shade=tri_shade,
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
        cull_backfaces=getattr(prim, "cull_backfaces", True),
        front_face_ccw=getattr(prim, "front_face_ccw", True),
    )
