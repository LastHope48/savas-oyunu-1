import os
import pygame

class Music:
    def __init__(self, filename: str | os.PathLike, name: str | None = None):
        self.filename = filename
        self.name = name or self.filename

    def play(self, volume: float, loops: int = -1):
        pygame.mixer.music.load(self.filename)
        pygame.mixer.music.set_volume(volume)

        pygame.mixer.music.play(loops=loops)

    def __str__(self):
        return self.name