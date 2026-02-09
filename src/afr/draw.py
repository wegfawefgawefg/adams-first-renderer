import pygame
from afr.linalg.mat4 import Mat4
from afr.linalg.vec2 import Vec2
from afr.linalg.vec3 import Vec3
from afr.settings import RES, WINDOW_RES
from afr.rendering import Camera, PointLight, Scene, draw_primitive

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
    import math

    world_up = Vec3(0.0, 1.0, 0.0)

    # Third-person camera: behind Mario, looking where he's facing.
    yaw = float(getattr(app_state, "mario_yaw", 0.0))
    pitch = float(getattr(app_state, "cam_pitch", 0.0))
    mario_pos = getattr(app_state, "mario_pos", Vec3(0.0, 1.0, 10.0))

    cy = math.cos(yaw)
    sy = math.sin(yaw)
    cp = math.cos(pitch)
    sp = math.sin(pitch)

    flat_forward = Vec3(sy, 0.0, cy).norm()
    cam_forward = Vec3(cp * sy, sp, cp * cy).norm()

    follow_dist = 6.0
    follow_height = 2.0
    cam_pos = mario_pos - flat_forward * follow_dist + Vec3(0.0, follow_height, 0.0)
    cam_target = mario_pos + Vec3(0.0, 1.0, 0.0) + cam_forward * 2.0

    cam = Camera(pos=cam_pos, target=cam_target, up=world_up)
    view = cam.view()

    # Perspective projection.
    w = surface.get_width()
    h = surface.get_height()
    aspect = (w / h) if h else 1.0
    proj = Mat4.perspective(math.radians(65.0), aspect, 0.1, 5000.0)

    # Simple "sun" light: high in the sky, bright, slightly warm.
    lights = [
        PointLight(
            pos=Vec3(200.0, 500.0, 150.0),
            color=Vec3(1.0, 0.98, 0.92),
            intensity=1.4,
        )
    ]
    scene = Scene(lights=lights, ambient=0.22)

    # Z-buffer per frame (CPU), shared across all cubes.
    zbuf = [float("inf")] * (surface.get_width() * surface.get_height())

    if getattr(app_state, "castle_scene", None) is not None:
        for prim in app_state.castle_scene.primitives:
            draw_primitive(surface, prim, Mat4.identity(), view, proj, scene=scene, zbuf=zbuf)

    if getattr(app_state, "mario_scene", None) is not None:
        mario_world = Mat4.translate(mario_pos.x, mario_pos.y, mario_pos.z) @ Mat4.rotate_y(yaw)
        for prim in app_state.mario_scene.primitives:
            draw_primitive(surface, prim, mario_world, view, proj, scene=scene, zbuf=zbuf)
