from .menu_screen import MenuScreen
import pygame
from fonts import font2, font3
from console import Console
import os
from basedir import BASE_DIR

class SettingsScreen(MenuScreen):
    def __init__(self, game):
        super().__init__(game)

        self.console = Console(
            self.game.command_parser,
            font3,
            font3
        )

        self.quit_icon = pygame.image.load(os.path.join(BASE_DIR,r"images/quit_icon.png")).convert_alpha()
        self.quit_icon = pygame.transform.scale(
            self.quit_icon,
            (
                self.game.info.current_w // 30,
                self.game.info.current_w // 30
            )
        )

        self.quit_icon_rect = self.quit_icon.get_rect()
        self.old_fullscreen = self.game.settings.get("fullscreen")

    def draw(self, surface: pygame.Surface):
        surface.fill('black')

        self.game.settings.draw(surface, font2)

        surface.blit(self.quit_icon, (0, 0))

        self.console.draw(surface, self.game.height)

    def update(self, dt):

        if self.old_fullscreen != self.game.settings.get("fullscreen"):
            self.game.screen = pygame.display.set_mode(
                (self.game.width, self.game.height),
                pygame.FULLSCREEN if self.game.settings.get("fullscreen") else pygame.RESIZABLE
            )

        self.old_fullscreen = self.game.settings.get("fullscreen")


    def handle_event(self, event: pygame.event.Event):
        self.game.settings.handle_event(event)

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.quit_icon_rect.collidepoint(event.pos):
                    self.game.screen_manager.set_screen(self.game.screen_manager.get_last_screen())

        self.console.handle_event(event)

    def on_enter(self, transfer_datas: dict):
        self.game.mixer.music.load(os.path.join(BASE_DIR,r"musics/settings_theme.mp3"))
        self.game.mixer.music.play(-1)

    def on_exit(self):
        self.game.mixer.music.stop()

        self.game.settings.save()
