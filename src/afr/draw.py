import pygame
from afr.linalg.mat4 import Mat4
from afr.linalg.vec2 import Vec2
from afr.linalg.vec3 import Vec3
from afr.settings import RES, WINDOW_RES
from afr.rendering import Camera, PointLight, Scene, draw_primitive, ortho_for_surface

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
    # Camera from AppState (world space).
    import math
    t = pygame.time.get_ticks() / 1000.0

    cy = math.cos(app_state.cam_yaw)
    sy = math.sin(app_state.cam_yaw)
    cp = math.cos(app_state.cam_pitch)
    sp = math.sin(app_state.cam_pitch)
    forward = Vec3(cp * sy, sp, cp * cy).norm()
    world_up = Vec3(0.0, 1.0, 0.0)
    right = forward.cross(world_up).norm()
    up = right.cross(forward).norm()
    if app_state.cam_roll != 0.0:
        right = right.rotate(forward, app_state.cam_roll)
        up = up.rotate(forward, app_state.cam_roll)

    cam = Camera(
        pos=app_state.cam_pos,
        target=app_state.cam_pos + forward,
        up=up,
    )
    view = cam.view()

    # Ortho projection sized for the surface.
    proj = ortho_for_surface(
        surface.get_width(),
        surface.get_height(),
        half_height=float(getattr(app_state, "ortho_half_height", 12.0)),
        # These are view-space distances; our view matrix puts points in front at negative Z.
        near=0.1,
        far=5000.0,
    )

    # A few colored point lights rotating around the model (world space).
    # Scale the orbit with zoom so lighting doesn't become microscopic once the
    # world gets "big" (castle + mario).
    hh = float(getattr(app_state, "ortho_half_height", 12.0))
    r = max(35.0, hh * 0.35)
    y = max(20.0, hh * 0.20)
    lights = [
        PointLight(
            pos=Vec3(math.cos(t * 0.8) * r, y, math.sin(t * 0.8) * r),
            color=Vec3(1.0, 0.2, 0.2),
            intensity=0.9,
        ),
        PointLight(
            pos=Vec3(math.cos(t * 0.8 + 2.1) * r, y, math.sin(t * 0.8 + 2.1) * r),
            color=Vec3(0.2, 1.0, 0.2),
            intensity=0.9,
        ),
        PointLight(
            pos=Vec3(math.cos(t * 0.8 + 4.2) * r, y, math.sin(t * 0.8 + 4.2) * r),
            color=Vec3(0.2, 0.4, 1.0),
            intensity=0.9,
        ),
        # Small white fill at the camera to keep the front readable.
        PointLight(pos=cam.pos, color=Vec3.splat(1.0), intensity=0.25),
    ]
    scene = Scene(lights=lights, ambient=0.10)

    # Z-buffer per frame (CPU), shared across all cubes.
    zbuf = [float("inf")] * (surface.get_width() * surface.get_height())

    root_world = Mat4.scale(1.0)
    if app_state.scene is not None:
        for prim in app_state.scene.primitives:
            draw_primitive(surface, prim, root_world, view, proj, scene=scene, zbuf=zbuf)
