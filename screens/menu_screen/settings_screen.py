from .menu_screen import MenuScreen
import pygame
from fonts import font2, font3
from console import Console
import os
from basedir import BASE_DIR
from classes import Button
from lang_support import Lang
import colours
from screens.types import ScreenType
from update_manager import check_for_update, prepare_update
import threading


class SettingsScreen(MenuScreen):
    def __init__(self, game):
        super().__init__(game)

        self.langs = {
            "update_button_text": Lang(türkçe="Güncellemeleri Kontrol Et", english="Check Updates")
        }

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

        self.update_button = Button(
            700,
            750,
            300,
            50,
            "Güncellemeleri Kontrol Et",
            font3,
            colours.YELLOW,
            colours.WHITE,
            [ScreenType.SETTINGS]
        )

        self.update_status = ""
        self.update_progress = 0

        self.update_thread = None
        self.update_running = False

    def draw(self, surface: pygame.Surface):
        surface.fill('black')

        self.game.settings.draw(surface, font2)

        surface.blit(self.quit_icon, (0, 0))


        self.update_button.draw(
            surface
        )

        if self.update_status:
            status_text = font3.return_text(
                self.update_status,
                (255, 255, 255)
            )

            surface.blit(
                status_text,
                (
                    self.update_button.rect.left,
                    self.update_button.rect.bottom + 15
                )
            )

        if self.update_running:

            bar_width = 500
            bar_height = 25

            bar_x = self.update_button.rect.left
            bar_y = (
                self.update_button.rect.bottom
                + 55
            )

            # Arka plan
            pygame.draw.rect(
                surface,
                (60, 60, 60),
                (
                    bar_x,
                    bar_y,
                    bar_width,
                    bar_height
                ),
                border_radius=5
            )

            # İlerleme
            progress_width = int(
                bar_width
                * self.update_progress
                / 100
            )

            if progress_width > 0:

                pygame.draw.rect(
                    surface,
                    (70, 180, 100),
                    (
                        bar_x,
                        bar_y,
                        progress_width,
                        bar_height
                    ),
                    border_radius=5
                )

            # Yüzde
            percentage_text = font3.return_text(
                f"%{self.update_progress:.1f}",
                (255, 255, 255)
            )

            percentage_rect = (
                percentage_text.get_rect(
                    center=(
                        bar_x + bar_width // 2,
                        bar_y + bar_height // 2
                    )
                )
            )

            surface.blit(
                percentage_text,
                percentage_rect
            )

        self.console.draw(surface, self.game.height)

    def update(self, dt):

        if self.old_fullscreen != self.game.settings.get("fullscreen"):
            self.game.screen = pygame.display.set_mode(
                (self.game.width, self.game.height),
                pygame.FULLSCREEN if self.game.settings.get("fullscreen") else pygame.RESIZABLE
            )

        self.old_fullscreen = self.game.settings.get("fullscreen")
        self.update_button.text = self.langs["update_button_text"].get(self.game.settings.get("language"))

        if self.game.settings.get("music"):
            other_music = self.game.settings.get_element("other_music")

            if os.path.exists(self.game.settings.get("other_music")):

                other_music.showing_icons = [
                    other_music.icons.get("path_found")
                ]

            else:
                other_music.showing_icons = [
                    other_music.icons.get("path_not_found")
                ]


    def handle_event(self, event: pygame.event.Event):

        self.game.settings.handle_event(event)

        if event.type == pygame.MOUSEBUTTONDOWN:

            if event.button == 1:

                if self.quit_icon_rect.collidepoint(
                    event.pos
                ):

                    self.game.screen_manager.set_screen(
                        self.game.screen_manager.get_last_screen()
                    )

                elif self.update_button.rect.collidepoint(
                    event.pos
                ):

                    self.check_update()

        self.console.handle_event(event)


    def check_update(self):

        if self.update_running:
            return

        self.update_running = True
        self.update_progress = 0
        self.update_status = "Güncellemeler kontrol ediliyor..."

        self.update_thread = threading.Thread(
            target=self.update_worker,
            daemon=True
        )

        self.update_thread.start()

    def update_worker(self):

        try:

            update = check_for_update()

            if update is None:

                self.update_status = (
                    "Oyun zaten güncel."
                )

                self.update_running = False
                return

            self.update_status = (
                f"Yeni sürüm bulundu: "
                f"{update['version']}"
            )

            prepare_update(
                update["url"],
                update["signature_url"],
                self.update_progress_callback
            )

            self.update_progress = 100

            self.update_status = (
                "Güncelleme hazır. "
                "Oyun kapatıldığında uygulanacak."
            )

        except Exception as e:


            self.update_status = (
                f"Güncelleme başarısız: {e}"
            )
            print("GÜNCELLEME HATASI:", repr(e))

        finally:

            self.update_running = False

    def update_progress_callback(self, progress):

        self.update_progress = progress

    def on_enter(self, transfer_datas: dict):
        self.game.mixer.music.load(os.path.join(BASE_DIR,r"musics/settings_theme.mp3"))

        self.game.mixer.music.play(-1)

    def on_exit(self):
        self.game.mixer.music.stop()

        self.game.dump("last_music", os.path.join(BASE_DIR,r"musics/settings_theme.mp3"))

        self.game.settings.save()
