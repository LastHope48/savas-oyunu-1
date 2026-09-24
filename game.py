import pygame
from pygame import mixer

import logging
from classes import defaults as game_data_defaults
import classes
from flags import SUCCESS, FAILURE
from version import VERSION

from update_manager import apply_pending_update

from save_manager import SaveManager
from settings import Settings
from pass_manager import HashManager
from console import CommandParser
from dump import Dump

from gamedata import GameData
import os
from basedir import BASE_DIR

from screens.screen_manager import ScreenManager


class Game:
    def __init__(self):
        pygame.init()
        mixer.init()

        self.mixer = mixer

        self.info = pygame.display.Info()

        self.screen = pygame.display.set_mode((800, 800), pygame.RESIZABLE)
        pygame.display.set_caption("Öz Hakiki GTA 7")
        self.clock = pygame.time.Clock()

        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(filename)s: %(lineno)d [%(funcName)s] | %(message)s',
            filename="game.log"
        )

        self.logger = logging.getLogger(__name__)

        self.GAME_VERSION = VERSION

        self.save_manager = SaveManager(os.path.join(BASE_DIR, "saves"))

        self.settings = Settings(file=os.path.join(BASE_DIR, "settings.json"))
        self.settings.load()

        self.hash_manager = HashManager(filename=os.path.join(BASE_DIR, "securedvars"))

        self.command_parser = CommandParser()
        self.command_parser.add_variable("dt_multiplier", 1)
        self.command_parser.add_command("dt", self.multiply_dt, [float], success_text="Delta Time multiplied to [arg1]")
        self.dump = Dump()

        self.mixer.music.load(
            os.path.join(
                BASE_DIR,
                r"musics/menu_theme.mp3"
            )
        )

        self.mixer.music.play(-1)

        self.dump("last_music", None)

        self.running = True

        self.game_data: GameData = GameData.to_gamedata(game_data_defaults)

        classes.Slot.create_slots(self.save_manager)

        self.played = False

        self.screen_manager = ScreenManager(self)

    @property
    def width(self):
        return self.screen.get_width()

    @property
    def height(self):
        return self.screen.get_height()

    def multiply_dt(self, value):
        self.command_parser.variables["dt_multiplier"] = value
        return SUCCESS, f"Oyun {self.command_parser.variables['dt_multiplier']} kat daha hızlı."

    def run(self):
        while self.running:
            orig_dt = self.clock.tick(self.settings.get("fps")) / 1000 # Şimdilik sabit
            dt = orig_dt * self.command_parser.variables["dt_multiplier"]

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                self.screen_manager.handle_event(event)


            self.screen_manager.update(dt)
    
            self.screen_manager.draw(self.screen)

            pygame.display.flip()

        apply_pending_update()
        pygame.quit()

        if self.played:
            self.save_manager.save_last_slot(self.game_data)
