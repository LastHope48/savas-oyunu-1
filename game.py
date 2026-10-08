import pygame
from pygame import mixer

import json
from datetime import datetime

import logging
from classes import defaults as game_data_defaults
import classes
import colours
import copy

from levels import level17

from fonts import (
    font1_univ,
    font2_univ,
    font3_univ,
    font4_univ,
    font1_arabic,
    font2_arabic,
    font3_arabic,
    font4_arabic,
    font1_sanskrit,
    font2_sanskrit,
    font3_sanskrit,
    font4_sanskrit,
    dfont1_univ,
    dfont2_univ,
    dfont3_univ,
    dfont4_univ,
    dfont5_univ,
    dfont6_univ,
    dfont7_univ,
    dfont1_arabic,
    dfont2_arabic,
    dfont3_arabic,
    dfont4_arabic,
    dfont5_arabic,
    dfont6_arabic,
    dfont7_arabic,
    dfont1_sanskrit,
    dfont2_sanskrit,
    dfont3_sanskrit,
    dfont4_sanskrit,
    dfont5_sanskrit,
    dfont6_sanskrit,
    dfont7_sanskrit
)

from flags import SUCCESS
from version import VERSION
from lang_support import Lang
import threading

from update_manager import apply_pending_update

from save_manager import SaveManager
from settings import Settings
from pass_manager import HashManager
from console import CommandParser
from sfx_manager import SFXManager
from achievements import Achievements
from device_id import DeviceID
from val_manager import ValueManager

from dump import Dump

from gamedata import GameData
import os
from basedir import BASE_DIR

from screens.screen_manager import ScreenManager


