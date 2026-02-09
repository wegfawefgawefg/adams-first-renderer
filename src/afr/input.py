import math

import pygame

from afr.linalg.vec3 import Vec3


def init_input(app_state) -> None:
    if getattr(app_state, "mouse_look", False):
        pygame.event.set_grab(True)
        pygame.mouse.set_visible(False)


def do_inputs(app_state, dt: float) -> bool:
    """Process inputs/events and update camera in app_state.

    Returns True to keep running, False to quit.
    """
    mouse_dx = 0
    mouse_dy = 0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return False

            if event.key == pygame.K_m:
                app_state.mouse_look = not app_state.mouse_look
                pygame.event.set_grab(app_state.mouse_look)
                pygame.mouse.set_visible(not app_state.mouse_look)

        if event.type == pygame.MOUSEMOTION and app_state.mouse_look:
            rel = event.rel
            mouse_dx += rel[0]
            mouse_dy += rel[1]

    # Yaw/pitch from mouse, roll from Q/E.
    if app_state.mouse_look:
        sens = 0.0025
        # Positive mouse_dx should look right.
        app_state.cam_yaw -= mouse_dx * sens
        app_state.cam_pitch += -mouse_dy * sens
        # Clamp pitch to avoid flipping.
        app_state.cam_pitch = max(-1.55, min(1.55, app_state.cam_pitch))

    keys = pygame.key.get_pressed()
    roll_speed = 1.5  # rad/sec
    if keys[pygame.K_q]:
        app_state.cam_roll -= roll_speed * dt
    if keys[pygame.K_e]:
        app_state.cam_roll += roll_speed * dt

    # Forward vector (yaw/pitch). Convention:
    # yaw=0 points +Z, yaw=pi points -Z.
    cy = math.cos(app_state.cam_yaw)
    sy = math.sin(app_state.cam_yaw)
    cp = math.cos(app_state.cam_pitch)
    sp = math.sin(app_state.cam_pitch)
    forward = Vec3(cp * sy, sp, cp * cy).norm()
    world_up = Vec3(0.0, 1.0, 0.0)
    right = forward.cross(world_up).norm()
    up = right.cross(forward).norm()

    # Apply roll around forward axis.
    if app_state.cam_roll != 0.0:
        right = right.rotate(forward, app_state.cam_roll)
        up = up.rotate(forward, app_state.cam_roll)

    # Movement: orthographic "pan" (W/S on world Y, A/D on camera right).
    # Use Space/Shift for depth along camera forward/back.
    move = Vec3(0.0, 0.0, 0.0)
    if keys[pygame.K_w]:
        move = move + world_up
    if keys[pygame.K_s]:
        move = move - world_up
    if keys[pygame.K_d]:
        move = move + right
    if keys[pygame.K_a]:
        move = move - right
    if keys[pygame.K_SPACE]:
        move = move + forward
    if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
        move = move - forward

    if move.mag() > 0:
        move = move.norm()
        speed = 3.0
        if keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]:
            speed *= 3.0
        app_state.cam_pos = app_state.cam_pos + move * (speed * dt)

    return True
