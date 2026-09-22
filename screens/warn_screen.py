from .screen import Screen
import pygame
import colours
from fonts import font1, font2, font3, dfont1, dfont2
import classes
from calcs import calculate_size
from .types import ScreenType
from lang_support import Lang

pygame.init()

class WarnScreen(Screen):
    def __init__(self, game):
        super().__init__(game)

        self.langs = {
            "continue": Lang(türkçe="Devam Et", english="Continue"),
            "return_button": Lang(türkçe="Geri Dön", english="Return Back"),
            "warn_text": Lang(
                türkçe="Yüklemekte bulunduğunuz kayıt ile\nşuanki oyunun sürümü aynı DEĞİL!\nOyun hata verebilir, devam etmek istiyor musunuz?",
                english="The slot that you are trying to load's\nversion and the game's version is NOT SAME!\nThe game could crash, do you want to continue?"
            ),
            "warning": Lang(türkçe="Uyarı!", english="Warning!")
        }

        self.warn_continue_button = classes.Button(
            0, 0, 200, 55,
            "Devam Et",
            font3,
            colours.lighter(colours.BLACK, 30),
            colours.WHITE,
            [ScreenType.WARN],
            border_radius=20,
            plus_data=False
        )

        self.warn_return_button = classes.Button(
            0, 0, 200, 55,
            "Geri Dön",
            font3,
            colours.lighter(colours.BLACK, 30),
            colours.WHITE,
            [ScreenType.WARN],
            border_radius=20,
            plus_data=False
        )

    def draw(self, surface: pygame.Surface):
        surface.fill(colours.BLACK)

        warn_rect = pygame.Rect(
            self.game.width / 2,
            self.game.height / 2,
            self.game.width * 0.5,
            self.game.height * 0.3
        )
        warn_rect.center = (
            self.game.width / 2,
            self.game.height / 2
        )

        warn_surface_header = pygame.Surface(
            (self.game.width * 0.3,
            self.game.height * 0.1)
        )

        warn_surface = pygame.Surface(
            (
                self.game.width * 0.5,
                self.game.height * 0.2
            )
        )

        pygame.draw.rect(
            surface,
            colours.lighter(colours.BLACK, 30),
            warn_rect,
            border_radius=20
        )

        warn_header_render, _ = dfont1.render(self.langs["warning"].get(self.game.settings.get("language")), colours.WHITE, warn_surface_header, 40)

        surface.blit(warn_header_render,(self.game.width / 2 - warn_header_render.get_width() / 2, self.game.height / 2 - warn_header_render.get_height() * 2))

        # font1.draw_text("UYARI!", (self.game.width / 2, self.game.height / 2 - 120), surface, colours.WHITE, hiza="center")

        messages, line_height = dfont2.render(
            self.langs["warn_text"].get(self.game.settings.get("language")),
            colours.WHITE,
            warn_surface,
            40,
            True
        )

        #font2.draw_text(
        #    "Yüklemekte bulunduğunuz kayıt ile",
        #    (self.game.width / 2, self.game.height / 2),
        #    surface,
        #    colours.WHITE,
        #    "center"
        #)
        #font2.draw_text(
        #    "şuanki oyunun sürümü aynı DEĞİL!",
        #    (self.game.width / 2, self.game.height / 2 + font2.font.get_height() + 20),
        #    surface,
        #    colours.WHITE,
        #    "center"
        #)

        for i, message in enumerate(messages):
            surface.blit(
                message,
                (
                    self.game.width / 2 - message.get_width() / 2,
                    self.game.height / 2 + i * line_height
                )
            )

        self.warn_continue_button.draw(surface)
        self.warn_return_button.draw(surface)

    def update(self, dt):
        width = self.game.width
        height = self.game.height

        self.warn_continue_button.set_center(width * 0.3, height * 0.7)
        self.warn_continue_button.width = calculate_size(200, 800, width)
        self.warn_continue_button.height = calculate_size(55, 800, height)
        self.warn_return_button.set_center(width * 0.7, height * 0.7)
        self.warn_return_button.width = calculate_size(200, 800, width)
        self.warn_return_button.height = calculate_size(55, 800, height)

    def handle_event(self, event: pygame.event.Event):
        if self.warn_continue_button.clicked(event, ScreenType.WARN):
            self.game.screen_manager.set_screen(ScreenType.LOAD, accepted_continue=True, slot_id=self.slot_id, warning=True)

        if self.warn_return_button.clicked(event, ScreenType.WARN):
            self.game.screen_manager.set_screen(ScreenType.LOAD, accepted_continue=False, slot_id=self.slot_id, warning=True)

    def on_enter(self, transfer_datas: dict):
        self.slot_id = transfer_datas["slot_id"]

    def on_exit(self):
        del self.slot_id
