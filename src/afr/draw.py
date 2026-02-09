import pygame
import glm


from afr.linalg.vec2 import Vec2
from afr.linalg.vec3 import Vec3
from afr.settings import RES, WINDOW_RES
from afr.primitives import *
from afr.colors import *

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


def draw(surface, app_state):
    # draw a point in the middle
    center = RES / 2
    # point(surface, center)

    cube_verts = [v.clone() for v in app_state.cube_model.verts]
    cube_faces_tris = app_state.cube_model.faces
    cube_faces_uvs = app_state.cube_model.uvs

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
            app_state.kirby_tex,
            zbuf,
            shade=brightness,
        )
