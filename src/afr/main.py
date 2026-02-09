import argparse
import sys
import pygame

from afr.settings import WINDOW_RES, RES
from afr.draw import draw, draw_some_points
import afr.state as state


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
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)

    state.DEFERRED_PLOTTING = bool(args.defer)
    state.BLIT_PPS = max(0, int(args.blit_rate))
    state.BLIT_ACCUM = 0.0
    state.PLOT = state.plot_deferred if state.DEFERRED_PLOTTING else state.plot_immediate

    pygame.init()
    clock = pygame.time.Clock()

    window = pygame.display.set_mode(WINDOW_RES.to_tuple())
    render_surface = pygame.Surface(RES.to_tuple())

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
            render_surface.fill((0, 0, 0))
            draw(render_surface)
        else:  # defered mode
            if not state.POINTS:
                render_surface.fill((0, 0, 0))
                draw(render_surface)
            else:
                draw_some_points(render_surface, dt)

        stretched_surface = pygame.transform.scale(
            render_surface, WINDOW_RES.to_tuple()
        )
        window.blit(stretched_surface, (0, 0))
        pygame.display.update()

    pygame.quit()


if __name__ == "__main__":
    main()
