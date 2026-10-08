import pygame
from pygame import mixer

import logging

from gamedata import GameData

from screens.typehint_screen_manager import ScreenManager

from save_manager import SaveManager
from pass_manager import HashManager
from settings import Settings
from console import CommandParser
from sfx_manager import SFXManager
from achievements import Achievements
from device_id import DeviceID
from dump import Dump
from val_manager import ValueManager
from typing import NoReturn, Literal
from userfont import userFont
from dfont import DynamicFont

LAST_BOSS_TYPES = Literal['normal', 'urasin_sumuklu_pecetesi']

class Game:
    GAME_FILE: str
    DEFAULT_GAME_DATA: dict

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
        self.sfx_manager: SFXManager
        self.achievements: Achievements
        self.val_manager: ValueManager
        self.device: DeviceID
        self.dump: Dump
        self.illegal: bool
        self.offline: bool
        self.console_used: bool
        self.fonts: dict[str, userFont | DynamicFont]
        self.initing_online_data: bool

        self.cheated: bool

        self.game_data: GameData
        self.screen_manager: ScreenManager
        self.info: pygame.display._VidInfo

        self.played: bool

        self.GAME_VERSION: str


        self.last_boss: LAST_BOSS_TYPES

        self.const_game_data: dict

    @property
    def height(self) -> int: ...

    @property
    def width(self) -> int: ...

    def run(self) -> NoReturn:
        '''
        Runs the game until `self.running` is False.
        '''