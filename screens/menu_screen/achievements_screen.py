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
from fonts import get_font


class AchievementsScreen(MenuScreen):
    def __init__(self, game):
        super().__init__(game)

        self.verifying = False
        self.offline = False
        self.illegal = False
        self.loading_time = 0
        self.achievements = []

        self.langs = {
            "achievement_counter": Lang(türkçe="Başarı", english="Achievement", sanskrit="सफलता", arabic="نجاح"),
            "datas_could_not_verified": Lang(türkçe="Achievement verileri doğrulanamadı.", english="Achievement datas could not be verified.", arabic="تعذّر التحقق من بيانات الإنجاز.", sanskrit="उपलब्धिदत्तांशस्य सत्यापनं कर्तुं न शक्यते स्म ।"),
            "verifying_achievements": Lang(türkçe="Başarımlar Doğrulanıyor", english="Verifying Achievements", sanskrit="उपलब्धीनां सत्यापनम्", arabic="يتم التحقق من الإنجازات."),
            "no_internet_connection": Lang(türkçe="İnternet bağlantısı gerekli.", english="No Internet Connection", arabic="يلزم الاتصال بالإنترنت", sanskrit="अन्तर्जालसम्पर्कः आवश्यकः")
        }

        self.achievement_images = {}
        self.achievement_card_cache = {}

        # Achievement title font
        self.font3 = get_font(
            self.game.fonts,
            Lang.USING_LANG,
            3,
            "DynamicFont"
        )

        # Achievement description font

        self.font4 = get_font(
            self.game.fonts,
            Lang.USING_LANG,
            4,
            "DynamicFont"
        )

        # counter_f

        self.font5 = get_font(
            self.game.fonts,
            Lang.USING_LANG,
            5,
            "DynamicFont"
        )
        # message / loading
        
        self.font7 = get_font(
            self.game.fonts,
            Lang.USING_LANG,
            7,
            "DynamicFont"
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
                update=self.create_achievement_surface,
                manual_update=True
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

    def create_achievement_card(
    self,
    achievement_id: str,
    width: int,
    height: int
):
        metadata = self.game.achievements.achievements_metadata[
            achievement_id
        ]

        card = pygame.Surface((width, height), pygame.SRCALPHA)

        # Kart çerçevesi
        pygame.draw.rect(
            card,
            "white",
            card.get_rect(),
            width=2,
            border_radius=10
        )

        # -------------------------
        # Görsel
        # -------------------------

        image_size = min(
            width // 2,
            height // 3
        )

        image = pygame.transform.smoothscale(
            metadata["image"],
            (image_size, image_size)
        )

        image_rect = image.get_rect(
            midtop=(width // 2, 20)
        )

        card.blit(image, image_rect)

        # -------------------------
        # Başlık
        # -------------------------

        title = metadata["title"](
            self.game.settings.get("language")
        )

        title_area = pygame.Surface(
            (width - 20, 60)
        )

        title_render, title_height = self.font3.render(
            title,
            "white",
            title_area,
            gap=0,
            breaklines=False
        )

        title_rect = title_render.get_rect(
            centerx=width // 2,
            top=image_rect.bottom + 15
        )

        card.blit(title_render, title_rect)

        # -------------------------
        # Açıklama
        # -------------------------

        description = metadata["description"](
            self.game.settings.get("language")
        )

        description_area = pygame.Surface(
            (
                width - 30,
                height - (title_rect.bottom) - 30
            )
        )

        description_renders, line_height = (
            self.font4.render(
                description,
                (180, 180, 180),
                description_area,
                gap=0,
                breaklines=True
            )
        )

        y = title_rect.bottom + 10

        for rendered in description_renders:

            if y + rendered.get_height() > height - 10:
                break

            rendered_rect = rendered.get_rect(
                centerx=width // 2,
                top=y
            )

            card.blit(rendered, rendered_rect)

            y += line_height

        return card

    def get_achievement_card(
        self,
        achievement_id: str,
        width: int,
        height: int
    ):
        language = self.game.settings.get("language")

        key = (
            achievement_id,
            width,
            height,
            language
        )

        if key not in self.achievement_card_cache:
            self.achievement_card_cache[key] = (
                self.create_achievement_card(
                    achievement_id,
                    width,
                    height
                )
            )

        return self.achievement_card_cache[key]
    
    def get_achievement_image(self, achievement_id, image_size):
        key = (achievement_id, image_size)

        if key not in self.achievement_images:
            image = self.game.achievements.achievements_metadata[
                achievement_id
            ]["image"]

            self.achievement_images[key] = pygame.transform.smoothscale(
                image,
                (image_size, image_size)
            )

        return self.achievement_images[key]

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

        if self.verifying or self.initing_online:
            self.draw_loading(surface)
            self.offline_bar.draw(surface)
            return

        if self.offline:
            message = self.langs["no_internet_connection"]()

            message_font = self.font7

            message_area = pygame.Surface(
                (
                    surface.get_width() - 100,
                    surface.get_height() - 100
                )
            )

            renders, line_height = self.font7.render(
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
            message_font = self.font7

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
        if self.offline or self.illegal:
            return

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
        card = self.get_achievement_card(
            achievement_id,
            rect.width,
            rect.height
        )

        surface.blit(card, rect)

    def update(self, dt):
        self.initing_online = self.game.initing_online_data

        self.bar.update()
        self.offline_bar.update()

        if self.verifying or self.initing_online:
            self.loading_time += dt

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
        if self.verifying or self.illegal or self.offline or self.initing_online:
            self.offline_bar.handle_event(event)

        else:
            self.bar.handle_event(event)

    def draw_loading(self, surface):
        dots = "." * (int(self.loading_time * 2) % 4)

        message = f"{self.langs['verifying_achievements']()}{dots}"

        font = self.font7
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

        return self.font5.render(
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
        # 3
        self.font3 = get_font(
            self.game.fonts,
            Lang.USING_LANG,
            3,
            "DynamicFont"
        )

        self.font4 = get_font(
            self.game.fonts,
            Lang.USING_LANG,
            4,
            "DynamicFont"
        )

        self.font5 = get_font(
            self.game.fonts,
            Lang.USING_LANG,
            5,
            "DynamicFont"
        )
        # message / loading
        
        self.font7 = get_font(
            self.game.fonts,
            Lang.USING_LANG,
            7,
            "DynamicFont"
        )

        self.illegal = self.game.illegal
        self.offline = self.game.offline
        self.initing_online = self.game.initing_online_data

        if self.initing_online or self.illegal or self.offline:
            return

        self.achievement_counter = self.create_achievement_surface()

        if self.game.dump("last_music") != os.path.join(BASE_DIR, r"musics/menu_theme.mp3"):
            self.game.mixer.music.load(
                os.path.join(
                    BASE_DIR,
                    r"musics/menu_theme.mp3"
                )
            )

            self.game.mixer.music.play(-1)

        self.start_verify()
        self.update_achievements()
        self.bar.update(manual=True)
        self.offline_bar.update(manual=True)
