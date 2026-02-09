# line demo
# a = center / 2
# b = center + a
# line(surface, a, b)
# line to mouse pos from tl
# line(surface, Vec2(0, 0), mouse_pos())

# rect demo
# rect(surface, center, 20)

# triangle demo
# a = center / 2
# b = center + Vec2(20, -20)
# c = center + Vec2(0, 20)
# triangle(surface, a, b, c)

# lines demo
# polygon_points = [
#     center + Vec2(0, -30),
#     center + Vec2(25, -10),
#     center + Vec2(15, 20),
#     center + Vec2(-15, 20),
#     center + Vec2(-25, -10),
# ]
# lines(surface, polygon_points)

# regular polygon demo
# center = RES / 2
# for i in range(3, 10):
#     regular_polygon(surface, center, 50, i)

# circle demo
# r = 10
# center = RES / 2
# circle(surface, center, r)

# circle raster demo
# circle_raster_lines(surface, center, r * 6, WHITE, 1)

# circle shader demo
# r = 40
# circle_shader(surface, center, r, WHITE)

# a = center / 2
# b = center + a
# line_shader(surface, a, b, 0.1, WHITE)
