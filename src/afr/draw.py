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


def draw_some_points(surface, dt: float):
    # Drain queued pixels at a fixed rate (pixels per second). This is only
    # meaningful when deferred plotting is enabled.
    if not state.POINTS:
        return

    # Convert pixels/sec into pixels this frame (with fractional carry).
    state.BLIT_ACCUM += float(state.BLIT_PPS) * float(dt)
    n = int(state.BLIT_ACCUM)
    if n <= 0:
        return
    state.BLIT_ACCUM -= n

    w = surface.get_width()
    h = surface.get_height()
    for _ in range(min(n, len(state.POINTS))):
        if not state.POINTS:
            break
        p, c = state.POINTS.popleft()
        x = int(p.x)
        y = int(p.y)
        if 0 <= x < w and 0 <= y < h:
            surface.set_at((x, y), c)


def draw(surface):
    # Immediate mode: clear and redraw every frame.
    a = Vec2(0, 0)
    line_shader(surface, a, mouse_pos(), 2, WHITE)

    # draw a point in the middle
    center = RES / 2
    # point(surface, center)

    # line demo
    # a = center / 2
    # b = center + a
    # line(surface, a, b)

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
