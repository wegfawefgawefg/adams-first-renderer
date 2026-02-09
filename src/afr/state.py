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
    castle_scene: object | None = None  # afr.scene.SceneData
    mario_scene: object | None = None  # afr.scene.SceneData

    # Mario/player transform in world space.
    mario_pos: object | None = None  # Vec3
    mario_yaw: float = math.pi  # yaw=pi looks toward -Z with our convention

    # Camera angles (third person).
    cam_pitch: float = -0.25
    mouse_look: bool = True


from pathlib import Path
from afr.linalg.vec3 import Vec3
from afr.linalg.mat4 import Mat4
from afr.models.obj import load_obj
from afr.models.gltf import load_gltf_scene


def load(app_state: AppState) -> None:
    if app_state.castle_scene is None or app_state.mario_scene is None:
        root = Path(__file__).resolve().parents[2] / "assets" / "models"

        castle = load_obj(root / "peaches_castle.obj")
        mario = load_gltf_scene(
            root
            / "mario-64-mario"
            / "source"
            / "prototype_mario_super_mario_64"
            / "scene.gltf"
        )

        def scene_bounds(scene):
            mn = Vec3(1e9, 1e9, 1e9)
            mx = Vec3(-1e9, -1e9, -1e9)
            for prim in scene.primitives:
                for v in prim.mesh.positions:
                    wv = prim.local_to_world @ v
                    mn = Vec3(min(mn.x, wv.x), min(mn.y, wv.y), min(mn.z, wv.z))
                    mx = Vec3(max(mx.x, wv.x), max(mx.y, wv.y), max(mx.z, wv.z))
            return mn, mx

        # Use Mario height ~= 1 world unit ("1 meter") as the baseline.
        mario_mn, mario_mx = scene_bounds(mario)
        mario_h = max(1e-6, mario_mx.y - mario_mn.y)
        mario_scale = 1.0 / mario_h

        # Make the castle about 100 Marios wide.
        # (Previously 200; that ended up feeling about 2x too big.)
        castle_mn, castle_mx = scene_bounds(castle)
        castle_w = max(1e-6, castle_mx.x - castle_mn.x)
        castle_scale = (100.0 * 1.0) / castle_w

        # Apply scaling.
        castle_xform = Mat4.scale(castle_scale)
        for prim in castle.primitives:
            prim.local_to_world = castle_xform @ prim.local_to_world

        mario_scale_mat = Mat4.scale(mario_scale)
        for prim in mario.primitives:
            prim.local_to_world = mario_scale_mat @ prim.local_to_world

        # Center the castle around the origin (XZ) and put its base on y=0.
        castle_mn, castle_mx = scene_bounds(castle)
        castle_center = (castle_mn + castle_mx) * 0.5
        castle_recenter = Mat4.translate(
            -castle_center.x,
            -castle_mn.y,
            -castle_center.z,
        )
        for prim in castle.primitives:
            prim.local_to_world = castle_recenter @ prim.local_to_world
        castle_mn, castle_mx = scene_bounds(castle)

        # Re-center Mario around a useful pivot: bottom-center of his bounds.
        mario_mn, mario_mx = scene_bounds(mario)
        mario_pivot = Vec3((mario_mn.x + mario_mx.x) * 0.5, mario_mn.y, (mario_mn.z + mario_mx.z) * 0.5)
        mario_recenter = Mat4.translate(-mario_pivot.x, -mario_pivot.y, -mario_pivot.z)
        for prim in mario.primitives:
            prim.local_to_world = mario_recenter @ prim.local_to_world
        mario_mn, mario_mx = scene_bounds(mario)

        # Place Mario: on top of the castle, near the "front" edge (+Z),
        # facing toward the castle (-Z).
        desired_pos = Vec3(0.0, castle_mx.y + 0.01, castle_mx.z + 5.0)
        app_state.mario_pos = desired_pos
        app_state.mario_yaw = math.pi
        app_state.cam_pitch = -0.25

        app_state.castle_scene = castle
        app_state.mario_scene = mario

    if app_state.mario_pos is None:
        app_state.mario_pos = Vec3(0.0, 1.0, 10.0)
