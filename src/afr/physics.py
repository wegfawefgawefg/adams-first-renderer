from __future__ import annotations

from dataclasses import dataclass
import math

from afr.linalg.vec3 import Vec3


@dataclass(frozen=True)
class Triangle:
    a: Vec3
    b: Vec3
    c: Vec3

    # Precomputed XZ bounds for spatial hashing.
    min_x: float
    max_x: float
    min_z: float
    max_z: float


@dataclass
class SpatialHashXZ:
    """Very simple spatial hash grid in XZ for static triangle meshes."""

    cell_size: float = 2.0

    def __post_init__(self) -> None:
        self.inv_cell_size = 1.0 / float(self.cell_size) if self.cell_size else 1.0
        self.cells: dict[tuple[int, int], list[int]] = {}

    def _cell(self, x: float, z: float) -> tuple[int, int]:
        return (math.floor(x * self.inv_cell_size), math.floor(z * self.inv_cell_size))

    def insert_tri(self, tri_idx: int, tri: Triangle) -> None:
        ix0, iz0 = self._cell(tri.min_x, tri.min_z)
        ix1, iz1 = self._cell(tri.max_x, tri.max_z)
        for iz in range(iz0, iz1 + 1):
            for ix in range(ix0, ix1 + 1):
                self.cells.setdefault((ix, iz), []).append(tri_idx)

    def query_aabb(self, min_x: float, max_x: float, min_z: float, max_z: float) -> list[int]:
        ix0, iz0 = self._cell(min_x, min_z)
        ix1, iz1 = self._cell(max_x, max_z)
        out: list[int] = []
        seen: set[int] = set()
        for iz in range(iz0, iz1 + 1):
            for ix in range(ix0, ix1 + 1):
                lst = self.cells.get((ix, iz))
                if not lst:
                    continue
                for ti in lst:
                    if ti in seen:
                        continue
                    seen.add(ti)
                    out.append(ti)
        return out


@dataclass
class CastleCollider:
    tris: list[Triangle]
    grid: SpatialHashXZ

    def query_sphere(self, center: Vec3, radius: float) -> list[int]:
        r = float(radius)
        return self.grid.query_aabb(center.x - r, center.x + r, center.z - r, center.z + r)


def _closest_point_on_triangle(p: Vec3, a: Vec3, b: Vec3, c: Vec3) -> Vec3:
    # Christer Ericson, "Real-Time Collision Detection" (closest point on triangle).
    ab = b - a
    ac = c - a
    ap = p - a
    d1 = ab.dot(ap)
    d2 = ac.dot(ap)
    if d1 <= 0.0 and d2 <= 0.0:
        return a

    bp = p - b
    d3 = ab.dot(bp)
    d4 = ac.dot(bp)
    if d3 >= 0.0 and d4 <= d3:
        return b

    vc = d1 * d4 - d3 * d2
    if vc <= 0.0 and d1 >= 0.0 and d3 <= 0.0:
        v = d1 / (d1 - d3) if (d1 - d3) != 0.0 else 0.0
        return a + ab * v

    cp = p - c
    d5 = ab.dot(cp)
    d6 = ac.dot(cp)
    if d6 >= 0.0 and d5 <= d6:
        return c

    vb = d5 * d2 - d1 * d6
    if vb <= 0.0 and d2 >= 0.0 and d6 <= 0.0:
        w = d2 / (d2 - d6) if (d2 - d6) != 0.0 else 0.0
        return a + ac * w

    va = d3 * d6 - d5 * d4
    if va <= 0.0 and (d4 - d3) >= 0.0 and (d5 - d6) >= 0.0:
        w = (d4 - d3) / ((d4 - d3) + (d5 - d6)) if ((d4 - d3) + (d5 - d6)) != 0.0 else 0.0
        return b + (c - b) * w

    denom = (va + vb + vc)
    if denom == 0.0:
        return a
    inv = 1.0 / denom
    v = vb * inv
    w = vc * inv
    return a + ab * v + ac * w


def build_collider_from_scene(scene) -> CastleCollider:
    """Build a static collider from a SceneData (castle)."""
    tris: list[Triangle] = []
    grid = SpatialHashXZ(cell_size=2.0)

    for prim in scene.primitives:
        # Transform once per vertex.
        verts_ws = [prim.local_to_world @ v for v in prim.mesh.positions]
        for (i1, i2, i3) in prim.mesh.indices:
            a = verts_ws[i1]
            b = verts_ws[i2]
            c = verts_ws[i3]
            min_x = min(a.x, b.x, c.x)
            max_x = max(a.x, b.x, c.x)
            min_z = min(a.z, b.z, c.z)
            max_z = max(a.z, b.z, c.z)
            tri = Triangle(a, b, c, min_x, max_x, min_z, max_z)
            idx = len(tris)
            tris.append(tri)
            grid.insert_tri(idx, tri)

    return CastleCollider(tris=tris, grid=grid)


