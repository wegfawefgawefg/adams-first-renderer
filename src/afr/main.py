import argparse
import sys
import time
import pygame

from afr.settings import WINDOW_RES, RES
from afr.draw import draw
from afr.core_rendering import draw_some_points
from afr.linalg.vec2 import Vec2
import afr.state as state
from afr.state import load


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(prog="afr", add_help=True)
    parser.add_argument(
        "--defer",
        action="store_true",
        help="Defer plotting into a pixel queue and blit it out gradually.",
    )
    parser.add_argument(
        "--blit-rate",
        type=int,
        default=state.BLIT_PPS,
        help="Pixels per second blitted when --defer is enabled.",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=60,
        help="Frame cap (use 0 for uncapped).",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Print FPS and effective blit throughput once per second.",
    )
    parser.add_argument(
        "--bench-blit",
        action="store_true",
        help="Benchmark blitting throughput by draining a pre-filled pixel queue (implies --defer).",
    )
    parser.add_argument(
        "--bench-pixels",
        type=int,
        default=200_000,
        help="How many pixels to enqueue for --bench-blit.",
    )
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)

    state.DEFERRED_PLOTTING = bool(args.defer) or bool(args.bench_blit)
    state.BLIT_PPS = max(0, int(args.blit_rate))
    state.BLIT_ACCUM = 0.0
    state.PLOT = (
        state.plot_deferred if state.DEFERRED_PLOTTING else state.plot_immediate
    )

    pygame.init()
    clock = pygame.time.Clock()

    window = pygame.display.set_mode(WINDOW_RES.to_tuple())
    # Use an RGBA surface so textured triangles can alpha-blend correctly.
    render_surface = pygame.Surface(RES.to_tuple(), flags=pygame.SRCALPHA, depth=32)
    app_state = state.AppState()
    load(app_state)

    if args.bench_blit:
        # Pre-fill a lot of pixels so the queue stays non-empty long enough to
        # observe a stable throughput plateau.
        w = render_surface.get_width()
        h = render_surface.get_height()
        n = max(0, int(args.bench_pixels))
        # Keep memory sane if someone passes a huge number accidentally.
        n = min(n, 5_000_000)
        for i in range(n):
            x = i % w
            y = (i // w) % h
            state.POINTS.append((Vec2(x, y), (255, 255, 255)))

    # Stats (effective drain throughput).
    stat_t0 = time.perf_counter()
    stat_pixels = 0
    stat_peak_pps = 0.0

    running = True
    while running:
        ms = clock.tick(args.fps) if args.fps > 0 else clock.tick()
        dt = ms / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT or (
                event.type == pygame.KEYDOWN
                and (event.key == pygame.K_ESCAPE or event.key == pygame.K_q)
            ):
                running = False

        if not state.DEFERRED_PLOTTING:
            render_surface.fill((0, 0, 0, 255))
            draw(render_surface, app_state)
        else:  # deferred mode
            if args.bench_blit:
                # Keep the queue non-empty so the benchmark measures steady-state drain.
                if not state.POINTS:
                    w = render_surface.get_width()
                    h = render_surface.get_height()
                    n = max(0, int(args.bench_pixels))
                    n = min(n, 5_000_000)
                    for i in range(n):
                        x = i % w
                        y = (i // w) % h
                        state.POINTS.append((Vec2(x, y), (255, 255, 255)))

                drained = draw_some_points(render_surface, dt, stats=args.stats)
                if args.stats:
                    stat_pixels += drained
            else:
                # Normal deferred behavior: only enqueue a new "frame" when the queue is empty,
                # then drain it gradually.
                if not state.POINTS:
                    state.NEEDS_CLEAR = True
                    draw(render_surface, app_state)
                drained = draw_some_points(render_surface, dt, stats=args.stats)
                if args.stats:
                    stat_pixels += drained

        stretched_surface = pygame.transform.scale(
            render_surface, WINDOW_RES.to_tuple()
        )
        window.blit(stretched_surface, (0, 0))
        pygame.display.update()

        if args.stats and state.DEFERRED_PLOTTING:
            now = time.perf_counter()
            elapsed = now - stat_t0
            if elapsed >= 1.0:
                pps = stat_pixels / elapsed if elapsed > 0 else 0.0
                stat_peak_pps = max(stat_peak_pps, pps)
                qlen = len(state.POINTS)
                fps = clock.get_fps()
                print(
                    f"fps={fps:5.1f} drained_pps={pps:10.1f} peak_pps={stat_peak_pps:10.1f} queue={qlen}"
                )
                stat_t0 = now
                stat_pixels = 0

    pygame.quit()


if __name__ == "__main__":
    main()
