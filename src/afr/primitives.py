import math
from afr.linalg.vec2 import Vec2
from afr.linalg.vec3 import Vec3
import afr.state as state


def point(surface, pos):
    cpoint(surface, pos, (255, 255, 255))


def cpoint(surface, pos, c):
    state.PLOT(surface, pos, c)


def line(surface, a, b, c):
    xd = b.x - a.x
    yd = b.y - a.y

    num_points = int(max(abs(xd), abs(yd)))
    # if line has length 0
    if num_points == 0:
        point(surface, a)
        return
    dx = xd / num_points
    dy = yd / num_points

    px = a.x
    py = a.y
    for _ in range(0, num_points + 1):
        cpoint(surface, Vec2(px, py), c)
        px += dx
        py += dy


def rline(surface, a, b):
    # base case (endpoints)
    dx = abs(b.x - a.x)
    dy = abs(b.y - a.y)
    if dx <= 1 and dy <= 1:
        point(surface, a)
        point(surface, b)
        return

    m = (a + b) / 2
    point(surface, m)
    rline(surface, a, m)
    rline(surface, m, b)


def rect(surface, p, size):
    a = p
    b = p + size
    line(surface, a, Vec2(b.x, a.y))
    line(surface, a, Vec2(a.x, b.y))
    line(surface, b, Vec2(a.x, b.y))
    line(surface, b, Vec2(b.x, a.y))


def triangle(surface, a, b, c):
    line(surface, a, b)
    line(surface, b, c)
    line(surface, a, c)


def triangle_filled(surface, a, b, c, col):
    """Filled triangle rasterization (simple bounding-box + edge test)."""
    w = surface.get_width()
    h = surface.get_height()

    min_x = int(max(0, math.floor(min(a.x, b.x, c.x))))
    max_x = int(min(w - 1, math.ceil(max(a.x, b.x, c.x))))
    min_y = int(max(0, math.floor(min(a.y, b.y, c.y))))
    max_y = int(min(h - 1, math.ceil(max(a.y, b.y, c.y))))

    if min_x > max_x or min_y > max_y:
        return

    def edge(p0, p1, x, y):
        return (x - p0.x) * (p1.y - p0.y) - (y - p0.y) * (p1.x - p0.x)

    # Determine winding so inside-test works for both CW and CCW input.
    area = edge(a, b, c.x, c.y)
    if area == 0:
        return

    for y in range(min_y, max_y + 1):
        py = y + 0.5
        for x in range(min_x, max_x + 1):
            px = x + 0.5
            w0 = edge(b, c, px, py)
            w1 = edge(c, a, px, py)
            w2 = edge(a, b, px, py)

            if area > 0:
                inside = w0 >= 0 and w1 >= 0 and w2 >= 0
            else:
                inside = w0 <= 0 and w1 <= 0 and w2 <= 0

            if inside:
                cpoint(surface, Vec2(x, y), col)


def triangle_filled_z(surface, a, b, c, col, zbuf):
    """Filled triangle with a simple Z-buffer (CPU).

    Inputs `a`, `b`, `c` are Vec3 where:
    - x,y are screen coordinates in pixels
    - z is depth (smaller z = closer)

    `zbuf` is a flat list of size (w*h) holding the closest z seen so far.
    """
    w = surface.get_width()
    h = surface.get_height()

    min_x = int(max(0, math.floor(min(a.x, b.x, c.x))))
    max_x = int(min(w - 1, math.ceil(max(a.x, b.x, c.x))))
    min_y = int(max(0, math.floor(min(a.y, b.y, c.y))))
    max_y = int(min(h - 1, math.ceil(max(a.y, b.y, c.y))))

    if min_x > max_x or min_y > max_y:
        return

    def edge(p0, p1, x, y):
        return (x - p0.x) * (p1.y - p0.y) - (y - p0.y) * (p1.x - p0.x)

    area = edge(a, b, c.x, c.y)
    if area == 0:
        return

    inv_area = 1.0 / area

    for y in range(min_y, max_y + 1):
        py = y + 0.5
        row = y * w
        for x in range(min_x, max_x + 1):
            px = x + 0.5
            w0 = edge(b, c, px, py)
            w1 = edge(c, a, px, py)
            w2 = edge(a, b, px, py)

            if area > 0:
                inside = w0 >= 0 and w1 >= 0 and w2 >= 0
            else:
                inside = w0 <= 0 and w1 <= 0 and w2 <= 0

            if not inside:
                continue

            # Barycentric weights (sum to 1).
            alpha = w0 * inv_area
            beta = w1 * inv_area
            gamma = w2 * inv_area
            z = alpha * a.z + beta * b.z + gamma * c.z

            idx = row + x
            if z < zbuf[idx]:
                zbuf[idx] = z
                cpoint(surface, Vec2(x, y), col)


