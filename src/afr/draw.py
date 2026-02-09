import pygame
from afr.linalg.mat4 import Mat4
from afr.linalg.vec2 import Vec2
from afr.linalg.vec3 import Vec3
from afr.settings import RES, WINDOW_RES
from afr.rendering import Camera, PointLight, Scene, draw_primitive

from afr.primitives import *
from afr.colors import *

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


def draw(surface, app_state):
    import math

    world_up = Vec3(0.0, 1.0, 0.0)
    t = pygame.time.get_ticks() / 1000.0

    # Third-person camera: behind Mario, looking where he's facing.
    yaw = float(getattr(app_state, "mario_yaw", 0.0))
    pitch = float(getattr(app_state, "cam_pitch", 0.0))
    mario_pos = getattr(app_state, "mario_pos", Vec3(0.0, 1.0, 10.0))

    cy = math.cos(yaw)
    sy = math.sin(yaw)
    cp = math.cos(pitch)
    sp = math.sin(pitch)

    flat_forward = Vec3(sy, 0.0, cy).norm()
    cam_forward = Vec3(cp * sy, sp, cp * cy).norm()

    follow_dist = 6.0
    follow_height = 2.0
    cam_pos = mario_pos - flat_forward * follow_dist + Vec3(0.0, follow_height, 0.0)
    cam_target = mario_pos + Vec3(0.0, 1.0, 0.0) + cam_forward * 2.0

    cam = Camera(pos=cam_pos, target=cam_target, up=world_up)
    view = cam.view()

    # Perspective projection.
    w = surface.get_width()
    h = surface.get_height()
    aspect = (w / h) if h else 1.0
    proj = Mat4.perspective(math.radians(65.0), aspect, 0.1, 5000.0)

    # Simple "sun" light: high in the sky, bright, slightly warm.
    lights = [
        PointLight(
            pos=Vec3(200.0, 500.0, 150.0),
            color=Vec3(1.0, 0.98, 0.92),
            intensity=1.4,
        )
    ]
    scene = Scene(lights=lights, ambient=0.22)

    # Z-buffer per frame (CPU), shared across all cubes.
    zbuf = [float("inf")] * (surface.get_width() * surface.get_height())

    if getattr(app_state, "castle_scene", None) is not None:
        for prim in app_state.castle_scene.primitives:
            draw_primitive(
                surface, prim, Mat4.identity(), view, proj, scene=scene, zbuf=zbuf
            )

    if getattr(app_state, "mario_scene", None) is not None:
        mario_world = Mat4.translate(
            mario_pos.x, mario_pos.y, mario_pos.z
        ) @ Mat4.rotate_y(yaw)
        for prim in app_state.mario_scene.primitives:
            draw_primitive(
                surface, prim, mario_world, view, proj, scene=scene, zbuf=zbuf
            )

    # HUD/status Mario: draw a big Mario on the left side of the screen.
    if getattr(app_state, "mario_scene", None) is not None:
        hud_w = max(64, surface.get_width() // 3)
        hud_h = max(64, surface.get_height() // 2)
        hud = pygame.Surface((hud_w, hud_h), flags=pygame.SRCALPHA, depth=32)
        hud.fill((0, 0, 0, 0))

        # Slight backdrop so he reads on dark backgrounds.
        pygame.draw.rect(hud, (0, 0, 0, 120), hud.get_rect(), border_radius=10)

        # HUD camera in its own little world near origin.
        hud_aspect = (hud_w / hud_h) if hud_h else 1.0
        hud_proj = Mat4.perspective(math.radians(35.0), hud_aspect, 0.1, 100.0)
        hud_cam = Camera(
            pos=Vec3(0.0, 1.25, 3.2),
            target=Vec3(0.0, 0.95, 0.0),
            up=world_up,
        )
        hud_view = hud_cam.view()
        hud_z = [float("inf")] * (hud_w * hud_h)

        # Make him big, face the camera, and shift down so the face stays in-frame.
        hud_scale = 2.6
        # Spin for a goofy "status" animation.
        hud_face_yaw = t * 0.1
        hud_y_offset = -0.55
        hud_world = (
            Mat4.translate(0.0, hud_y_offset, 0.0)
            @ Mat4.rotate_y(hud_face_yaw)
            @ Mat4.scale(hud_scale)
        )

        # HUD-only vertex wiggle (keep world Mario stable).
        from afr.scene import Mesh, Primitive

        wiggle_amp = 0.10  # model-space units (scaled by hud_scale)
        wiggle_freq = 2.0  # Hz-ish
        wiggle_spatial = 6.0  # phase variation across the mesh
        wiggle_phase = t * (2.0 * math.pi * wiggle_freq)

        for prim in app_state.mario_scene.primitives:
            base = prim.mesh.positions
            if not base:
                continue

            # Cheap "inflate" direction: outward from mesh center (bounds center).
            minx = min(v.x for v in base)
            maxx = max(v.x for v in base)
            miny = min(v.y for v in base)
            maxy = max(v.y for v in base)
            minz = min(v.z for v in base)
            maxz = max(v.z for v in base)
            center = Vec3((minx + maxx) * 0.5, (miny + maxy) * 0.5, (minz + maxz) * 0.5)

            wiggled = []
            for v in base:
                # Phase is based on vertex position so different parts move differently.
                ph = wiggle_phase + (v.x * 0.7 + v.y * 1.1 + v.z * 0.5) * wiggle_spatial
                s = math.sin(ph) * wiggle_amp
                d = v - center
                if d.mag() > 1e-9:
                    d = d.norm()
                else:
                    d = Vec3(0.0, 1.0, 0.0)
                wiggled.append(v + d * s)

            wmesh = Mesh(
                positions=wiggled, uvs=prim.mesh.uvs, indices=prim.mesh.indices
            )
            wprim = Primitive(
                mesh=wmesh,
                material=prim.material,
                local_to_world=prim.local_to_world,
                cull_backfaces=getattr(prim, "cull_backfaces", True),
                front_face_ccw=getattr(prim, "front_face_ccw", True),
            )
            draw_primitive(
                hud, wprim, hud_world, hud_view, hud_proj, scene=scene, zbuf=hud_z
            )

        pad_x = int(surface.get_width() * 0.02)
        pad_y = int(surface.get_height() * 0.18)
        surface.blit(hud, (pad_x, pad_y))
