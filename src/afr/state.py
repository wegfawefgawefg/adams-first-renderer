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
    scene: object | None = None  # afr.scene.SceneData
    ortho_half_height: float = 150.0

    # Fly camera (world space).
    cam_pos: object | None = None
    cam_yaw: float = math.pi  # yaw=pi looks toward -Z with our convention
    cam_pitch: float = 0.0
    cam_roll: float = 0.0
    mouse_look: bool = True


from pathlib import Path
from afr.linalg.vec3 import Vec3
from afr.linalg.mat4 import Mat4
from afr.models.obj import load_obj
from afr.models.gltf import load_gltf_scene


def load(app_state: AppState) -> None:
    if app_state.scene is None:
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

        # Make the castle about 200 Marios wide.
        castle_mn, castle_mx = scene_bounds(castle)
        castle_w = max(1e-6, castle_mx.x - castle_mn.x)
        castle_scale = (200.0 * 1.0) / castle_w

        # Apply scaling.
        castle_xform = Mat4.scale(castle_scale)
        for prim in castle.primitives:
            prim.local_to_world = castle_xform @ prim.local_to_world

        mario_scale_mat = Mat4.scale(mario_scale)
        for prim in mario.primitives:
            prim.local_to_world = mario_scale_mat @ prim.local_to_world

        # Recompute scaled castle bounds for placement.
        castle_mn, castle_mx = scene_bounds(castle)
        castle_center = (castle_mn + castle_mx) * 0.5

        # Place Mario in front of and on top of the castle.
        mario_mn, mario_mx = scene_bounds(mario)
        mario_h = mario_mx.y - mario_mn.y
        mario_center = (mario_mn + mario_mx) * 0.5

        desired_pos = Vec3(castle_center.x, castle_mx.y + mario_h * 0.5, castle_mx.z + 10.0)
        mario_xform = Mat4.translate(
            desired_pos.x - mario_center.x,
            desired_pos.y - mario_center.y,
            desired_pos.z - mario_center.z,
        )
        for prim in mario.primitives:
            prim.local_to_world = mario_xform @ prim.local_to_world

        # Merge into one scene.
        castle.primitives.extend(mario.primitives)
        app_state.scene = castle

        # Default camera: above and in front, looking at the castle center.
        cam_target = castle_center
        cam_pos = castle_center + Vec3(0.0, 120.0, 160.0)
        app_state.cam_pos = cam_pos
        d = (cam_target - cam_pos).norm()
        # Our forward convention: forward = (cp*sy, sp, cp*cy)
        app_state.cam_yaw = math.atan2(d.x, d.z)
        app_state.cam_pitch = math.asin(d.y)
        app_state.cam_roll = 0.0

        # Ortho zoom to fit the scaled castle reasonably.
        app_state.ortho_half_height = max(50.0, (castle_mx.y - castle_mn.y) * 0.75)

    if app_state.cam_pos is None:
        app_state.cam_pos = Vec3(0.0, 5.0, 20.0)
