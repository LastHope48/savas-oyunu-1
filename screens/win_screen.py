from .screen import Screen
import pygame
import colours

class WinScreen(Screen):
    def draw(self, surface: pygame.Surface):
        surface.fill(colours.YELLOW)

    def update(self, dt):
        pass

    def handle_event(self, event: pygame.event.Event):
        pass
