import math
from gra.vec2 import Vec2
from gra.state import POINTS


def point(surface, pos):
    POINTS.append((pos, (255, 255, 255)))
    # pygame.draw.rect(surface, (255, 255, 255), (pos.x, pos.y, 1, 1))


def cpoint(surface, pos, c):
    POINTS.append((pos, c))


def line(surface, a, b):
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
        point(surface, Vec2(px, py))
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
                surface.set_at((x, y), col)


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
