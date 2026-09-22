import pygame
import os

pygame.font.init()

class userFont:
    fonts = []

    def __init__(self, name: str, size: int, bold=False, italic=False):
        self.name = name
        self.size = size
        self.bold = bold
        self.italic = italic
        size_name_map = {
            0: {"name": "so small", "size": "0-10"},
            1: {"name": "small", "size": "10-20"},
            2: {"name": "mid", "size": "20-30"},
            3: {"name": "big", "size": "30-40"},
            4: {"name": "so big", "size": "40-50"},
            5: {"name": "huge", "size": "50-80"},
            6: {"name": "başlık", "size": "80-160"}
        }
        for index in size_name_map.keys():
            if self.size >= int(size_name_map[index]["size"].split("-")[0]) and self.size <= int(size_name_map[index]["size"].split("-")[1]):
                self.size_name = size_name_map[index]["name"]
        if os.path.exists(name):
            self.font = pygame.font.Font(name, size)
        else:
            self.font = pygame.font.SysFont(self.name, self.size, self.bold, self.italic)
        self.fonts.append(self)

    def return_text(self, text: str, color: tuple, background: tuple = None, antialias=True):
        return self.font.render(text, antialias, color, background)

    def draw_text(self, text: str, pos: tuple, surface: pygame.Surface, color: tuple, hiza: str = None, background: tuple = None, antialias=True):
        rendered = self.return_text(text, color, background, antialias)
        if hiza is not None:
            rect = rendered.get_rect()
            if not hasattr(rect, hiza):
                raise ValueError(f"Geçersiz hiza: {hiza}")
            setattr(rect, hiza, pos)
            surface.blit(rendered, rect)
        else:
            surface.blit(rendered, pos)