class Game:
    GAME_FILE = os.path.join(BASE_DIR, "game_data.dat")
    DEFAULT_GAME_DATA = {
        "worlds_accessable": False
    }

    def __init__(self):
        pygame.init()
        mixer.init()

        self.mixer = mixer

        self.cheated = False

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

        self.hash_manager = HashManager(filename=os.path.join(BASE_DIR, "securedvars"))

        self.settings = Settings(file=os.path.join(BASE_DIR, "settings.json"))
        self.settings.load()

        Lang.USING_LANG = self.settings.get("language")

        self.command_parser = CommandParser()
        self.command_parser.add_variable("dt_multiplier", 1)
        self.command_parser.add_command("dt", self.multiply_dt, [float], success_text="Delta Time multiplied to [arg1]")

        self.command_parser.add_command("fun", self.fun, [str])

        self.dump = Dump()

        self.dump("new_game", False)
        self.dump("gun_combo", False)

        self.sfx_manager = SFXManager()
        self.sfx_manager.add(self.mixer, "click", os.path.join(BASE_DIR, r"sounds/click.wav"))

        self.illegal = False

        self.achievements = None
        self.device = None
        self.offline = False
        self.illegal = False
        self.console_used = False

        self.initing_online_data = True

        threading.Thread(target=self.initialize_online_data, daemon=True).start()

        self.val_manager = ValueManager()

        if self.settings.get("music"):
            self.mixer.music.set_volume(self.settings.get("music_volume"))

        else:
            self.mixer.music.set_volume(0.0)

        self.mixer.music.load(
            os.path.join(
                BASE_DIR,
                r"musics/menu_theme.mp3"
            )
        )

        self.mixer.music.play(-1)

        self.dump("last_music", None)

        self.fonts = {
            "türkçe-1": font1_univ,
            "türkçe-2": font2_univ,
            "türkçe-3": font3_univ,
            "türkçe-4": font4_univ,

            "english-1": font1_univ,
            "english-2": font2_univ,
            "english-3": font3_univ,
            "english-4": font4_univ,

            "arabic-1": font1_arabic,
            "arabic-2": font2_arabic,
            "arabic-3": font3_arabic,
            "arabic-4": font4_arabic,

            "sanskrit-1": font1_sanskrit,
            "sanskrit-2": font2_sanskrit,
            "sanskrit-3": font3_sanskrit,
            "sanskrit-4": font4_sanskrit,

            "dtürkçe-1": dfont1_univ,
            "dtürkçe-2": dfont2_univ,
            "dtürkçe-3": dfont3_univ,
            "dtürkçe-4": dfont4_univ,
            "dtürkçe-5": dfont5_univ,
            "dtürkçe-6": dfont6_univ,
            "dtürkçe-7": dfont7_univ,

            "denglish-1": dfont1_univ,
            "denglish-2": dfont2_univ,
            "denglish-3": dfont3_univ,
            "denglish-4": dfont4_univ,
            "denglish-5": dfont5_univ,
            "denglish-6": dfont6_univ,
            "denglish-7": dfont7_univ,

            "darabic-1": dfont1_arabic,
            "darabic-2": dfont2_arabic,
            "darabic-3": dfont3_arabic,
            "darabic-4": dfont4_arabic,
            "darabic-5": dfont5_arabic,
            "darabic-6": dfont6_arabic,
            "darabic-7": dfont7_arabic,
            
            "dsanskrit-1": dfont1_sanskrit,
            "dsanskrit-2": dfont2_sanskrit,
            "dsanskrit-3": dfont3_sanskrit,
            "dsanskrit-4": dfont4_sanskrit,
            "dsanskrit-5": dfont5_sanskrit,
            "dsanskrit-6": dfont6_sanskrit,
            "dsanskrit-7": dfont7_sanskrit
        }

        self.running = True

        self.game_data: GameData = GameData.to_gamedata(game_data_defaults)

        classes.Slot.create_slots(self.save_manager, self.fonts["türkçe-2"])
        classes.Player.set_settings_manager(self.settings)
        classes.Enemy.set_val_manager(self.val_manager)

        self.played = False

        self.const_game_data = None

        self.last_boss = "normal"

        if not os.path.exists(Game.GAME_FILE):
            with open(Game.GAME_FILE, "w", encoding="utf-8") as f:
                json.dump(
                    Game.DEFAULT_GAME_DATA,
                    f,
                    indent=4
                )

                self.const_game_data = copy.deepcopy(Game.DEFAULT_GAME_DATA)

        else:
            with open(Game.GAME_FILE, "r", encoding="utf-8") as f:
                self.const_game_data = json.load(f)

        self.screen_manager = ScreenManager(self)

    @property
    def width(self):
        return self.screen.get_width()

    @property
    def height(self):
        return self.screen.get_height()

    def multiply_dt(self, value):
        self.command_parser.variables["dt_multiplier"] = value
        self.cheated = True

        return SUCCESS, f"Oyun {self.command_parser.variables['dt_multiplier']} kat daha hızlı."

    def fun(self, key: str):
        def append_cheat_gun():
            nonlocal self
            self.cheated = True

            classes.defaults["Player"].available_guns.append(
                classes.Gun(
                    "At Kafası",
                    colours.lighter(
                        colours.BLACK,
                        30
                    ),
                    40,
                    700,
                    os.path.join(BASE_DIR,r"images/silver_silahr.png"),
                    os.path.join(BASE_DIR,r"images/silver_silah_mermi.png"),
                    0.03,
                    "__deflected__"
                )
            )

            self.game_data.player.available_guns.append(
                classes.Gun(
                    "At Kafası",
                    colours.lighter(
                        colours.BLACK,
                        30
                    ),
                    40,
                    700,
                    os.path.join(BASE_DIR,r"images/silver_silahr.png"),
                    os.path.join(BASE_DIR,r"images/silver_silah_mermi.png"),
                    0.03,
                    "__deflected__"
                )
            )

        def append_slow_cheat_gun():
            nonlocal self
            self.cheated = True

            classes.defaults["Player"].available_guns.append(
                classes.Gun(
                    "Küçük Salyangoz Timmy",
                    colours.lighter(
                        colours.BLACK,
                        30
                    ),
                    40,
                    10,
                    os.path.join(BASE_DIR,r"images/fucking_snail.png"),
                    os.path.join(BASE_DIR,r"images/silver_silah_mermi.png"),
                    0.03,
                    "__deflected__",
                    img_size=0.1
                )
            )

            self.game_data.player.available_guns.append(
                classes.Gun(
                    "Küçük Salyangoz Timmy",
                    colours.lighter(
                        colours.BLACK,
                        30
                    ),
                    40,
                    10,
                    os.path.join(BASE_DIR,r"images/fucking_snail.png"),
                    os.path.join(BASE_DIR,r"images/silver_silah_mermi.png"),
                    0.03,
                    "__deflected__",
                    img_size=0.1
                )
            )

        def activate_gun_combo():
            nonlocal self
            self.cheated = True

            self.dump("gun_combo", True)

        def secret_boss():
            nonlocal self
            self.cheated = True
            self.last_boss = "urasin_sumuklu_pecetesi"

            virus = classes.Item(
                "Hastalıklı Hentai Virüsü",
                (124, 12, 231),
                [
                    classes.Effect(
                    "hp",
                    0.23,
                    seconds=0,
                    flags=(classes.Item.REDUCER,)
                    )
                ],
                classes.Item.TUP_IKSIR
            )

            index = None

            for i, enemy in enumerate(level17):
                if type(enemy) == classes.Boss and enemy.name.lower() == "demirin boklu telefonu":
                    index = i

            dialogues = [
                ("Boss", "Hapşu"),
                ("Player", "Çok yaşa"),
                ("Boss", "Heapşiyuu"),
                ("Player", "Çok yaşa"),
                ("Boss", "Hapşuu"),
                ("Boss", "Hocam çok hastayım (gırtlaktan gelen bir ölüm sesi)"),
                ("Player", "Ya bi git"),
                ("Boss", "Hastayımm"),
                ("Boss", "Hapşu"),
                ("Player", "Çok yaşa"),
                ("Boss", "..."),
                ("Player", "...")
            ]

            for i in range(50):
                dialogues.append(
                    ("Boss", "Hapşu")
                )

                dialogues.append(("Player", "Çok yaşa"))

            dialogues.append(("Boss", "Hapşu"))
            dialogues.append(("Player", "YAŞA ARTIK"))

            if index is not None:
                level17.clear()

                level17.append(
                    classes.Boss(
                        100_000,
                        1,
                        [classes.EnemyAbilities.ABILITY_SNEEZE],
                        r_image_name=os.path.join(BASE_DIR, r"images/sumuklu_pecete.png"),
                        l_image_name=os.path.join(BASE_DIR, r"images/sumuklu_pecete.png"),
                        collisions=False,
                        name="Uras'ın Sümüklü Peçetesi",
                        bagimsiz_summons=[
                            classes.Enemy(
                                1,
                                0.2,
                                [classes.EnemyAbilities.ABILITY_ARROWS],
                                r_image_name=os.path.join(BASE_DIR, r"images/at_kafasi.png"),
                                l_image_name=os.path.join(BASE_DIR, r"images/at_kafasi.png"),
                                arrow_image=os.path.join(BASE_DIR, r"images/parlama.png"),
                                drops=[
                                    virus.copy(),
                                    virus.copy(),
                                    virus.copy(),
                                    virus.copy(),
                                    virus.copy(),
                                    virus.copy(),
                                    virus.copy(),
                                    virus.copy(),
                                    virus.copy(),
                                    virus.copy(),
                                    virus.copy(),
                                    virus.copy(),
                                    virus.copy(),
                                    virus.copy(),
                                    virus.copy(),
                                    virus.copy(),
                                    virus.copy(),
                                    virus.copy(),
                                    virus.copy(),
                                    virus.copy(),
                                    virus.copy(),
                                    virus.copy(),
                                    virus.copy(),
                                    virus.copy(),
                                    virus.copy(),
                                    virus.copy(),
                                    virus.copy(),
                                    virus.copy(),
                                    virus.copy(),
                                    virus.copy(),
                                    virus.copy(),
                                    virus.copy()
                                ]
                            )
                        ],
                        cooldown_bagimsiz_summons=classes.Cooldown(1),
                        scene_dialogues=dialogues
                    )
                )

        def nothing():
            pass

        cheat_map = {
            "slow_cheat_gun": append_slow_cheat_gun,
            "cheat_gun": append_cheat_gun,
            "activate_gun_combo": activate_gun_combo,
            "cok_yasa_uras": secret_boss
        }

        cheat_map.get(key, nothing)()
        runned = cheat_map.get(key, nothing)

        return SUCCESS, f"{key} anahtarı doğru ve çalıştı!" if runned != nothing else f"{key} diye bir anahtar yok."


    def initialize_online_data(self):
        try:
            self.logger.info("Online sistem başlatılıyor...")

            self.logger.info("DeviceID oluşturuluyor...")
            device = DeviceID()
            self.logger.info("DeviceID başarıyla oluşturuldu.")

            self.logger.info("Achievements oluşturuluyor...")
            achievements = Achievements(device)
            self.logger.info("Achievements başarıyla oluşturuldu.")

            self.device = device
            self.achievements = achievements

            self.logger.info("Online sistem başarıyla başlatıldı.")

        except ConnectionError as e:
            self.logger.exception(f"İnternet bağlantısı hatası: {e}")
            self.illegal = False
            self.offline = True

        except (ValueError, FileNotFoundError) as e:
            self.logger.exception(f"Online sistem veri/dosya hatası: {e}")
            self.illegal = True
            self.offline = False

        except Exception as e:
            self.logger.exception(f"Online sistem başlatılamadı: {e}")

        finally:
            self.initing_online_data = False

    def run(self):
        if self.settings.get("fullscreen"):
            self.screen = pygame.display.set_mode((self.info.current_w, self.info.current_h), pygame.FULLSCREEN)

        while self.running:
            orig_dt = self.clock.tick(self.settings.get("fps")) / 1000
            dt = orig_dt * self.command_parser.variables["dt_multiplier"]

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RCTRL:
                        home = os.path.expanduser('~')

                        desktop_path = os.path.join(home, 'Desktop')

                        # Eğer Desktop klasörü yoksa alternatif olarak Masaüstü'ne bak
                        if not os.path.exists(desktop_path):
                            alt_path = os.path.join(home, 'Masaüstü')
                            if os.path.exists(alt_path):
                                desktop_path = alt_path

                        pygame.image.save(self.screen, os.path.join(desktop_path, rf"scr_shot - {datetime.now()}.png"))

                self.screen_manager.handle_event(event)


            self.screen_manager.update(dt)
            # 1. Update kısmında:
            if self.achievements is not None:
                self.achievements.update_popups(dt, self.width, self.height)

    
            self.screen_manager.draw(self.screen)

            # 2. Draw kısmında (UI ve yazıların en üstünde görünmesi için sonlara doğru):
            if self.achievements is not None:
                self.achievements.draw_popups(self.screen)

            pygame.display.flip()

        self.logger.info("Applying update if there")
        apply_pending_update()

        self.logger.info(f"Saving settings to '{self.settings.file}'.")
        self.settings.save()

        self.logger.info(f"Saving persistent values to '{self.val_manager.filename}'.")
        self.val_manager.save()

        self.logger.info("Quitting Pygame")

        self.mixer.stop()
        self.mixer.music.stop()
        self.mixer.quit()
        pygame.quit()

        if self.played:
            self.save_manager.save_last_slot(self.game_data, self.cheated)

        if self.const_game_data is not None:
            with open(Game.GAME_FILE, "w", encoding="utf-8") as f:
                json.dump(
                    self.const_game_data,
                    f,
                    indent=4
                )
