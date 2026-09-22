WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRAY = (128, 128, 128)
BLACK = (0, 0, 0)
PURPLE = (128, 0, 128)
YELLOW = (128, 128, 0)
BROWN = (150, 75, 0)
LIGHT_BLUE = (23, 236, 236)


def darker(color: tuple, amount: int):
    return tuple(max(0, c - amount) for c in color[:3])

def lighter(color: tuple, amount: int):
    return tuple(min(255, c + amount) for c in color[:3])