def triangle_textured_z(surface, a, b, c, uva, uvb, uvc, texture, zbuf, shade=1.0):
    """Textured triangle with a simple Z-buffer (CPU).

    Inputs `a`, `b`, `c` are Vec3 where:
    - x,y are screen coordinates in pixels
    - z is depth (smaller z = closer)

    UVs are Vec2 in [0..1] (no wrapping, clamped).
    `shade` multiplies the sampled texture color (simple lighting).
    """
    w = surface.get_width()
    h = surface.get_height()

    min_x = int(max(0, math.floor(min(a.x, b.x, c.x))))
    max_x = int(min(w - 1, math.ceil(max(a.x, b.x, c.x))))
    min_y = int(max(0, math.floor(min(a.y, b.y, c.y))))
    max_y = int(min(h - 1, math.ceil(max(a.y, b.y, c.y))))

    if min_x > max_x or min_y > max_y:
        return

    tw = texture.get_width()
    th = texture.get_height()

    def edge(p0, p1, x, y):
        return (x - p0.x) * (p1.y - p0.y) - (y - p0.y) * (p1.x - p0.x)

    area = edge(a, b, c.x, c.y)
    if area == 0:
        return

    inv_area = 1.0 / area

    # Shade can be float or Vec3 (rgb multipliers).
    if isinstance(shade, (int, float)):
        shade_r = shade_g = shade_b = max(0.0, float(shade))
    else:
        shade_r = max(0.0, float(shade.x))
        shade_g = max(0.0, float(shade.y))
        shade_b = max(0.0, float(shade.z))

    for y in range(min_y, max_y + 1):
        py = y + 0.5
        row = y * w
        for x in range(min_x, max_x + 1):
            px = x + 0.5
            w0 = edge(b, c, px, py)
            w1 = edge(c, a, px, py)
            w2 = edge(a, b, px, py)

            if area > 0:
                inside = w0 >= 0 and w1 >= 0 and w2 >= 0
            else:
                inside = w0 <= 0 and w1 <= 0 and w2 <= 0

            if not inside:
                continue

            alpha = w0 * inv_area
            beta = w1 * inv_area
            gamma = w2 * inv_area

            z = alpha * a.z + beta * b.z + gamma * c.z
            idx = row + x
            if z >= zbuf[idx]:
                continue
            zbuf[idx] = z

            u = alpha * uva.x + beta * uvb.x + gamma * uvc.x
            v = alpha * uva.y + beta * uvb.y + gamma * uvc.y

            # Clamp (no wrapping for now).
            if u < 0.0:
                u = 0.0
            elif u > 1.0:
                u = 1.0
            if v < 0.0:
                v = 0.0
            elif v > 1.0:
                v = 1.0

            tx = int(u * (tw - 1))
            ty = int(v * (th - 1))
            r, g, b_, a_ = texture.get_at((tx, ty))
            if a_ == 0:
                continue

            sr = min(255, int(r * shade_r))
            sg = min(255, int(g * shade_g))
            sb = min(255, int(b_ * shade_b))

            # Deferred plotting can't blend (no destination pixel yet).
            if state.PLOT is state.plot_deferred or a_ == 255:
                cpoint(surface, Vec2(x, y), (sr, sg, sb, int(a_)))
                continue

            # Alpha blend (source-over) in immediate mode.
            dr, dg, db, da = surface.get_at((x, y))
            sa = a_ / 255.0
            inv = 1.0 - sa
            out_r = int(sr * sa + dr * inv)
            out_g = int(sg * sa + dg * inv)
            out_b = int(sb * sa + db * inv)
            out_a = int(a_ + da * inv)
            cpoint(surface, Vec2(x, y), (out_r, out_g, out_b, out_a))


