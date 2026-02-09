import math

import pygame

from afr.linalg.vec3 import Vec3


def init_input(app_state) -> None:
    if getattr(app_state, "mouse_look", False):
        pygame.event.set_grab(True)
        pygame.mouse.set_visible(False)


def do_inputs(app_state, dt: float) -> bool:
    """Process inputs/events and update mario + camera angles in app_state.

    Returns True to keep running, False to quit.
    """
    mouse_dx = 0
    mouse_dy = 0

    app_state.jump_pressed = False

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

            if event.key == pygame.K_SPACE:
                app_state.jump_pressed = True

        if event.type == pygame.MOUSEMOTION and app_state.mouse_look:
            rel = event.rel
            mouse_dx += rel[0]
            mouse_dy += rel[1]

    # Yaw/pitch from mouse (camera follows behind Mario).
    if app_state.mouse_look:
        sens = 0.0025
        # Positive mouse_dx should look right (increase yaw).
        app_state.mario_yaw += mouse_dx * sens
        # Mouse up should look up; pygame gives negative dy for up.
        app_state.cam_pitch += -mouse_dy * sens
        # Clamp pitch to avoid flipping.
        app_state.cam_pitch = max(-1.25, min(1.25, app_state.cam_pitch))

    keys = pygame.key.get_pressed()
    # Q/E intentionally unbound.

    # Flat forward/right for Mario movement (XZ plane).
    cy = math.cos(app_state.mario_yaw)
    sy = math.sin(app_state.mario_yaw)
    forward = Vec3(sy, 0.0, cy).norm()
    world_up = Vec3(0.0, 1.0, 0.0)
    right = forward.cross(world_up).norm()

    # Movement intent: Mario locomotion (W/S forward/back, A/D strafe).
    move = Vec3(0.0, 0.0, 0.0)
    if keys[pygame.K_w]:
        move = move + forward
    if keys[pygame.K_s]:
        move = move - forward
    if keys[pygame.K_d]:
        move = move + right
    if keys[pygame.K_a]:
        move = move - right

    app_state.move_dir = move
    app_state.sprint = bool(keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT])

    return True
