from .screen import Screen
import pygame
import colours
from calcs import calculate_size
from classes import userFont
from lang_support import Lang
import os
from basedir import BASE_DIR

class LoseScreen(Screen):
    def __init__(self, game):
        super().__init__(game)

        self._font = None

    def draw(self, surface: pygame.Surface):
        surface.fill(colours.RED)

        self.langs = {
            "lose_text": Lang(türkçe="Kaybettiniz!", english="You Lose!", arabic="لقد خسرت!", sanskritçe="त्वं हारितवान् !")
        }

        _bolum = calculate_size(50, 800, self.game.width)

        if self._font is None or self.title_font_size != int(_bolum):
            self.title_font_size = int(_bolum)

            if Lang.USING_LANG.lower() == "türkçe" or Lang.USING_LANG.lower() == "english":
                clarity_city = os.path.join(BASE_DIR, r"fonts/Clarity-city.ttf")
                self._font = userFont(clarity_city, self.title_font_size)

            elif Lang.USING_LANG.lower() == "arabic":
                self._font = userFont(
                    os.path.join(BASE_DIR, r"fonts/arabica.ttf"),
                    self.title_font_size
                )

            elif Lang.USING_LANG.lower() == "sanskrit":
                self._font = userFont(
                    os.path.join(BASE_DIR, r"fonts/arabica.ttf"),
                    self.title_font_size
                )

        if self._font is not None:
            self._font.draw_text(f"{self.langs['lose_text'].get(self.game.settings.get('language'))}", (self.game.width//2, int(self.game.height*0.11)), surface, colours.WHITE, "center")

    def update(self, dt):
        pass

    def handle_event(self, event: pygame.event.Event):
        pass
