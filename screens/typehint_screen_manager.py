import pygame
from .typehint_screen import Screen
from enum import auto

class ScreenManager:
    def __init__(self, game):
        self.game = game
        self.screens: dict[auto, Screen]

        self.current_screen: Screen
        self.last_screen: Screen

    def set_screen(self, screen_type, **transfer_data): ...

    def get_screen(self, screen_type) -> Screen: ...

    def draw(self, surface: pygame.Surface): ...

    def update(self, dt): ...

    def handle_event(self, event: pygame.event.Event): ...

    def get_last_screen(self): ...
