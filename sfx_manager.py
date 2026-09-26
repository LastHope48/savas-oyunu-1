import pygame
import os
import logging
import warnings

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(filename)s: "
            "%(lineno)d [%(funcName)s] | %(message)s",
    filename="game.log",
)

pygame.init()

class SFX:
    def __init__(self, mixer: pygame.mixer, filename: str | os.PathLike):
        self.mixer = mixer

        try:
            self.file = pygame.mixer.Sound(filename)
            self.playable = True
            
        except FileNotFoundError:
            self.file = None
            self.playable = False

    def play(self, volume: float):
        if not self.playable: return

        self.file.set_volume(volume)

        self.file.play()

logging.info("SFX class created.")

class SFXManager:
    def __init__(self, **sfx):
        self.sfx: dict[str, SFX] = sfx

    def play(self, name: str, volume: float):
        self.sfx[name].play(volume)

    def get(self, name: str):
        self.sfx.get(name)

    def add(self, mixer: pygame.mixer, name: str, filename: str | os.PathLike):
        if name in self.sfx.keys():
            warnings.warn(
                f"SFX named {name} is already in SFXes. Did you mean another name?"
            )

            logging.warning(
                f"SFX named {name} is already in SFX dictionary."
            )

        self.sfx[name] = SFX(mixer, filename)

logging.info("SFXManager class created.")
