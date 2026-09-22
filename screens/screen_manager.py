import pygame
from .types import ScreenType
from .menu_screen.main_menu_screen import MainMenuScreen
from .menu_screen.load_screen import LoadScreen
from .menu_screen.save_screen import SaveScreen
from .menu_screen.settings_screen import SettingsScreen
from .win_screen import WinScreen
from .lose_screen import LoseScreen
from .game_screen import GameScreen
from .warn_screen import WarnScreen
from typehint_game import Game
from .screen import Screen
from helper_funcs import invert_dict

class ScreenManager:
    def __init__(self, game: Game):
        self.game: Game = game
        self.screens = {
            ScreenType.MENU: MainMenuScreen(self.game),
            ScreenType.GAME: GameScreen(self.game),
            ScreenType.LOAD: LoadScreen(self.game),
            ScreenType.SAVE: SaveScreen(self.game),
            ScreenType.SETTINGS: SettingsScreen(self.game),
            ScreenType.WIN: WinScreen(self.game),
            ScreenType.LOSE: LoseScreen(self.game),
            ScreenType.WARN: WarnScreen(self.game),
        }

        self.screen_to_type = invert_dict(self.screens)

        self.current_screen: Screen = self.screens[ScreenType.MENU]
        self.last_screen: Screen = None

    def set_screen(self, screen_type: ScreenType, **transfer_data):
        self.last_screen = self.screen_to_type[self.current_screen]

        if hasattr(self.current_screen, "on_exit"):
            self.current_screen.on_exit()

        self.current_screen = self.screens[screen_type]

        if hasattr(self.current_screen, "on_enter"):
            self.current_screen.on_enter(transfer_data)

    def get_screen(self, screen_type: ScreenType) -> Screen:
        return self.screens[screen_type]

    def draw(self, surface: pygame.Surface):
        self.current_screen.draw(surface)

    def update(self, dt: int):
        self.current_screen.update(dt)

    def handle_event(self, event: pygame.event.Event):
        self.current_screen.handle_event(event)

    def get_last_screen(self):
        return self.last_screen
