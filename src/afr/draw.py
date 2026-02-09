import pygame
from afr.linalg.mat4 import Mat4
from afr.linalg.vec2 import Vec2
from afr.linalg.vec3 import Vec3
from afr.settings import RES, WINDOW_RES
from afr.rendering import Camera, PointLight, Scene, draw_model, ortho_for_surface

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
    model = app_state.cube_model
    tex = app_state.kirby_tex

    t = pygame.time.get_ticks() / 1000.0
    angle = t * 0.5

    # World-space camera.
    cam = Camera(
        pos=Vec3(0.0, 0.0, 5.0),
        target=Vec3(0.0, 0.0, 0.0),
        up=Vec3(0.0, 1.0, 0.0),
    )
    view = cam.view()

    # Ortho projection sized for the surface.
    proj = ortho_for_surface(
        surface.get_width(), surface.get_height(), half_height=2.2, near=0.1, far=100.0
    )

    # Model transform in world space (scale + rotate).
    model_mat = (
        Mat4.rotate_x(angle)
        @ Mat4.rotate_y(angle * 0.5)
        @ Mat4.rotate_z(angle * 0.25)
        @ Mat4.scale(1.2)
    )

    scene = Scene(lights=[PointLight(pos=cam.pos, intensity=1.0)], ambient=0.15)

    # Z-buffer per frame (CPU).
    zbuf = [float("inf")] * (surface.get_width() * surface.get_height())

    draw_model(
        surface, model, model_mat, view, proj, scene=scene, texture=tex, zbuf=zbuf
    )
