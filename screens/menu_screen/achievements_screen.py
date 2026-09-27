import pygame
from .menu_screen import MenuScreen
import colours
from dfont import DynamicFont
import os
from basedir import BASE_DIR
from ui import Bar, BarElement
from lang_support import Lang
from screens.types import ScreenType
import threading


class AchievementsScreen(MenuScreen):
    def __init__(self, game):
        super().__init__(game)

        self.verifying = False
        self.offline = False
        self.illegal = False
        self.loading_time = 0
        self.achievements = []

        self.langs = {
            "achievement_counter": Lang(türkçe="Başarı", english="Achievement"),
            "datas_could_not_verified": Lang(türkçe="Achievement verileri doğrulanamadı.", english="Achievement datas could not be verified."),
            "verifying_achievements": Lang(türkçe="Başarımlar Doğrulanıyor", english="Verifying Achievements"),
            "no_internet_connection": Lang(türkçe="İnternet bağlantısı gerekli.", english="No Internet Connection")
        }

        self.achievement_title_font = DynamicFont(
            "arial",
            20,
            60
        )

        self.achievement_description_font = DynamicFont(
            "arial",
            12,
            30
        )

        self.achievements_counter_f = DynamicFont(
            "arial",
            10,
            50
        )

        self.orig_quit_icon = pygame.image.load(os.path.join(BASE_DIR, r"images/quit.png")).convert_alpha()
        self.quit_icon = pygame.transform.scale(self.orig_quit_icon, (self.game.info.current_w // 20, self.game.info.current_w // 20))
        self.old_screen_size = (self.game.width, self.game.height)

        bar_height = self.game.info.current_h // 10

        self.bar = Bar(
            0,
            self.game.screen.get_height() - bar_height,
            self.game.screen.get_width(),
            bar_height,
            colours.GRAY,
            BarElement(
                self.quit_icon,
                on_click=self.quit_button_on_click
            ),
            BarElement(
                pygame.Surface((1, 1)),
                update=self.create_achievement_surface
            ),
            separator=True
        )

        self.offline_bar = Bar(
            0,
            self.game.screen.get_height() - bar_height,
            self.game.screen.get_width(),
            bar_height,
            colours.GRAY,
            BarElement(
                self.quit_icon,
                on_click=self.quit_button_on_click
            ),
            separator=True
        )


        self.bar.update()

    def quit_button_on_click(self):
        self.game.screen_manager.set_screen(ScreenType.MENU)

    def start_verify(self):
        if self.verifying:
            return

        self.verifying = True
        self.offline = False
        self.illegal = False
        self.loading_time = 0

        threading.Thread(
            target=self.verify_achievements,
            daemon=True
        ).start()

    def draw(self, surface: pygame.Surface):
        surface.fill(colours.BLACK)

        if self.verifying:
            self.draw_loading(surface)
            self.offline_bar.draw(surface)
            return

        if self.offline:
            message = self.langs["no_internet_connection"]()

            message_font = DynamicFont(
                "notosans.ttf",
                20,
                50
            )

            message_area = pygame.Surface(
                (
                    surface.get_width() - 100,
                    surface.get_height() - 100
                )
            )

            renders, line_height = message_font.render(
                message,
                "white",
                message_area,
                gap=0,
                breaklines=True
            )

            y = (surface.get_height() - len(renders) * line_height) // 2

            for rendered in renders:
                rect = rendered.get_rect(
                    centerx=surface.get_width() // 2,
                    top=y
                )

                surface.blit(rendered, rect)
                y += line_height

            self.offline_bar.draw(surface)


        elif self.illegal:
            message_font = DynamicFont(
                "arial",
                20,
                50
            )

            message_area = pygame.Surface(
                (
                    surface.get_width() - 100,
                    surface.get_height() - 100
                )
            )

            renders, line_height = message_font.render(
                self.langs["datas_could_not_verified"](),
                "white",
                message_area,
                gap=0,
                breaklines=True
            )

            y = (surface.get_height() - len(renders) * line_height) // 2

            for rendered in renders:
                rect = rendered.get_rect(
                    centerx=surface.get_width() // 2,
                    top=y
                )

                surface.blit(rendered, rect)

                y += line_height

            self.offline_bar.draw(surface)


        else:

            x = 100
            y = 100

            card_width = 300
            card_height = 400
            gap = 30

            for achievement_id in self.achievements:

                rect = pygame.Rect(
                    x,
                    y,
                    card_width,
                    card_height
                )

                self.draw_achievement(
                    surface,
                    achievement_id,
                    rect
                )

                x += card_width + gap

            self.bar.draw(surface)


    def update_achievements(self):
        self.achievements = []

        for achievement_id, achievement in self.game.achievements.achievements.items():

            if not achievement.get("unlocked"):
                continue

            if achievement_id not in self.game.achievements.achievements_metadata:
                continue

            self.achievements.append(achievement_id)

    def draw_achievement(
        self,
        surface: pygame.Surface,
        achievement_id: str,
        rect: pygame.Rect
    ):

        pygame.draw.rect(
            surface,
            "white",
            rect,
            width=2,
            border_radius=10
        )
        
        metadata = self.game.achievements.achievements_metadata[
            achievement_id
        ]

        title = metadata["title"](self.game.settings.get("language"))
        description = metadata["description"](self.game.settings.get("language"))
        image = metadata["image"]

        # Görsel
        image_size = min(
            rect.width // 2,
            rect.height // 3
        )

        image = pygame.transform.smoothscale(
            image,
            (image_size, image_size)
        )

        image_rect = image.get_rect(
            midtop=(
                rect.centerx,
                rect.top + 20
            )
        )

        surface.blit(image, image_rect)

        # Başlık
        title_area = pygame.Surface(
            (
                rect.width - 20,
                60
            )
        )

        title_render, title_height = self.achievement_title_font.render(
            title,
            "white",
            title_area,
            gap=0,
            breaklines=False
        )

        title_rect = title_render.get_rect(
            centerx=rect.centerx,
            top=image_rect.bottom + 15
        )

        surface.blit(
            title_render,
            title_rect
        )

        # Açıklama
        description_area = pygame.Surface(
            (
                rect.width - 30,
                rect.height - (title_rect.bottom - rect.top) - 30
            )
        )

        description_renders, line_height = (
            self.achievement_description_font.render(
                description,
                (180, 180, 180),
                description_area,
                gap=0,
                breaklines=True
            )
        )

        y = title_rect.bottom + 10

        for rendered in description_renders:

            if y + rendered.get_height() > rect.bottom - 10:
                break

            rendered_rect = rendered.get_rect(
                centerx=rect.centerx,
                top=y
            )

            surface.blit(
                rendered,
                rendered_rect
            )

            y += line_height

    def update(self, dt):
        if self.verifying:
            self.loading_time += dt

        self.bar.update()
        self.offline_bar.update()

        bar_height = self.game.screen.get_height() // 10

        self.bar.rect.y = self.game.screen.get_height() - bar_height
        self.bar.rect.height = bar_height
        self.bar.rect.width = self.game.screen.get_width()

        self.offline_bar.rect.y = self.game.screen.get_height() - bar_height
        self.offline_bar.rect.height = bar_height
        self.offline_bar.rect.width = self.game.screen.get_width()

        if (self.game.width, self.game.height) != self.old_screen_size:
            self.quit_icon = pygame.transform.scale(
                self.orig_quit_icon,
                (
                    self.game.width // 12,
                    self.game.width // 12
                )
            )


            self.bar.elements[0].surface = self.quit_icon
            self.offline_bar.elements[0].surface = self.quit_icon

        self.old_screen_size = (self.game.width, self.game.height)


    def handle_event(self, event: pygame.event.Event):
        if self.verifying or self.illegal or self.offline:
            self.offline_bar.handle_event(event)

        else:
            self.bar.handle_event(event)

    def draw_loading(self, surface):
        dots = "." * (int(self.loading_time * 2) % 4)

        message = f"{self.langs['verifying_achievements']()}{dots}"

        font = DynamicFont(
            "notosans.ttf",
            20,
            50
        )

        area = pygame.Surface(
            (
                surface.get_width() - 100,
                surface.get_height() - 100
            )
        )

        renders, line_height = font.render(
            message,
            "white",
            area,
            gap=0,
            breaklines=True
        )

        y = (surface.get_height() - len(renders) * line_height) // 2

        for rendered in renders:
            rect = rendered.get_rect(
                centerx=surface.get_width() // 2,
                top=y
            )

            surface.blit(rendered, rect)

            y += line_height


    def create_achievement_surface(self):
        if self.game.achievements is None: return

        unlocked = len(list(filter(
            lambda x: x["unlocked"],
            self.game.achievements.achievements.values()
        )))

        total = len(self.game.achievements.achievements.keys())

        return self.achievements_counter_f.render(
            f"{self.langs['achievement_counter'](self.game.settings.get('language'))} {unlocked}/{total}",
            colours.BLACK,
            pygame.Surface((self.bar._per_width_for_element(), self.bar.rect.h))
        )[0]

    def verify_achievements(self):
        for achievement_id, achievement in self.game.achievements.achievements.items():

            if not achievement.get("unlocked"):
                continue

            result = self.game.achievements.verify(achievement_id)

            if result is None:
                self.offline = True
                self.verifying = False
                return

            if result is False:
                self.illegal = True
                self.verifying = False
                return

        self.verifying = False

    def on_enter(self, transfer_datas):
        self.achievement_counter = self.create_achievement_surface()

        if self.game.dump("last_music") != os.path.join(BASE_DIR, r"musics/menu_theme.mp3"):
            self.game.mixer.music.load(
                os.path.join(
                    BASE_DIR,
                    r"musics/menu_theme.mp3"
                )
            )

            self.game.mixer.music.play(-1)

        self.illegal = self.game.illegal
        self.offline = self.game.offline

        if self.illegal or self.offline:
            return

        self.start_verify()
        self.update_achievements()
        self.bar.update()