def triangle_filled_scanline(surface, a, b, c, col):
    """Filled triangle rasterization (simple scanline fill).

    This is usually less wasteful than the bounding-box method for long/thin
    triangles because it fills only the horizontal spans that intersect the
    triangle.
    """
    # Degenerate (area ~ 0).
    if (b - a).cross(c - a) == 0:
        return

    w = surface.get_width()
    h = surface.get_height()

    # Sort by Y: v0 (top), v1 (mid), v2 (bottom).
    v0, v1, v2 = sorted([a, b, c], key=lambda p: p.y)

    def x_at_y(p0, p1, y):
        dy = p1.y - p0.y
        if dy == 0:
            return p0.x
        t = (y - p0.y) / dy
        return p0.x + t * (p1.x - p0.x)

    y_start = int(max(0, math.ceil(v0.y)))
    y_end = int(min(h - 1, math.floor(v2.y)))
    if y_start > y_end:
        return

    for y in range(y_start, y_end + 1):
        # Sample at pixel center in Y.
        sample_y = y + 0.5

        if sample_y < v1.y:
            xa = x_at_y(v0, v2, sample_y)
            xb = x_at_y(v0, v1, sample_y)
        else:
            xa = x_at_y(v0, v2, sample_y)
            xb = x_at_y(v1, v2, sample_y)

        if xa > xb:
            xa, xb = xb, xa

        x_start = int(max(0, math.ceil(xa)))
        x_end = int(min(w - 1, math.floor(xb)))
        for x in range(x_start, x_end + 1):
            cpoint(surface, Vec2(x, y), col)


def lines(surface, ps):
    if len(ps) == 0:
        return
    if len(ps) == 1:
        return
    for i in range(0, len(ps) - 1):
        line(surface, ps[i], ps[i + 1])

    line(surface, ps[0], ps[-1])


def polygon(surface, ps):
    lines(surface, ps)


def regular_polygon(surface, p, r, num_points):
    points = []
    for i in range(num_points):
        angle = i * (2 * math.pi / num_points)
        x = p.x + r * math.cos(angle)
        y = p.y + r * math.sin(angle)
        points.append(Vec2(x, y))
    polygon(surface, points)


def circle(surface, p, r):
    regular_polygon(surface, p, r, 12)


def circle_fill_raster(surface, p, r, c):
    # two for loops and radius check
    for y in range(-r, r + 1):
        for x in range(-r, r + 1):
            # shader
            if x * x + y * y <= r * r:
                cpoint(surface, p + Vec2(x, y), c)


# smae as fill raster but in the r+w and r-w
def circle_raster_lines(surface, p, r, c, w):
    for y in range(-r, r + 1):
        for x in range(-r, r + 1):
            if x * x + y * y <= (r + w) * (r + w) and x * x + y * y >= (r - w) * (
                r - w
            ):
                cpoint(surface, p + Vec2(x, y), c)


def circle_shader(surface, p, r, c):
    def c_shader(surface, pos):
        dist_x = pos.x - p.x
        dist_y = pos.y - p.y
        if dist_x * dist_x + dist_y * dist_y <= r * r:
            return c
        return None

    shader(surface, c_shader, ())


def shader(surface, func, args):
    surface_width = surface.get_width()
    surface_height = surface.get_height()
    for y in range(surface_height):
        for x in range(surface_width):
            col = func(surface, Vec2(x, y), *args)
            if col is not None:
                cpoint(surface, Vec2(x, y), col)


"""
shader_code = loadf(shader path);
cshader_handle = nvidia.compile(String shader_code, hardward_id);
buffer
shader_args
run_shader(buffer, cshader_handle, shader_args);
"""

"""
    vector project to the line, use dist to line, w is thickness
"""


def line_shader(surface, a, b, w, c):
    def l_shader(surface, pos):
        ab = b - a
        ap = pos - a
        a_proj_b = ab.norm() * ap.dot(ab.norm())
        closest = a + a_proj_b
        # check if in lines rect
        if (a.x <= closest.x <= b.x or a.x >= closest.x >= b.x) and (
            a.y <= closest.y <= b.y or a.y >= closest.y >= b.y
        ):
            # Check the distance to the line
            dist = (closest - pos).mag()
            if dist <= w:
                return c
        return None

    shader(surface, l_shader, ())
