import pygame

from afr.settings import WINDOW_RES, RES
from afr.draw import draw, draw_once

pygame.init()


def main():
    window = pygame.display.set_mode(WINDOW_RES.to_tuple())
    render_surface = pygame.Surface(RES.to_tuple())

    draw_once(render_surface)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (
                event.type == pygame.KEYDOWN
                and (event.key == pygame.K_ESCAPE or event.key == pygame.K_q)
            ):
                running = False

        render_surface.fill((0, 0, 0))
        draw(render_surface)

        stretched_surface = pygame.transform.scale(
            render_surface, WINDOW_RES.to_tuple()
        )
        window.blit(stretched_surface, (0, 0))
        pygame.display.update()

    pygame.quit()


if __name__ == "__main__":
    main()
