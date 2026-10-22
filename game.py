import os
import platform
import base64

os.environ['SDL_VIDEO_X11_WMCLASS'] = "savas_oyunu"
os.environ['SDL_VIDEO_WAYLAND_WMCLASS'] = "savas_oyunu"

if platform.system() == "Windows":
    import ctypes
    app_id = "savasoyunu.oyun.surum1"
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)

from helper_funcs import ensure_linux_desktop_entry
ensure_linux_desktop_entry()

import pygame
from pygame import mixer

from screens.types import ScreenType

import json
from datetime import datetime

import logging

from classes import defaults as game_data_defaults
from classes import constant_defaults

import classes
import colours
import copy

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
from console import CommandParser
from sfx_manager import SFXManager
from achievements import Achievements
from device_id import DeviceID
from val_manager import ValueManager
from juice import JuiceManager

from dump import Dump

from gamedata import GameData
import os
from basedir import BASE_DIR

from screens.screen_manager import ScreenManager
from levels import level17, levels

class Game:
    GAME_FILE = os.path.join(BASE_DIR, "game_data.dat")
    DEFAULT_GAME_DATA = {
        "worlds_accessable": False
    }

    IMG_FALLBACKS = {
        "enemy_r": "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",
        "enemy_l": "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"
    }

    IMG_FALLBACK_PATHS = {
        "enemy_r": os.path.join(BASE_DIR, r"images/fallback_enemyr.png"),
        "enemy_l": os.path.join(BASE_DIR, r"images/fallback_enemyl.png")
    }

    def __init__(self):
        pygame.init()
        mixer.init()

        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(filename)s: %(lineno)d [%(funcName)s] | %(message)s',
            filename="game.log"
        )

        self.logger = logging.getLogger(__name__)

        self._check_fallbacks()

        self.mixer = mixer

        self.cheated = False

        self.info = pygame.display.Info()

        game_icon = pygame.image.load(os.path.join(BASE_DIR, r"images/game_icon.png"))

        pygame.display.set_icon(game_icon)
        self.screen = pygame.display.set_mode((800, 800), pygame.RESIZABLE)

        pygame.display.set_caption("Öz Hakiki GTA 7")
        self.clock = pygame.time.Clock()

        self.GAME_VERSION = VERSION

        self.save_manager = SaveManager(os.path.join(BASE_DIR, "saves"))

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

        # Oyunun heyecanını katan manager!
        self.juice = JuiceManager()
        self.render_surf = pygame.Surface((self.width, self.height))

        if self.settings.get("music"):
            self.mixer.music.set_volume(self.settings.get("music_volume"))

        else:
            self.mixer.music.set_volume(0.0)

        self.mixer.music.load(
            os.path.join(
                BASE_DIR,
                r"musics/menu_theme.ogg"
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

        # Görselleri convert et
        if pygame.display.get_surface() is not None:

            for enemy in self.game_data.enemy_data.values():
                enemy.image_l = enemy.image_l.convert_alpha()
                enemy.image_r = enemy.image_r.convert_alpha()
                enemy.arrow_image = enemy.arrow_image.convert_alpha()
                if type(enemy) == classes.Boss:
                    enemy.full_image = enemy.full_image.convert_alpha()

            for enemy_list in levels:
                for enemy in enemy_list:
                    enemy.image_l = enemy.image_l.convert_alpha()
                    enemy.image_r = enemy.image_r.convert_alpha()
                    enemy.arrow_image = enemy.arrow_image.convert_alpha()
                    if type(enemy) == classes.Boss:
                        enemy.full_image = enemy.full_image.convert_alpha()

            self.game_data.player.image = self.game_data.player.image.convert_alpha()
            self.game_data.player.anim.convert_alpha()

            self.game_data.world.terrain_image = self.game_data.world.terrain_image.convert_alpha()
            self.game_data.world.dirt_image = self.game_data.world.dirt_image.convert_alpha()

        else:
            self.logger.warning("Images can not convert. (Screen is not set)")

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
        # init içinde yapılamayan fonksiyon verme
        self.settings.options["credits"]["callback"] = (
            lambda: self.screen_manager.set_screen(ScreenType.CREDITS)
        )
        self.settings.create_elements()

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

    def _check_fallbacks(self):
        self.logger.info("Checking if fallback images deleted.")

        for key, value in Game.IMG_FALLBACK_PATHS.items():
            if not os.path.exists(value):
                self.logger.warning(f"{value} fallback image not found. Recovering image by base64.")

                try:
                    fallback_bytes = base64.b64decode(Game.IMG_FALLBACKS[key])
                    with open(value, "wb") as f:
                        f.write(fallback_bytes)

                except Exception as e:
                    self.logger.error(f"Fallback recover caused error: {e}")

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
                        cooldown_bagimsiz_summons=classes.Cooldown(0.3),
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

    def reset(self):
        game_data_defaults = constant_defaults

        self.game_data = self.game_data.to_gamedata(game_data_defaults)


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

        if self.played and self.screen_manager.get_screen(ScreenType.GAME).mode == "campaign":
            self.save_manager.save_last_slot(self.game_data, self.cheated)

        if self.const_game_data is not None:
            with open(Game.GAME_FILE, "w", encoding="utf-8") as f:
                json.dump(
                    self.const_game_data,
                    f,
                    indent=4
                )
