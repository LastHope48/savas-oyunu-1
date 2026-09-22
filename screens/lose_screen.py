from .screen import Screen
import pygame
import colours
from calcs import calculate_size
from classes import userFont
from lang_support import Lang

class LoseScreen(Screen):
    def draw(self, surface: pygame.Surface):
        surface.fill(colours.RED)

        self.langs = {
            "lose_text": Lang(türkçe="Kaybettiniz!", english="You Lose!")
        }

        _bolum = calculate_size(50, 800, self.game.width)
        _font = userFont("arial", int(_bolum))
        _font.draw_text(f"{self.langs['lose_text'].get(self.game.settings.get('language'))}", (self.game.width//2, int(self.game.height*0.11)), surface, colours.WHITE, "center")

    def update(self, dt):
        pass

    def handle_event(self, event: pygame.event.Event):
        pass
