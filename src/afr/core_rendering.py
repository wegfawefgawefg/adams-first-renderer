import pygame
import glm

from afr.settings import RES, WINDOW_RES
from afr.primitives import *
from afr.colors import *
import afr.state as state


def draw_some_points(surface, dt: float, stats: bool = False) -> int:
    # Drain queued pixels at a fixed rate (pixels per second). This is only
    # meaningful when deferred plotting is enabled.
    if not state.POINTS:
        return 0

    if state.NEEDS_CLEAR:
        surface.fill(state.CLEAR_COLOR)
        state.NEEDS_CLEAR = False

    # Convert pixels/sec into pixels this frame (with fractional carry).
    state.BLIT_ACCUM += float(state.BLIT_PPS) * float(dt)
    n = int(state.BLIT_ACCUM)
    if n <= 0:
        return 0
    state.BLIT_ACCUM -= n

    w = surface.get_width()
    h = surface.get_height()
    drained = 0
    for _ in range(min(n, len(state.POINTS))):
        if not state.POINTS:
            break
        p, c = state.POINTS.popleft()
        x = int(p.x)
        y = int(p.y)
        if 0 <= x < w and 0 <= y < h:
            surface.set_at((x, y), c)
        if stats:
            drained += 1

    return drained
