import pygame
from pygame import mixer

import logging

from gamedata import GameData

from screens.typehint_screen_manager import ScreenManager

from save_manager import SaveManager
from pass_manager import HashManager
from settings import Settings
from console import CommandParser
from dump import Dump

class Game:
    def __init__(self):

        self.mixer: mixer

        self.screen: pygame.Surface

        self.clock: pygame.time.Clock


        self.logger: logging.Logger

        self.running: bool

        self.save_manager: SaveManager
        self.hash_manager: HashManager
        self.settings: Settings
        self.command_parser: CommandParser
        self.dump: Dump

        self.game_data: GameData
        self.screen_manager: ScreenManager
        self.info: pygame.display._VidInfo

        self.played: bool

        self.GAME_VERSION: str

    @property
    def height(self) -> int: ...

    @property
    def width(self) -> int: ...

    def run(self):
        '''
        Runs the game until self.running is False.
        '''