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
    scene_prims: list | None = None  # list of (Model, pygame.Surface|None, Mat4)

    # Fly camera (world space).
    cam_pos: object | None = None
    cam_yaw: float = math.pi  # yaw=pi looks toward -Z with our convention
    cam_pitch: float = 0.0
    cam_roll: float = 0.0
    mouse_look: bool = True


from pathlib import Path
from afr.linalg.vec3 import Vec3
from afr.models.gltf import load_gltf_scene


def load(app_state: AppState) -> None:
    if app_state.scene_prims is None:
        gltf_path = (
            Path(__file__).resolve().parents[2]
            / "assets"
            / "models"
            / "mario-64-mario"
            / "source"
            / "prototype_mario_super_mario_64"
            / "scene.gltf"
        )
        app_state.scene_prims = load_gltf_scene(gltf_path)

    if app_state.cam_pos is None:
        app_state.cam_pos = Vec3(0.0, 1.5, 8.0)
