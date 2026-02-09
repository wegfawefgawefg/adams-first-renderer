from __future__ import annotations

from dataclasses import dataclass
from collections import deque

import pygame
import math

DEFERRED_PLOTTING = False

# Deferred plotting drain rate (pixels per second).
BLIT_PPS = 20_000

# Fractional pixel accumulator for time-based draining.
BLIT_ACCUM = 0.0

# Queue entries are (Vec2, color).
POINTS = deque()

# When starting a new deferred "frame", we clear right before draining the first
# pixels. This avoids a blank frame (flicker) where we clear but haven't blitted
# any pixels yet.
NEEDS_CLEAR = False
CLEAR_COLOR = (0, 0, 0, 255)


def plot_deferred(surface, pos, c) -> None:
    # Enqueue pixels so the main loop can blit them out gradually.
    POINTS.append((pos, c))


def plot_immediate(surface, pos, c) -> None:
    # Plot directly for max speed.
    x = int(pos.x)
    y = int(pos.y)
    if 0 <= x < surface.get_width() and 0 <= y < surface.get_height():
        surface.set_at((x, y), c)


# Primitive plotting entrypoint. Configured by main().
PLOT = plot_immediate


@dataclass
class AppState:
    # Cached resources for draw().
    cube_model: object | None = None
    kirby_tex: object | None = None

    # Fly camera (world space).
    cam_pos: object | None = None
    cam_yaw: float = math.pi  # yaw=pi looks toward -Z with our convention
    cam_pitch: float = 0.0
    cam_roll: float = 0.0
    mouse_look: bool = True


from pathlib import Path
from afr.models import Model
from afr.linalg.vec3 import Vec3


def load(app_state: AppState) -> None:
    model_path = (
        Path(__file__).resolve().parents[2] / "assets" / "models" / "cube.afrmodel"
    )
    app_state.cube_model = Model.load(model_path)

    tex_path = (
        Path(__file__).resolve().parents[2] / "assets" / "textures" / "kirby.png"
    )
    tex = pygame.image.load(str(tex_path))
    # convert_alpha requires a video mode; keep it optional so this loader can
    # be used in headless tests/tools.
    if pygame.display.get_surface() is not None:
        tex = tex.convert_alpha()
    app_state.kirby_tex = tex

    if app_state.cam_pos is None:
        app_state.cam_pos = Vec3(0.0, 0.0, 5.0)
