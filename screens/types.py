from enum import Enum, auto

class ScreenType(Enum):
    MENU = auto()
    GAME = auto()
    LOAD = auto()
    SAVE = auto()
    SETTINGS = auto()
    WIN = auto()
    LOSE = auto()
    WARN = auto()
