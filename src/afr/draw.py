import pygame
import glm

from afr.linalg.vec3 import Vec3
from afr.settings import RES, WINDOW_RES
from afr.primitives import *
from afr.colors import *
import afr.state as state

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

    # faces
    cube_faces_tris = [
        (0, 1, 2),
        (0, 2, 3),
        (1, 5, 6),
        (1, 6, 2),
        (5, 4, 7),
        (5, 7, 6),
        (4, 0, 3),
        (4, 3, 7),
        (3, 2, 6),
        (3, 6, 7),
        (4, 5, 1),
        (4, 1, 0),
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

        # draw point
        # cpoint(surface, Vec2(p.x, p.y), RED)

    # draw triangles as lines
    # for v1, v2, v3 in cube_faces_tris:
    #     p1 = cube_verts[v1]
    #     p2 = cube_verts[v2]
    #     p3 = cube_verts[v3]
    #     line(surface, Vec2(p1.x, p1.y), Vec2(p2.x, p2.y), GREEN)
    #     line(surface, Vec2(p2.x, p2.y), Vec2(p3.x, p3.y), GREEN)
    #     line(surface, Vec2(p3.x, p3.y), Vec2(p1.x, p1.y), GREEN)

    light_pos = Vec3(0.0, 0.0, 5.0)
    light_color = Vec3(0.0, 0.0, 255)
    # light color varies over time
    # light_color = Vec3(
    #     (math.sin(pygame.time.get_ticks() / 1000.0) + 1) / 2,
    #     (math.sin(pygame.time.get_ticks() / 1000.0 + 2) + 1) / 2,
    #     (math.sin(pygame.time.get_ticks() / 1000.0 + 4) + 1) / 2,
    # )

    l = light_pos

    # sort faces by center z
    def face_z(face):
        v1, v2, v3 = face
        p1 = cube_verts[v1]
        p2 = cube_verts[v2]
        p3 = cube_verts[v3]
        return (p1.z + p2.z + p3.z) / 3.0

    cube_faces_tris.sort(key=face_z, reverse=True)

    # do with filled triangle
    for v1, v2, v3 in cube_faces_tris:
        p1 = cube_verts[v1]
        p2 = cube_verts[v2]
        p3 = cube_verts[v3]

        u = (p2 - p1).norm()
        v = (p3 - p1).norm()
        face_normal = u.cross(v).norm()
        face_center = (p1 + p2 + p3) * (1.0 / 3.0)
        face_to_light = (l - face_center).norm()
        brightness = max(0.1, face_normal.dot(face_to_light))
        c = brightness * light_color

        triangle_filled(
            surface,
            Vec2(p1.x, p1.y),
            Vec2(p2.x, p2.y),
            Vec2(p3.x, p3.y),
            c.to_tuple(),
        )
