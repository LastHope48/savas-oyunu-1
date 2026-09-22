import pygame
import pygame.gfxdraw
import copy


def draw_aa_line(surface, color, start, end, width=10):
    x1, y1 = start
    x2, y2 = end

    pygame.draw.line(
        surface,
        color,
        start,
        end,
        width
    )

    radius = width / 2

    pygame.gfxdraw.filled_circle(
        surface,
        round(x1),
        round(y1),
        round(radius),
        color
    )

    pygame.gfxdraw.filled_circle(
        surface,
        round(x2),
        round(y2),
        round(radius),
        color
    )

    pygame.gfxdraw.aacircle(
        surface,
        round(x1),
        round(y1),
        round(radius),
        color
    )

    pygame.gfxdraw.aacircle(
        surface,
        round(x2),
        round(y2),
        round(radius),
        color
    )

def invert_dict(d: dict):
    return {v: k for k, v in d.items()}
