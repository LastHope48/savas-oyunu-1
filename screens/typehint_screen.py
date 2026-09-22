from abc import ABC, abstractmethod
import pygame
import typehint_game

class Screen(ABC):

    def __init__(self, game):
        self.game: typehint_game.Game

    @abstractmethod
    def draw(self, surface: pygame.Surface):
        pass

    @abstractmethod
    def handle_event(self, event: pygame.event.Event):
        pass

    @abstractmethod
    def update(self, dt):
        pass

    def on_exit(self):
        pass

    def on_enter(self):
        pass
