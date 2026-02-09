import pygame
import glm

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
    # Immediate mode: clear and redraw every frame.
    # a = Vec2(0, 0)
    # line_shader(surface, a, mouse_pos(), 2, WHITE)

    # draw a point in the middle
    center = RES / 2
    # point(surface, center)

    # line demo
    a = center / 2
    b = center + a
    # line(surface, a, b)
    # line to mouse pos from tl
    line(surface, Vec2(0, 0), mouse_pos())

    # rect demo
    # rect(surface, center, 20)

    # triangle demo
    # a = center / 2
    # b = center + Vec2(20, -20)
    # c = center + Vec2(0, 20)
    # triangle(surface, a, b, c)

    # lines demo
    # polygon_points = [
    #     center + Vec2(0, -30),
    #     center + Vec2(25, -10),
    #     center + Vec2(15, 20),
    #     center + Vec2(-15, 20),
    #     center + Vec2(-25, -10),
    # ]
    # lines(surface, polygon_points)

    # regular polygon demo
    # center = RES / 2
    # for i in range(3, 10):
    #     regular_polygon(surface, center, 50, i)

    # circle demo
    # r = 10
    # center = RES / 2
    # circle(surface, center, r)

    # circle raster demo
    # circle_raster_lines(surface, center, r * 6, WHITE, 1)

    # circle shader demo
    # r = 40
    # circle_shader(surface, center, r, WHITE)

    # a = center / 2
    # b = center + a
    # line_shader(surface, a, b, 0.1, WHITE)
