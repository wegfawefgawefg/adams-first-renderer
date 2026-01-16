import pygame
import glm

from gra.settings import RES, WINDOW_RES
from gra.primitives import *
from gra.state import cframe, POINTS, POINTS_PER_FRAME, DELAY
from gra.colors import *

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


def old_draw(surface):
    angle = pygame.time.get_ticks() / 1000

    rect_size = Vec2(16, 16)
    center = RES / 2
    rect_pos = center - rect_size / 2 + Vec2(32, 32)

    for i in range(3):
        rot = glm.rotate(glm.vec2(0.0, 1.0), angle + i * 90)
        rect_pos_rotated = rot @ (rect_pos - center) + center
        pygame.draw.rect(
            surface, (255, 0, 0), (rect_pos_rotated.to_tuple(), rect_size.to_tuple())
        )

    pygame.draw.circle(surface, (0, 255, 0), mouse_pos(), 10)


def draw_mouse_coords(surface):
    # draw the mouse coords in the top left
    mouse_coords = mouse_pos()
    font = pygame.font.Font(None, 24)
    text = font.render(
        f"{mouse_coords.x:.2f}, {mouse_coords.y:.2f}", True, (255, 255, 255)
    )
    surface.blit(text, (10, 10))


def draw_some_points(surface):
    global cframe
    cframe += 1
    if cframe % DELAY == 0:
        if POINTS:
            for _ in range(0, POINTS_PER_FRAME):
                p, c = POINTS.pop(0)
                # pygame.draw.rect(surface, c, (p.x, p.y, 1, 1))
                surface.set_at((int(p.x), int(p.y)), c)


def draw(surface):
    # draw_mouse_coords(surface)
    # pygame.draw.circle(surface, (0, 255, 0), mouse_pos(), 10)

    draw_some_points(surface)

    a = Vec2(0, 0)
    line_shader(surface, a, mouse_pos(), 2, WHITE)


def draw_once(surface):
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
