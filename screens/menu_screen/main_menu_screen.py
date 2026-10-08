from .menu_screen import MenuScreen
import pygame
from classes import defaults as game_data_defaults
from classes import Button
import classes
from fonts import get_font
import colours
from calcs import calculate_size
from screens.types import ScreenType
from gamedata import GameData
from lang_support import Lang
import os
from basedir import BASE_DIR

class MainMenuScreen(MenuScreen):
    def __init__(self, game):
        super().__init__(game)

        self.langs = {
            "new_game_button": Lang(türkçe="Yeni Oyun", english="New Game", arabic="لعبة جديدة", sanskrit="नूतनः क्रीडा"),
            "continue_button": Lang(türkçe="Devam Et", english="Continue", arabic="يكمل", sanskrit="अनुवर्तते"),
            "world_select_button": Lang(türkçe="Dünya Seç", english="World Select", sanskrit="जगत् चयन करें", arabic="اختر العالم"),
            "load_button": Lang(türkçe="Yükle", english="Load", sanskrit="अपलोड् कुर्वन्तु", arabic="رفع"),
            "achivements_button": Lang(türkçe="Başarılar", english="Achivements", arabic="حظ سعيد", sanskrit="शुभकामना"),
            "settings_button": Lang(türkçe="Ayarlar", english="Settings", sanskrit="सेटिंग्स्", arabic="إعدادات"),
            "quit_button": Lang(türkçe="Çık", english="Quit", arabic="مخرج", sanskrit="निर्गम"),
        }

        self.font1 = get_font(
            self.game.fonts,
            Lang.USING_LANG,
            1,
            "userFont"
        )

        self.font2 = get_font(
            self.game.fonts,
            Lang.USING_LANG,
            2,
            "userFont"
        )

        self.font4 = get_font(
            self.game.fonts,
            Lang.USING_LANG,
            4,
            "userFont"
        )

        button_number = 6 + (1 if self.game.const_game_data["worlds_accessable"] else 0)

        self.button_height = 800 // (button_number // 0.6)

        self.new_game_button = Button(
            0, 0, 300, self.button_height,
            "Yeni Oyun",
            self.font1,
            colours.YELLOW,
            colours.WHITE,
            [ScreenType.MENU],
            colours.darker(colours.YELLOW, 20),
            colours.darker(colours.YELLOW, 50),
            design="bevel",
            border_radius=0
        )

        self.continue_button = Button(
            0, 0, 300, 80,
            "Devam Et",
            self.font1,
            colours.YELLOW,
            colours.WHITE,
            [ScreenType.MENU],
            colours.darker(colours.YELLOW, 20),
            colours.darker(colours.YELLOW, 50),
            design="bevel",
            border_radius=0
        )

        self.worlds_button = Button(
            0, 0, 300, 80,
            "Dünya Seç",
            self.font1,
            colours.LIGHT_BLUE,
            colours.WHITE,
            [ScreenType.MENU],
            design="bevel",
            border_radius=0
        )

        self.load_button = Button(
            0, 0, 300, 80,
            "Yükle",
            self.font1,
            colours.YELLOW,
            colours.WHITE,
            [ScreenType.MENU],
            colours.darker(colours.YELLOW, 20),
            colours.darker(colours.YELLOW, 50),
            design="bevel",
            border_radius=0
        )

        self.achivements_button = Button(
            0, 0, 300, 80,
            "Başarılar",
            self.font1,
            colours.YELLOW,
            colours.WHITE,
            [ScreenType.MENU],
            colours.darker(colours.YELLOW, 20),
            colours.darker(colours.YELLOW, 50),
            design="bevel",
            border_radius=0
        )

        self.settings_button = Button(
            0, 0, 300, 80,
            "Ayarlar",
            self.font1,
            colours.YELLOW,
            colours.WHITE,
            [ScreenType.MENU],
            colours.darker(colours.YELLOW, 20),
            colours.darker(colours.YELLOW, 50),
            design="bevel",
            border_radius=0
        )

        self.quit_button = Button(
            0, 0, 300, 80,
            "Çık",
            self.font1,
            colours.RED,
            colours.WHITE,
            [ScreenType.MENU],
            colours.darker(colours.RED, 20),
            colours.darker(colours.RED, 50),
            design="bevel",
            border_radius=0
        )

        self.last = self.game.save_manager.get_info_last_slot()

        self.title_font = None
        self.title_font_size = None

    def draw(self, surface: pygame.Surface):
        surface.fill(colours.BLACK)
        _bolum = calculate_size(50, 800, self.game.width)

        if self.title_font is None or self.title_font_size != int(_bolum):
            self.title_font_size = int(_bolum)

            if Lang.USING_LANG.lower() == "türkçe" or Lang.USING_LANG.lower() == "english":
                clarity_city = os.path.join(BASE_DIR, r"fonts/Clarity-city.ttf")
                self.title_font = classes.userFont(clarity_city, self.title_font_size)

            elif Lang.USING_LANG.lower() == "arabic":
                self.title_font = classes.userFont(
                    os.path.join(BASE_DIR, r"fonts/arabica.ttf"),
                    self.title_font_size
                )

            elif Lang.USING_LANG.lower() == "sanskrit":
                self.title_font = classes.userFont(
                    os.path.join(BASE_DIR, r"fonts/arabica.ttf"),
                    self.title_font_size
                )
        if self.title_font is not None:
            self.title_font.draw_text(
                "SAVAŞ OYUNU",
                (self.game.width // 2, int(self.game.height * 0.11)),
                surface,
                colours.WHITE,
                "center"
            )

        self.new_game_button.draw(surface)
        self.continue_button.draw(surface)

        if self.game.const_game_data["worlds_accessable"]:
            self.worlds_button.draw(surface)

        self.load_button.draw(surface)
        self.achivements_button.draw(surface)
        self.settings_button.draw(surface)
        self.quit_button.draw(surface)

    def update(self, dt):
        width = self.game.width
        height = self.game.height

        btn_w = calculate_size(300, 800, width)
        btn_h = calculate_size(self.button_height, 800, height)
        gap = calculate_size(50, 2160, height)
        step = btn_h + gap

        # Quit butonunun ekranın alt kenarından bırakacağı boşluk (px):
        bottom_padding = 40  
        quit_y = height - bottom_padding - (btn_h / 2)

        step_counter = 0

        # 7. Quit (En altta, tabandan biraz yüksekte)
        self.quit_button.set_center(width * 0.5, quit_y - step * step_counter)
        self.quit_button.width = btn_w
        self.quit_button.height = btn_h

        step_counter += 1

        # 6. Settings
        self.settings_button.set_center(width * 0.5, quit_y - step * step_counter)
        self.settings_button.width = btn_w
        self.settings_button.height = btn_h
        self.settings_button.text = self.langs['settings_button'].get(self.game.settings.get('language'))

        step_counter += 1

        # 5. Achievements
        self.achivements_button.set_center(width * 0.5, quit_y - step * step_counter)
        self.achivements_button.width = btn_w
        self.achivements_button.height = btn_h
        self.achivements_button.text = self.langs['achivements_button'].get(self.game.settings.get('language'))

        step_counter += 1

        # 4. Load
        self.load_button.set_center(width * 0.5, quit_y - step * step_counter)
        self.load_button.width = btn_w
        self.load_button.height = btn_h
        self.load_button.text = self.langs['load_button'].get(self.game.settings.get('language'))

        # 3. World Select
        if self.game.const_game_data["worlds_accessable"]:
            step_counter += 1
            self.worlds_button.set_center(width * 0.5, quit_y - step * step_counter)
            self.worlds_button.width = btn_w
            self.worlds_button.height = btn_h
            self.worlds_button.text = self.langs["world_select_button"]()

        step_counter += 1

        # 2. Continue
        self.continue_button.set_center(width * 0.5, quit_y - step * step_counter)
        self.continue_button.width = btn_w
        self.continue_button.height = btn_h
        self.continue_button.text = self.langs['continue_button'].get(self.game.settings.get('language'))

        step_counter += 1

        # 1. New Game (En üstte)
        self.new_game_button.set_center(width * 0.5, quit_y - step * step_counter)
        self.new_game_button.width = btn_w
        self.new_game_button.height = btn_h
        self.new_game_button.text = self.langs['new_game_button'].get(self.game.settings.get('language'))

        self.new_game_button.on_mouse()
        self.continue_button.on_mouse()
        self.worlds_button.on_mouse()
        self.achivements_button.on_mouse()
        self.load_button.on_mouse()
        self.settings_button.on_mouse()
        self.quit_button.on_mouse()


    def handle_event(self, event: pygame.event.Event):
        if self.new_game_button.clicked(event, ScreenType.MENU):
            self.game.dump("new_game", True)

            if self.game.settings.get("sfx"):
                self.game.sfx_manager.play("click", self.game.settings.get("sfx_volume"))

            self.game.game_data = GameData.to_gamedata(game_data_defaults)
            game_screen = self.game.screen_manager.get_screen(ScreenType.GAME)

            game_screen.start_new_game()
            self.game.screen_manager.set_screen(ScreenType.GAME)
            return

        if self.continue_button.clicked(event, ScreenType.MENU):

            if self.game.settings.get("sfx"):
                self.game.sfx_manager.play("click", self.game.settings.get("sfx_volume"))

            data = self.game.save_manager.last_slot()

            if data is not None:
                continue_data, cheated = data

                self.game.game_data = continue_data
                self.game.cheated = cheated
                self.game.screen_manager.set_screen(ScreenType.GAME)
                return

        if self.game.const_game_data["worlds_accessable"]:
            if self.worlds_button.clicked(event, ScreenType.MENU):

                if self.game.settings.get("sfx"):
                    self.game.sfx_manager.play("click", self.game.settings.get("sfx_volume"))

                self.game.screen_manager.set_screen(ScreenType.WORLD_SELECT)

        if self.achivements_button.clicked(event, ScreenType.MENU):

            if self.game.settings.get("sfx"):
                self.game.sfx_manager.play("click", self.game.settings.get("sfx_volume"))

            self.game.screen_manager.set_screen(ScreenType.ACHIEVEMENTS, screen_type_before=ScreenType.MENU)

        if self.load_button.clicked(event, ScreenType.MENU):

            if self.game.settings.get("sfx"):
                self.game.sfx_manager.play("click", self.game.settings.get("sfx_volume"))

            self.game.screen_manager.set_screen(ScreenType.LOAD, screen_type_before=ScreenType.MENU)

        if self.settings_button.clicked(event, ScreenType.MENU):

            if self.game.settings.get("sfx"):
                self.game.sfx_manager.play("click", self.game.settings.get("sfx_volume"))

            self.game.screen_manager.set_screen(ScreenType.SETTINGS)

        if self.quit_button.clicked(event, ScreenType.MENU):

            if self.game.settings.get("sfx"):
                self.game.sfx_manager.play("click", self.game.settings.get("sfx_volume"))

            self.game.running = False
            return

    def on_enter(self, transfer_datas):
        button_number = 6 + 1 if self.game.const_game_data["worlds_accessable"] else 0

        self.button_height = 800 // (button_number // 0.6)

        self.font1 = get_font(
            self.game.fonts,
            Lang.USING_LANG,
            1,
            "userFont"
        )

        self.font2 = get_font(
            self.game.fonts,
            Lang.USING_LANG,
            2,
            "userFont"
        )

        self.font4 = get_font(
            self.game.fonts,
            Lang.USING_LANG,
            4,
            "userFont"
        )

        self.new_game_button = Button(
            0, 0, 300, 80,
            "Yeni Oyun",
            self.font1,
            colours.YELLOW,
            colours.WHITE,
            [ScreenType.MENU],
            colours.darker(colours.YELLOW, 20),
            colours.darker(colours.YELLOW, 50),
            design="bevel",
            border_radius=0
        )

        self.continue_button = Button(
            0, 0, 300, 80,
            "Devam Et",
            self.font1,
            colours.YELLOW,
            colours.WHITE,
            [ScreenType.MENU],
            colours.darker(colours.YELLOW, 20),
            colours.darker(colours.YELLOW, 50),
            design="bevel",
            border_radius=0
        )

        self.worlds_button = Button(
            0, 0, 300, 80,
            "Dünya Seç",
            self.font1,
            colours.LIGHT_BLUE,
            colours.WHITE,
            [ScreenType.MENU],
            design="bevel",
            border_radius=0
        )

        self.load_button = Button(
            0, 0, 300, 80,
            "Yükle",
            self.font1,
            colours.YELLOW,
            colours.WHITE,
            [ScreenType.MENU],
            colours.darker(colours.YELLOW, 20),
            colours.darker(colours.YELLOW, 50),
            design="bevel",
            border_radius=0
        )

        self.achivements_button = Button(
            0, 0, 300, 80,
            "Başarılar",
            self.font1,
            colours.YELLOW,
            colours.WHITE,
            [ScreenType.MENU],
            colours.darker(colours.YELLOW, 20),
            colours.darker(colours.YELLOW, 50),
            design="bevel",
            border_radius=0
        )

        self.settings_button = Button(
            0, 0, 300, 80,
            "Ayarlar",
            self.font1,
            colours.YELLOW,
            colours.WHITE,
            [ScreenType.MENU],
            colours.darker(colours.YELLOW, 20),
            colours.darker(colours.YELLOW, 50),
            design="bevel",
            border_radius=0
        )

        self.quit_button = Button(
            0, 0, 300, 80,
            "Çık",
            self.font1,
            colours.RED,
            colours.WHITE,
            [ScreenType.MENU],
            colours.darker(colours.RED, 20),
            colours.darker(colours.RED, 50),
            design="bevel",
            border_radius=0
        )

        self.title_font = None

        if self.game.dump("last_music") != os.path.join(BASE_DIR, r"musics/menu_theme.mp3"):
            self.game.mixer.music.load(
                os.path.join(
                    BASE_DIR,
                    r"musics/menu_theme.mp3"
                )
            )

            self.game.mixer.music.play(-1)

    def on_exit(self):

        self.game.dump(
            "last_music",
            os.path.join(
                    BASE_DIR,
                    r"musics/menu_theme.mp3"
            )
        )
