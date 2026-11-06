import os
import pygame
import json
from lang_support import Lang

class Music:
    def __init__(self, filename: str | os.PathLike, name: str | Lang | None = None, default=False):
        '''
        Ayarlarda seçmek için hazır müzik sınıfı.

        Args:
            filename: Tam dosya yolu.
            name: Görünecek isim. Seçilmezse `filename` gösterilir.
            default: Müziğin seçilmemiş müziği taklit ediyor mu?
        '''
        self.filename = filename
        self.name = name or self.filename
        self.default = default

    def play(self, volume: float, loops: int = -1):
        if self.default: return

        pygame.mixer.music.load(self.filename)
        pygame.mixer.music.set_volume(volume)

        pygame.mixer.music.play(loops=loops)

    def to_dict(self) -> dict:
        '''Objeyi `Python Dict`e çevirir.'''
        return {
            "filename": self.filename,
            "name": self.name,
            "default": self.default
        }

    def to_json(self):
        '''Objeyi `JSON` formatına çevirir.'''
        return json.loads(self.to_dict())

    @classmethod
    def from_dict(cls, d) -> "Music":
        print("MUSİC",d)

        return cls(
            d["filename"],
            d["name"] if type(d["name"]) == str else Lang.from_dict(d["name"]),
            d["default"]
        )

    @classmethod
    def from_json(cls, d) -> "Music":
        return Music.from_dict(json.loads(d))

    def __str__(self):
        return str(self.name)
    