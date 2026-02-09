import pygame
import glm

from pathlib import Path

from afr.linalg.vec2 import Vec2
from afr.linalg.vec3 import Vec3
from afr.settings import RES, WINDOW_RES
from afr.primitives import *
from afr.colors import *
import afr.state as state

_kirby_tex = None

""" we are inventing these from scratch for education 
## lines
    draw point
    draw line
    draw rect
    draw circle
    draw triangle?
    draw polygon

## filled
    draw rect
    draw circle
    draw triangle?
    draw polygon

## textures
    draw point
    draw line
    draw rect
    draw circle
    draw triangle?
    draw polygon

jump to 3d
"""


def mouse_pos():
    mp = pygame.mouse.get_pos()
    return Vec2(mp[0], mp[1]) / WINDOW_RES * RES


def draw_mouse_coords(surface):
    # draw the mouse coords in the top left
    mouse_coords = mouse_pos()
    font = pygame.font.Font(None, 24)
    text = font.render(
        f"{mouse_coords.x:.2f}, {mouse_coords.y:.2f}", True, (255, 255, 255)
    )
    surface.blit(text, (10, 10))


def draw(surface):
    # draw a point in the middle
    center = RES / 2
    # point(surface, center)

    # cube # centered at 0 # lengths of 1
    # 8 points pls
    cube_verts = [
        Vec3(-1, -1, -1),
        Vec3(1, -1, -1),
        Vec3(1, 1, -1),
        Vec3(-1, 1, -1),
        Vec3(-1, -1, 1),
        Vec3(1, -1, 1),
        Vec3(1, 1, 1),
        Vec3(-1, 1, 1),
    ]

    # faces (triangles), CCW winding when viewed from outside (outward normals).
    #
    # Each cube face is 2 triangles. We give each face a simple 0..1 UV square.
    uv_a = Vec2(0.0, 0.0)
    uv_b = Vec2(0.0, 1.0)
    uv_c = Vec2(1.0, 1.0)
    uv_d = Vec2(1.0, 0.0)

    cube_faces_tris = [
        # z = -1 (back)
        (0, 2, 1),
        (0, 3, 2),
        # x = +1 (right)
        (1, 6, 5),
        (1, 2, 6),
        # z = +1 (front)
        (5, 7, 4),
        (5, 6, 7),
        # x = -1 (left)
        (4, 3, 0),
        (4, 7, 3),
        # y = +1 (top)
        (3, 6, 2),
        (3, 7, 6),
        # y = -1 (bottom)
        (4, 1, 5),
        (4, 0, 1),
    ]
    cube_faces_uvs = [
        (uv_a, uv_c, uv_d),
        (uv_a, uv_b, uv_c),
        (uv_a, uv_c, uv_d),
        (uv_a, uv_b, uv_c),
        (uv_a, uv_c, uv_d),
        (uv_a, uv_b, uv_c),
        (uv_a, uv_c, uv_d),
        (uv_a, uv_b, uv_c),
        (uv_a, uv_c, uv_d),
        (uv_a, uv_b, uv_c),
        (uv_a, uv_c, uv_d),
        (uv_a, uv_b, uv_c),
    ]

    scale = Vec3.splat(20)
    center_3d = Vec3(center.x, center.y, 0)
    angle = pygame.time.get_ticks() / 1000.0 * 0.5  # rotate over time

    # transform points in place
    for i, p in enumerate(cube_verts):
        p = p * scale
        p = p.rotate_x(angle)
        p = p.rotate_y(angle * 0.5)
        p = p.rotate_z(angle * 0.25)
        p = p + center_3d
        cube_verts[i] = p

    # Approx camera is in front of the screen looking toward the origin.
    # Put the light at the camera so faces oriented toward us are bright.
    camera_pos = center_3d + Vec3(0.0, 0.0, -200.0)
    light_pos = camera_pos
    l = light_pos

    # Simple Z-buffer for correct visibility (prevents "missing triangles"
    # caused by painter sorting edge-cases).
    sw = surface.get_width()
    sh = surface.get_height()
    zbuf = [float("inf")] * (sw * sh)

    global _kirby_tex
    if _kirby_tex is None:
        # draw.py is at repo_root/src/afr/draw.py
        tex_path = Path(__file__).resolve().parents[2] / "assets" / "kirby.png"
        _kirby_tex = pygame.image.load(str(tex_path)).convert_alpha()

    for (i1, i2, i3), (t1, t2, t3) in zip(cube_faces_tris, cube_faces_uvs):
        p1, p2, p3 = cube_verts[i1], cube_verts[i2], cube_verts[i3]

        face_normal = (p2 - p1).cross(p3 - p1).norm()
        face_center = (p1 + p2 + p3) * (1.0 / 3.0)
        face_to_light = (l - face_center).norm()
        brightness = max(0.15, face_normal.dot(face_to_light))
        triangle_textured_z(
            surface,
            p1,
            p2,
            p3,
            t1,
            t2,
            t3,
            _kirby_tex,
            zbuf,
            shade=brightness,
        )
