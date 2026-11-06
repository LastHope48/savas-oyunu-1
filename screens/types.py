from enum import Enum, auto

class ScreenType(Enum):
    MENU = auto()
    GAME = auto()
    WORLD_SELECT = auto()
    LOAD = auto()
    SAVE = auto()
    ACHIEVEMENTS = auto()
    SETTINGS = auto()
    MODS = auto()
    WIN = auto()
    LOSE = auto()
    WARN = auto()
    CREDITS = auto()
