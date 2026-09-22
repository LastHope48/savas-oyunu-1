from .menu_screen import MenuScreen
import pygame
from classes import defaults as game_data_defaults
from classes import Button
import classes
from fonts import font1, font2, font3, font4
import colours
from calcs import calculate_size
from screens.types import ScreenType
from gamedata import GameData
from lang_support import Lang

class MainMenuScreen(MenuScreen):
    def __init__(self, game):
        super().__init__(game)

        self.langs = {
            "new_game_button": Lang(türkçe="Yeni Oyun", english="New Game"),
            "continue_button": Lang(türkçe="Devam Et", english="Continue"),
            "load_button": Lang(türkçe="Yükle", english="Load"),
            "save_button": Lang(türkçe="Kaydet", english="Save"),
            "settings_button": Lang(türkçe="Ayarlar", english="Settings"),
            "quit_button": Lang(türkçe="Çık", english="Quit"),
            "date_info": Lang(türkçe="Tarih", english="Date"),
            "version_info": Lang(türkçe="Sürüm", english="Version")
        }

        self.new_game_button = Button(
            0, 0, 300, 80,
            "Yeni Oyun",
            font1,
            colours.YELLOW,
            colours.WHITE,
            [ScreenType.MENU],
            colours.darker(colours.YELLOW, 20),
            colours.darker(colours.YELLOW, 50)
        )

        self.continue_button = Button(
            0, 0, 300, 80,
            "Devam Et",
            font1,
            colours.YELLOW,
            colours.WHITE,
            [ScreenType.MENU],
            colours.darker(colours.YELLOW, 20),
            colours.darker(colours.YELLOW, 50)
        )

        self.load_button = Button(
            0, 0, 300, 80,
            "Yükle",
            font1,
            colours.YELLOW,
            colours.WHITE,
            [ScreenType.MENU],
            colours.darker(colours.YELLOW, 20),
            colours.darker(colours.YELLOW, 50)
        )

        self.save_button = Button(
            0, 0, 300, 80,
            "Kaydet",
            font1,
            colours.YELLOW,
            colours.WHITE,
            [ScreenType.MENU],
            colours.darker(colours.YELLOW, 20),
            colours.darker(colours.YELLOW, 50)
        )

        self.settings_button = Button(
            0, 0, 300, 80,
            "Ayarlar",
            font1,
            colours.YELLOW,
            colours.WHITE,
            [ScreenType.MENU],
            colours.darker(colours.YELLOW, 20),
            colours.darker(colours.YELLOW, 50)
        )

        self.quit_button = Button(
            0, 0, 300, 80,
            "Çık",
            font1,
            colours.RED,
            colours.WHITE,
            [ScreenType.MENU],
            colours.darker(colours.RED, 20),
            colours.darker(colours.RED, 50)
        )

        self.last = self.game.save_manager.get_info_last_slot()

        self.info_button = Button(
            0, 0, 80, 80,
            "i",
            font2,
            colours.BLUE,
            colours.WHITE,
            [ScreenType.MENU],
            plus_data=False
        )

        self.info_rect = classes.AlignedRect(
            0, 0, 200, 200,
            font4,
            colours.WHITE,
            f"Tarih: {self.last['date'] if self.last else ''}\nSürüm: {self.last['version'] if self.last else ''}",
            colours.BLACK,
            plus_data=False
        )

    def draw(self, surface: pygame.Surface):
        surface.fill(colours.BLACK)
        _bolum = calculate_size(50, 800, self.game.width)
        _font = classes.userFont("arial", int(_bolum))
        _font.draw_text("SAVAŞ OYUNU", (self.game.width//2, int(self.game.height*0.11)), surface, colours.WHITE, "center")
        self.new_game_button.draw(surface)
        self.continue_button.draw(surface)
        self.load_button.draw(surface)
        self.save_button.draw(surface)
        self.settings_button.draw(surface)
        self.quit_button.draw(surface)
        if self.last:
            if self.info_rect.plus_data:
                self.info_button.draw(surface)
                if self.info_button.plus_data:
                    self.info_rect.draw(surface)

    def update(self, dt):
        width = self.game.width
        height = self.game.height

        self.new_game_button.set_center(width * 0.5, height * 0.27)
        self.new_game_button.width = calculate_size(300, 800, width) # bu butonların genişliği 300 yüksekliği 800
        self.new_game_button.height = calculate_size(80, 800, height)
        self.new_game_button.text = self.langs['new_game_button'].get(self.game.settings.get('language'))

        self.continue_button.set_center(width * 0.5, height * 0.4)
        self.continue_button.width = calculate_size(300, 800, width)
        self.continue_button.height = calculate_size(80, 800, height)
        self.continue_button.text = self.langs['continue_button'].get(self.game.settings.get('language'))

        self.load_button.set_center(width * 0.5, height * 0.53)
        self.load_button.width = calculate_size(300, 800, width)
        self.load_button.height = calculate_size(80, 800, height)
        self.load_button.text = self.langs['load_button'].get(self.game.settings.get('language'))

        self.save_button.set_center(width * 0.5, height * 0.66)
        self.save_button.width = calculate_size(300, 800, width)
        self.save_button.height = calculate_size(80, 800, height)
        self.save_button.text = self.langs['save_button'].get(self.game.settings.get('language'))

        self.settings_button.set_center(width * 0.5, height * 0.79)
        self.settings_button.width = calculate_size(300, 800, width)
        self.settings_button.height = calculate_size(80, 800, height)
        self.settings_button.text = self.langs['settings_button'].get(self.game.settings.get('language'))

        self.quit_button.set_center(width * 0.5, height * 0.92)
        self.quit_button.width = calculate_size(300, 800, width)
        self.quit_button.height = calculate_size(80, 800, height)
        self.quit_button.text = self.langs['quit_button'].get(self.game.settings.get('language'))

        if self.last:
            self.info_button.set_center(self.continue_button.rect.center[0] + self.continue_button.width / 2 + 50, height * 0.53)
            self.info_rect.set_center(self.continue_button.rect.center[0] + self.continue_button.width / 2 + 300, height * 0.53)
            self.info_rect.width = calculate_size(200, 800, self.game.width)
            self.info_rect.height = calculate_size(200, 800, self.game.height)
            self.info_rect.text = f"{self.langs['date_info'].get(self.game.settings.get('language'))}: {self.last['date']}\n{self.langs['version_info'].get(self.game.settings.get('language'))}: {self.last['version']}"

        for button in classes.Button.buttons:
            button: Button
            button.on_mouse()

        self.last = self.game.save_manager.get_info_last_slot(log=False)

    def handle_event(self, event: pygame.event.Event):
        if self.new_game_button.clicked(event, ScreenType.MENU):
            self.game.game_data = GameData.to_gamedata(game_data_defaults)
            game_screen = self.game.screen_manager.get_screen(ScreenType.GAME)
            game_screen.start_new_game()
            self.game.screen_manager.set_screen(ScreenType.GAME)
            return

        if self.continue_button.clicked(event, ScreenType.MENU):
            continue_data = self.game.save_manager.last_slot()

            if continue_data is not None:
                self.game.game_data = continue_data
                self.game.screen_manager.set_screen(ScreenType.GAME)
                return

        if self.save_button.clicked(event, ScreenType.MENU):
            self.game.screen_manager.set_screen(ScreenType.SAVE, screen_type_before=ScreenType.MENU)

        if self.load_button.clicked(event, ScreenType.MENU):
            self.game.screen_manager.set_screen(ScreenType.LOAD, screen_type_before=ScreenType.MENU)

        if self.settings_button.clicked(event, ScreenType.MENU):
            self.game.screen_manager.set_screen(ScreenType.SETTINGS)

        if self.quit_button.clicked(event, ScreenType.MENU):
            self.game.running = False
            return

        if event.type == pygame.WINDOWMAXIMIZED:
            if self.last:
                self.info_rect.plus_data = True

        if event.type == pygame.WINDOWRESTORED:
            if self.last:
                self.info_rect.plus_data = False

        if self.info_button.clicked(event, ScreenType.MENU) and self.info_rect.plus_data:
            self.info_button.plus_data = not self.info_button.plus_data