def raycast_down_y(
    collider: CastleCollider,
    x: float,
    z: float,
    y0: float,
    *,
    query_radius: float = 4.0,
) -> float | None:
    """Raycast straight down from (x,y0,z). Returns hit Y (world) or None."""
    orig = Vec3(float(x), float(y0), float(z))
    dir = Vec3(0.0, -1.0, 0.0)

    best_t: float | None = None
    cand = collider.grid.query_aabb(x - query_radius, x + query_radius, z - query_radius, z + query_radius)
    eps = 1e-8
    for ti in cand:
        tri = collider.tris[ti]
        a, b, c = tri.a, tri.b, tri.c

        # Moller-Trumbore ray/triangle intersection.
        e1 = b - a
        e2 = c - a
        h = dir.cross(e2)
        det = e1.dot(h)
        if -eps < det < eps:
            continue
        inv_det = 1.0 / det
        s = orig - a
        u = inv_det * s.dot(h)
        if u < 0.0 or u > 1.0:
            continue
        q = s.cross(e1)
        v = inv_det * dir.dot(q)
        if v < 0.0 or (u + v) > 1.0:
            continue
        t = inv_det * e2.dot(q)
        if t <= eps:
            continue

        if best_t is None or t < best_t:
            best_t = t

    if best_t is None:
        return None
    return float(y0) - float(best_t)


def step_mario_physics(app_state, dt: float) -> None:
    """Integrate Mario movement with gravity and sphere-vs-triangle collisions."""
    if getattr(app_state, "castle_collider", None) is None:
        return
    if getattr(app_state, "mario_pos", None) is None:
        return

    collider: CastleCollider = app_state.castle_collider
    pos: Vec3 = app_state.mario_pos
    vel: Vec3 = getattr(app_state, "mario_vel", Vec3(0.0, 0.0, 0.0))
    on_ground: bool = bool(getattr(app_state, "on_ground", False))

    radius = float(getattr(app_state, "mario_radius", 0.35))

    # Controls.
    move_dir: Vec3 = getattr(app_state, "move_dir", Vec3(0.0, 0.0, 0.0))
    sprint: bool = bool(getattr(app_state, "sprint", False))
    jump_pressed: bool = bool(getattr(app_state, "jump_pressed", False))
    app_state.jump_pressed = False  # consume

    # Terraria-style substepping to avoid tunneling at low FPS:
    # run multiple smaller integrate+collide steps when movement is large.
    # Keep dt sane if the renderer stalls.
    dt = max(0.0, min(float(dt), 0.10))

    # Horizontal velocity intent (XZ).
    speed = 4.5 * (2.0 if sprint else 1.0)
    if move_dir.mag() > 0.0:
        d = move_dir.norm()
        hvel = Vec3(d.x * speed, 0.0, d.z * speed)
    else:
        hvel = Vec3(0.0, 0.0, 0.0)

    # Jump (impulse only when grounded at the start of the frame).
    if jump_pressed and on_ground:
        vel = Vec3(vel.x, 7.0, vel.z)
        on_ground = False

    gravity = 20.0  # units / s^2
    max_step = max(0.05, radius * 0.50)
    # Estimate max travel this frame (use current vertical speed + 1 frame of gravity).
    vy_est = vel.y - gravity * dt
    speed_est = math.sqrt(hvel.x * hvel.x + hvel.z * hvel.z + vy_est * vy_est)
    travel = speed_est * dt
    n = int(math.ceil(travel / max_step)) if travel > 0.0 else 1
    n = max(1, min(n, 8))
    sub_dt = dt / n

    r2 = radius * radius
    for _step in range(n):
        # Integrate.
        pos = Vec3(pos.x + hvel.x * sub_dt, pos.y, pos.z + hvel.z * sub_dt)
        vel = Vec3(vel.x, vel.y - gravity * sub_dt, vel.z)
        pos = Vec3(pos.x, pos.y + vel.y * sub_dt, pos.z)

        # Sphere center: feet pivot + radius.
        center = pos + Vec3(0.0, radius, 0.0)

        # Resolve penetrations (a couple Gauss-Seidel iterations).
        step_ground = False
        for _ in range(2):
            moved = False
            cand = collider.query_sphere(center, radius)
            for ti in cand:
                tri = collider.tris[ti]
                cp = _closest_point_on_triangle(center, tri.a, tri.b, tri.c)
                v = center - cp
                d2 = v.dot(v)
                if d2 >= r2:
                    continue

                moved = True
                if d2 > 1e-12:
                    dlen = math.sqrt(d2)
                    nrm = v * (1.0 / dlen)
                else:
                    # Degenerate: push up.
                    nrm = Vec3(0.0, 1.0, 0.0)

                center = cp + nrm * radius
                if nrm.y > 0.5:
                    step_ground = True
            if not moved:
                break

        # Convert back to feet pivot.
        pos = center - Vec3(0.0, radius, 0.0)

        if step_ground and vel.y < 0.0:
            vel = Vec3(vel.x, 0.0, vel.z)
        on_ground = step_ground or on_ground

    app_state.mario_pos = pos
    app_state.mario_vel = vel
    app_state.on_ground = on_ground
