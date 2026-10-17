import os
from dfont import DynamicFont
import json
import pygame
from copy import deepcopy
from enum import Enum
from lang_support import Lang
from userfont import userFont
from ready_music import Music
from basedir import BASE_DIR
from calcs import SCALE, calculate_size
from update_manager import check_for_update
from screens.types import ScreenType

desktop_size = pygame.display.get_desktop_sizes()[0]


def is_json_serializable(value):
    try:
        json.dumps(value)
        return True
    except (TypeError, ValueError):
        return False


def make_json_serializable(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Enum):
        return make_json_serializable(value.value)
    if isinstance(value, dict):
        return {
            str(k): make_json_serializable(v)
            for k, v in value.items()
            if is_json_serializable(v)
        }
    if isinstance(value, (list, tuple, set)):
        return [
            make_json_serializable(v)
            for v in value
            if is_json_serializable(v)
        ]
    if hasattr(value, "__dict__"):
        return make_json_serializable(value.__dict__)
    return None


class Icon:
    def __init__(self, image_name: str | os.PathLike, size: int | float):
        self.image_name = image_name
        self.size = size
        self.image = pygame.image.load(self.image_name).convert_alpha()
        self.image = pygame.transform.scale_by(self.image, self.size)

    def draw(self, surface: pygame.Surface, x, y):
        rect = self.image.get_rect(center=(x, y))
        surface.blit(self.image, rect)


class SettingElement:
    default_size = (260, 40)

    def __init__(self, pos, image=None, size=None, icons: dict[str, Icon] = None):
        if size is None:
            size = self.default_size

        self.rect = pygame.Rect(pos, size)
        self.base_rel_pos = (pos[0], pos[1])

        self.image = self.prepare_image(image, self.rect.size)
        self.icons: dict[str, Icon] = icons or {}
        self.showing_icons: list[Icon] = []

    def prepare_image(self, image, size):
        if image is None:
            return None
        return pygame.transform.smoothscale(image, size)

    def draw_image(self, screen):
        if self.image:
            screen.blit(self.image, self.rect)

    def draw(self, screen, font, value):
        self.draw_image(screen)

    def draw_icon(self, screen):
        for icon in self.showing_icons:
            icon.draw(
                screen,
                self.rect.midright[0] + max(12, self.rect.width // 30),
                self.rect.midright[1]
            )

    def handle_event(self, event, value):
        return value


class Checkbox(SettingElement):
    default_size = (38, 38)

    def __init__(
        self,
        pos,
        checked_image=None,
        unchecked_image=None,
        size=None,
        icons=None,
        click_sound: pygame.mixer.Sound = None
    ):
        if size is None:
            size = self.default_size

        super().__init__(pos, size=size, icons=icons)

        self.checked_image = self.prepare_image(checked_image, self.rect.size)
        self.unchecked_image = self.prepare_image(unchecked_image, self.rect.size)
        self.click_sound = click_sound

    def draw(self, screen, font, value):
        image = self.checked_image if value else self.unchecked_image

        if image:
            screen.blit(image, self.rect)
        else:
            pygame.draw.rect(screen, (16, 22, 32), self.rect, border_radius=8)
            border_col = (0, 240, 255) if value else (70, 85, 105)
            pygame.draw.rect(screen, border_col, self.rect, width=2, border_radius=8)

            if value:
                inner = self.rect.inflate(-10, -10)
                pygame.draw.rect(screen, (0, 255, 170), inner, border_radius=5)
                pygame.draw.circle(screen, (255, 255, 255), inner.center, 3)

    def handle_event(self, event, value, *, volume: float = 0.0, play: bool = False):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if play and self.click_sound:
                    self.click_sound.set_volume(volume)
                    self.click_sound.play()
                return not value
        return value


class Slider(SettingElement):
    default_size = (360, 38)

    def __init__(
        self,
        pos,
        min_value,
        max_value,
        step=1,
        background_image=None,
        knob_image=None,
        size=None,
        icons=None,
        slide_sfx: pygame.mixer.Sound = None
    ):
        if size is None:
            size = self.default_size

        super().__init__(pos, background_image, size, icons=icons)

        self.min = min_value
        self.max = max_value
        self.step = step
        self.slide_sfx = slide_sfx
        self.knob_image = self.prepare_knob(knob_image)
        self.dragging = False

    def prepare_knob(self, image):
        if image is None:
            return None
        height = self.rect.height
        ratio = image.get_width() / image.get_height()
        width = int(height * ratio)
        return pygame.transform.smoothscale(image, (width, height))

    def draw(self, screen, font, value):
        ratio = (value - self.min) / (self.max - self.min)
        ratio = max(0.0, min(1.0, ratio))

        track_h = 8
        track_y = self.rect.centery - track_h // 2
        track_rect = pygame.Rect(self.rect.left, track_y, self.rect.width, track_h)

        pygame.draw.rect(screen, (20, 26, 38), track_rect, border_radius=4)
        pygame.draw.rect(screen, (40, 52, 70), track_rect, width=1, border_radius=4)

        filled_w = int(self.rect.width * ratio)
        if filled_w > 0:
            fill_rect = pygame.Rect(self.rect.left, track_y, filled_w, track_h)

            fill_color = (252, 3, 148) if self.dragging else (0, 230, 255)

            pygame.draw.rect(screen, fill_color, fill_rect, border_radius=4)
            pygame.draw.line(screen, (200, 255, 255), (fill_rect.left, track_y + 1), (fill_rect.right, track_y + 1), 1)

        knob_x = self.rect.left + filled_w
        if self.knob_image:
            knob_rect = self.knob_image.get_rect(center=(knob_x, self.rect.centery))
            screen.blit(self.knob_image, knob_rect)
        else:
            pygame.draw.circle(screen, (10, 14, 20), (knob_x, self.rect.centery), 11)
            pygame.draw.circle(screen, (0, 255, 240), (knob_x, self.rect.centery), 10)
            pygame.draw.circle(screen, (255, 255, 255), (knob_x, self.rect.centery), 4)

    def handle_event(self, event: pygame.event.Event, value, *, volume: float = 0.0, play: bool = False):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.dragging = True
                new_value = self.calculate_value(event.pos[0])
                if new_value != value and self.slide_sfx and play:
                    self.slide_sfx.set_volume(volume)
                    self.slide_sfx.play()
                return new_value

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False

        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                new_value = self.calculate_value(event.pos[0])
                if new_value != value and self.slide_sfx and play:
                    self.slide_sfx.set_volume(volume)
                    self.slide_sfx.play()
                return new_value

        return value

    def calculate_value(self, mouse_x):
        ratio = (mouse_x - self.rect.left) / self.rect.width
        ratio = max(0.0, min(1.0, ratio))
        value = self.min + ratio * (self.max - self.min)
        value = round(value / self.step) * self.step
        return max(self.min, min(self.max, value))


class TextBox(SettingElement):
    default_size = (360, 44)

    def __init__(self, pos, max_length=25, font: userFont = None, image=None, size=None, icons=None):
        if size is None:
            size = list(self.default_size)
            size[0] = font.font.size("W" * max_length)[0] + int(SCALE * 50)

        super().__init__(pos, image, size, icons=icons)
        self.font = font
        self.max_length = max_length
        self.active = False
        self.color = (55, 68, 88)
        # 

    def draw(self, screen: pygame.Surface, font: userFont, value):
        pygame.draw.rect(screen, (16, 22, 32), self.rect, border_radius=8)

        if self.active:
            self.color = (0, 240, 255)

        pygame.draw.rect(screen, self.color, self.rect, width=2, border_radius=8)

        use_font = self.font if self.font is not None else font
        txt_str = str(value)
        text_surf = use_font.return_text(txt_str, (240, 250, 255))

        screen.blit(
            text_surf,
            (self.rect.x + 12, self.rect.centery - text_surf.get_height() // 2)
        )

        if self.active:
            cursor_x = self.rect.x + 12 + text_surf.get_width() + 2
            pygame.draw.line(screen, (0, 255, 240), (cursor_x, self.rect.centery - 10), (cursor_x, self.rect.centery + 10), 2)

    def handle_event(self, event: pygame.event.Event, value):
        # Renk Önceliği
        # 1. Mavi: Aktifken
        # 2. Beyaz: Fare üzerindeyken
        # 3. Gri: Boştayken

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.active = True
            else:
                self.active = False
                self.color = (55, 68, 88)

        if not self.active and event.type == pygame.MOUSEMOTION:
            if self.rect.collidepoint(event.pos):
                self.color = (210, 255, 255)

            else:
                self.color = (55, 68, 88)

        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                value = value[:-1]
            elif event.key == pygame.K_RETURN:
                self.active = False
            elif event.unicode.isprintable() and len(value) < self.max_length:
                value += event.unicode
        return value


class Select(SettingElement):
    default_size = (320, 42)

    def __init__(self, pos, values, font: userFont = None, image=None, size=None, icons=None):
        if size is None:
            size = self.default_size
        self.font = font
        super().__init__(pos, image, size, icons=icons)

        self.index = 0
        self.values = values
        self.color = (50, 68, 90)

    def draw(self, screen, font: userFont, value):
        pygame.draw.rect(screen, (18, 24, 34), self.rect, border_radius=8)
        pygame.draw.rect(screen, self.color, self.rect, width=2, border_radius=8)

        pygame.draw.polygon(screen, (0, 240, 255), [
            (self.rect.left + 14, self.rect.centery),
            (self.rect.left + 20, self.rect.centery - 5),
            (self.rect.left + 20, self.rect.centery + 5)
        ])
        pygame.draw.polygon(screen, (0, 240, 255), [
            (self.rect.right - 14, self.rect.centery),
            (self.rect.right - 20, self.rect.centery - 5),
            (self.rect.right - 20, self.rect.centery + 5)
        ])

        use_font = self.font if self.font is not None else font
        txt_str = str(value)
        text = use_font.return_text(txt_str, (245, 250, 255))
        text_rect = text.get_rect(center=self.rect.center)
        screen.blit(text, text_rect)

    def handle_event(self, event: pygame.event.Event, value):
        if event.type == pygame.MOUSEMOTION:

            if self.rect.collidepoint(event.pos):
                self.color = (210, 255, 255)
            else:
                self.color = (50, 68, 90)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
            
                self.index = (self.index + 1) % len(self.values)

                return self.values[self.index]
        return value


class SettingsButton(SettingElement):
    default_size = (320, 44)

    def __init__(
        self,
        pos,
        text: str | Lang = "Buton",
        callback=None,
        params: list=None,
        font: userFont = None,
        size=None,
        click_sound: pygame.mixer.Sound = None,
        accent_color: tuple = (0, 240, 255),
        icons=None
    ):
        if size is None:
            size = self.default_size

        super().__init__(pos, size=size, icons=icons)
        self.text = text
        self.callback = callback
        self.params = params or []
        self.font = font
        self.click_sound = click_sound
        self.accent_color = accent_color
        self.is_hovered = False
        self.is_pressed = False

    def draw(self, screen: pygame.Surface, font: userFont, value):
        # 1. Fare Üzerinde mi Kontrolü (Hover)
        mx, my = pygame.mouse.get_pos()
        self.is_hovered = self.rect.collidepoint(mx, my)

        # 2. Gövde Dolgusu (Hover anında daha aydınlık siber-grafit)
        if self.is_pressed:
            bg_col = (10, 14, 20)
        elif self.is_hovered:
            bg_col = (24, 34, 48)
        else:
            bg_col = (16, 22, 32)

        pygame.draw.rect(screen, bg_col, self.rect, border_radius=8)

        # 3. Dış Neon Kontur & Parıltı
        border_col = (210, 255, 255) if self.is_hovered else self.accent_color
        border_w = 3 if self.is_hovered else 2
        pygame.draw.rect(screen, border_col, self.rect, width=border_w, border_radius=8)

        # 4. Üst Kenar Cam Işıltısı (Rim Highlight)
        if self.is_hovered:
            pygame.draw.line(
                screen,
                (255, 255, 255),
                (self.rect.left + 8, self.rect.top + 2),
                (self.rect.right - 8, self.rect.top + 2),
                2
            )

        # 5. Metin Çizimi (Lang desteğiyle)
        use_font = self.font if self.font is not None else font
        btn_str = self.text
        if isinstance(btn_str, Lang):
            btn_str = btn_str() if callable(btn_str) else str(btn_str)
        
        # Eğer buton bir durum mesajı döndürüyorsa (örn: "Güncel!") onu öncelikli yazdırır
        display_text = str(value) if value else str(btn_str)

        text_col = (255, 255, 255) if self.is_hovered else (200, 240, 255)
        text_surf = use_font.return_text(display_text, text_col)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def handle_event(self, event: pygame.event.Event, value, *, volume: float = 0.0, play: bool = False):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.is_pressed = True
                if play and self.click_sound:
                    self.click_sound.set_volume(volume)
                    self.click_sound.play()

                # Callback fonksiyonu tanımlıysa tetikle
                if callable(self.callback):
                    res = self.callback(*self.params)
                    # Eğer callback yeni bir durum metni döndürürse butonda o yazar
                    if res is not None:
                        return res
                return value

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.is_pressed = False

        return value


class Settings:
    def __init__(self, file="settings.json"):
        self.file = file

        # ---------------------------------
        # AYARLAR
        # ---------------------------------
        self.values = {
            "fullscreen": False,
            "music": True,
            "sfx": True,
            "music_volume": 0.7,
            "sfx_volume": 0.8,
            "music_source": Lang(türkçe="Seçilen Müzik", english="Selected Music", arabic="موسيقى مختارة", sanskrit="चयनितं सङ्गीतम्"),
            "selected_music": Lang(türkçe="Seçilmedi", english="Not Selected", arabic="لم يتم اختياره", sanskrit="न चयनितः आसीत्"),
            "other_music": "",
            "fps": 60,
            "language": "Türkçe",
            "check_updates": "",
            "credits": ""
        }

        self.types = {
            "fullscreen": bool,
            "music": bool,
            "sfx": bool,
            "music_volume": float,
            "sfx_volume": float,
            "music_source": Lang,
            "selected_music": Music,
            "other_music": str,
            "fps": int,
            "language": str,
            "check_updates": str,
            "credits": str
        }

        # ---------------------------------
        # UI TİPLERİ
        # ---------------------------------
        click_sfx = pygame.mixer.Sound(os.path.join(BASE_DIR, r"sounds/click.wav")) if os.path.exists(os.path.join(BASE_DIR, r"sounds/click.wav")) else None
        slide_sfx = pygame.mixer.Sound(os.path.join(BASE_DIR, r"sounds/slide_bar_sfx.wav")) if os.path.exists(os.path.join(BASE_DIR, r"sounds/slide_bar_sfx.wav")) else None

        self.options = {
            "fullscreen": {
                "type": "checkbox",
                "images": {
                    "checked": os.path.join(BASE_DIR, r"settings_images/checkbox_on.png"),
                    "unchecked": os.path.join(BASE_DIR, r"settings_images/checkbox_off.png")
                },
                "click_sound": click_sfx
            },
            "music": {
                "type": "checkbox",
                "images": {
                    "checked": os.path.join(BASE_DIR, r"settings_images/checkbox_on.png"),
                    "unchecked": os.path.join(BASE_DIR, r"settings_images/checkbox_off.png")
                },
                "click_sound": click_sfx
            },
            "sfx": {
                "type": "checkbox",
                "images": {
                    "checked": os.path.join(BASE_DIR, r"settings_images/checkbox_on.png"),
                    "unchecked": os.path.join(BASE_DIR, r"settings_images/checkbox_off.png")
                },
                "click_sound": click_sfx
            },
            "music_volume": {
                "type": "slider",
                "min": 0.0,
                "max": 1.0,
                "step": 0.05,
                "slide_sfx": slide_sfx
            },
            "sfx_volume": {
                "type": "slider",
                "min": 0.0,
                "max": 1.0,
                "step": 0.05,
                "slide_sfx": slide_sfx
            },
            "music_source": {
                "type": "select",
                "values": [
                    Lang(türkçe="Seçilen Müzik", english="Selected Music", arabic="موسيقى مختارة", sanskrit="चयनितं सङ्गीतम्"),
                    Lang(türkçe="Bilgisayardan Müzik", english="Music Path", arabic="موسيقى من الكمبيوتر", sanskrit="सङ्गणकात् सङ्गीतम्")
                ],
                "font_size": 24
            },
            "selected_music": {
                "type": "select",
                "values": [
                    Music(os.path.join(BASE_DIR, r"musics/eba_phonk.mp3"), "Eba Fank"),
                    Music(os.path.join(BASE_DIR, r"musics/bouncing_seals.mp3"), "Zıplayan foklar"),
                    Music(os.path.join(BASE_DIR, r"musics/miguel_phonk.mp3"), "Miguel Phonk"),
                    Music(os.path.join(BASE_DIR, r"musics/verity_obesity.mp3"), "Obez Verity"),
                    Music(os.path.join(BASE_DIR, r"musics/overclock.ogg"), "Overclock")
                ],
                "font_size": 24
            },
            "other_music": {
                "type": "textbox",
                "max_length": int(60 * SCALE),
                "icons": {
                    "path_found": Icon(os.path.join(BASE_DIR, r"settings_images/tick.png"), 0.1) if os.path.exists(os.path.join(BASE_DIR, r"settings_images/tick.png")) else None,
                    "path_not_found": Icon(os.path.join(BASE_DIR, "settings_images/x.png"), 0.1) if os.path.exists(os.path.join(BASE_DIR, "settings_images/x.png")) else None
                }
            },
            "fps": {
                "type": "slider",
                "min": 30,
                "max": 240,
                "step": 10,
                "slide_sfx": slide_sfx
            },
            "language": {
                "type": "select",
                "values": [
                    "Türkçe",
                    "English",
                    "Arabic",
                    "Sanskrit"
                ],
                "font_size": 24
            },

            "check_updates": {
                "type": "button",
                "text": Lang(
                    türkçe="Güncellemeleri Kontrol Et",
                    english="Check for Updates",
                    arabic="التحقق من التحديثات",
                    sanskrit="नवीनीकरणं परीक्ष्यताम्"
                ),
                "callback": check_for_update,
                "click_sound": click_sfx,
                "accent_color": (0, 240, 255)  # İstersen sarı (255, 205, 50) veya yeşil de yapabilirsin
            },
            "credits": {
                "type": "button",
                "text": Lang(
                    türkçe="Jeneriği Göster",
                    english="Show Credits",
                    arabic="عرض الأسماء المشاركة",
                    sanskrit="श्रेयः दर्शयतु"
                ),
                "click_sound": click_sfx,
                "callback": "__ongame__",
                "accent_color": (255, 205, 50)
            }
        }

        self.names = {
            "fullscreen": Lang(türkçe="Tam Ekran", english="Full Screen", arabic="ملء الشاشة", sanskrit="पूर्णपर्दे"),
            "music": Lang(türkçe="Müzik", english="Music", arabic="موسيقى", sanskrit="संगीतं"),
            "sfx": "SFX",
            "music_volume": Lang(türkçe="Müzik Sesi", english="Music Volume", arabic="صوت الموسيقى", sanskrit="संगीतध्वनिः"),
            "sfx_volume": Lang(türkçe="SFX Sesi", english="SFX Volume", arabic="مؤثر صوتي", sanskrit="SFX शब्दः"),
            "music_source": Lang(türkçe="Müzik Kaynağı", english="Music Source", arabic="مصدر الموسيقى", sanskrit="सङ्गीतस्य स्रोतः"),
            "selected_music": Lang(türkçe="Seçilen Müzik", english="Selected Music", arabic="موسيقى مختارة", sanskrit="चयनितं सङ्गीतम्"),
            "other_music": Lang(türkçe="Bilgisayardan Müzik", english="Music Path", arabic="موسيقى من الكمبيوتر", sanskrit="सङ्गणकात् सङ्गीतम्"),
            "fps": "FPS",
            "language": Lang(türkçe="Dil", english="Language", arabic="لغة", sanskrit="भाषा"),
            "check_updates": Lang(
                türkçe="Sürüm",
                english="Version",
                arabic="إصدار",
                sanskrit="संस्करणम्"
            ),
            "credits": Lang(
                türkçe="Jenerik",
                english="Credits",
                arabic="شكر وتقدير",
                sanskrit="श्रेयः ददाति"
            )
        }

        # ---------------------------------
        # BÜYÜTÜLMÜŞ NEON KUTU VE SCROLL SİSTEMİ
        # ---------------------------------
        self.full_panel_w = 1200 * SCALE
        self.full_panel_h = 760 * SCALE

        self.panel_w = self.full_panel_w
        self.panel_h = self.full_panel_h
        self.panel_rect = pygame.Rect(0, 0, self.panel_w, self.panel_h)

        self.header_h = 65
        self.content_padding = 32
        self.scrollbar_w = 12

        self.content_rect = pygame.Rect(
            0,
            self.header_h,
            self.panel_w - self.scrollbar_w - self.content_padding * 2,
            self.panel_h - self.header_h - self.content_padding
        )

        self.scroll_y = 0.0
        self.target_scroll_y = 0.0
        self.total_content_height = 0
        self.max_scroll = 0.0

        self.elements = {}
        self.element_relative_positions: dict[str, tuple[int, int]] = {}

        self.create_elements()
        self.load()

    # =================================================
    # ELEMENT OLUŞTURMA
    # =================================================
    def create_elements(self):
        # Büyütülmüş kutuya göre elemanların X konumu sağa kaydırıldı
        element_rel_x = 650
        rel_y = 25
        gap = 26

        for key, option in self.options.items():
            element_type = option["type"]

            if element_type == "checkbox":
                element = Checkbox(
                    (0, 0),
                    self.load_image(option.get("images", {}).get("checked")),
                    self.load_image(option.get("images", {}).get("unchecked")),
                    icons=option.get("icons"),
                    click_sound=option.get("click_sound")
                )

            elif element_type == "slider":
                element = Slider(
                    (0, 0),
                    option["min"],
                    option["max"],
                    option.get("step", 1),
                    self.load_image(option.get("images", {}).get("background")),
                    self.load_image(option.get("images", {}).get("knob")),
                    icons=option.get("icons"),
                    slide_sfx=option.get("slide_sfx")
                )

            elif element_type == "select":
                font_path = os.path.join(BASE_DIR, r"fonts/unifont-18.0.01.otf")
                font = userFont(font_path, option.get("font_size", 24)) if os.path.exists(font_path) else None
                element = Select((0, 0), option["values"], font=font, icons=option.get("icons"))

            elif element_type == "textbox":
                font_path = os.path.join(BASE_DIR, r"fonts/unifont-18.0.01.otf")
                font = userFont(font_path, 22) if os.path.exists(font_path) else None

                element = TextBox((0, 0), option.get("max_length", 35), font=font, icons=option.get("icons"))
            
            elif element_type == "button":
                font_path = os.path.join(BASE_DIR, r"fonts/unifont-18.0.01.otf")
                font = userFont(font_path, option.get("font_size", 22)) if os.path.exists(font_path) else None
                
                element = SettingsButton(
                    (0, 0),
                    text=option.get("text", "Buton"),
                    callback=option.get("callback"),
                    font=font,
                    click_sound=option.get("click_sound"),
                    params=option.get("params", None),
                    accent_color=option.get("accent_color", (0, 240, 255)),
                    icons=option.get("icons")
                )

            else:
                continue

            self.elements[key] = element
            self.element_relative_positions[key] = (element_rel_x, rel_y)
            rel_y += element.rect.height + gap

        self.total_content_height = rel_y + 15
        self.max_scroll = max(0.0, float(self.total_content_height - self.content_rect.height))

    # =================================================
    # GET / SET & DOSYA
    # =================================================
    @property
    def height(self):
        return self.panel_h

    @property
    def y(self):
        return self.panel_rect.top

    def get(self, name):
        return self.values.get(name)

    def get_element(self, name: str) -> SettingElement | None:
        return self.elements.get(name)

    def set(self, name, value):
        if name not in self.values:
            return
        self.values[name] = value

    def save(self):
        values = deepcopy(self.values)
        values = make_json_serializable(values)
        with open(self.file, "w", encoding="utf-8") as file:
            json.dump(values, file, ensure_ascii=False, indent=4)

    def load(self):
        try:
            with open(self.file, "r", encoding="utf-8") as file:
                data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return

        for key, value in data.items():
            if key not in self.values:
                continue
            if type(value) is self.types[key]:
                self.values[key] = value

    def load_image(self, path):
        if not path or not os.path.exists(path):
            return None
        try:
            return pygame.image.load(path).convert_alpha()
        except pygame.error:
            return None

    # =================================================
    # GÜNCELLEME VE LERP SCROLL
    # =================================================
    def update(self, dt: float = 0.016, swidth=None, sheight=None):

        self.scroll_y += (self.target_scroll_y - self.scroll_y) * min(1.0, 14.0 * dt)

        if swidth is not None and sheight is not None:
            self.panel_w = calculate_size(self.full_panel_w, 1920 * SCALE, swidth)
            self.panel_h = calculate_size(self.full_panel_h, 1080 * SCALE, sheight)
            self.panel_rect.width = self.panel_w
            self.panel_rect.height = self.panel_h

        content_origin_x = self.content_rect.left
        content_origin_y = self.content_rect.top - self.scroll_y

        for key, element in self.elements.items():
            rel_x, rel_y = self.element_relative_positions[key]
            element.rect.topleft = (
                content_origin_x + rel_x,
                int(content_origin_y + rel_y)
            )

    # =================================================
    # EVENT YÖNETİMİ
    # =================================================
    def handle_event(self, event):
        if event.type == pygame.MOUSEWHEEL:
            self.target_scroll_y -= event.y * 60
            self.target_scroll_y = max(0.0, min(self.max_scroll, self.target_scroll_y))
            return

        is_mouse_click = event.type == pygame.MOUSEBUTTONDOWN
        if is_mouse_click and not self.content_rect.collidepoint(event.pos):
            for el in self.elements.values():
                if isinstance(el, TextBox):
                    el.active = False
            return

        for key, element in self.elements.items():
            element: SettingElement
            old_value = self.values[key]

            if isinstance(element, (Checkbox, Slider)):
                new_value = element.handle_event(
                    event,
                    old_value,
                    volume=self.get("sfx_volume"),
                    play=self.get("sfx")
                )
            else:
                new_value = element.handle_event(event, old_value)

            self.values[key] = new_value

    # =================================================
    # ÇİZİM (NEON HUD STİLİ)
    # =================================================
    def draw(self, screen: pygame.Surface, font: userFont | DynamicFont, swidth=None, sheight=None):
        if swidth is not None and sheight is not None:
            self.panel_rect.center = (swidth // 2, sheight // 2)
            self.content_rect.left = self.panel_rect.left + self.content_padding
            self.content_rect.top = self.panel_rect.top + self.header_h + 10
            self.content_rect.width = self.panel_w - self.scrollbar_w - self.content_padding * 2 - 16
            self.content_rect.height = self.panel_h - self.header_h - self.content_padding - 18

        else:
            sw, sh = screen.get_size()
            self.panel_rect.center = (sw // 2, sh // 2)

            self.content_rect.left = self.panel_rect.left + self.content_padding
            self.content_rect.top = self.panel_rect.top + self.header_h + 10
            self.content_rect.width = self.panel_w - self.scrollbar_w - self.content_padding * 2 - 16
            self.content_rect.height = self.panel_h - self.header_h - self.content_padding - 18

        # ---------------------------------------------------------
        # 1. NEON KUTU GÖVDESİ & ÇERÇEVESİ
        # ---------------------------------------------------------
        pygame.draw.rect(screen, (12, 16, 24), self.panel_rect, border_radius=18)
        pygame.draw.rect(screen, (0, 110, 160), self.panel_rect.inflate(4, 4), width=3, border_radius=20)
        pygame.draw.rect(screen, (0, 240, 255), self.panel_rect, width=2, border_radius=18)

        # ---------------------------------------------------------
        # 2. ÜST NEON BAŞLIK
        # ---------------------------------------------------------
        header_rect = pygame.Rect(self.panel_rect.left, self.panel_rect.top, self.panel_w, self.header_h)
        pygame.draw.rect(screen, (16, 22, 34), header_rect, border_top_left_radius=18, border_top_right_radius=18)
        pygame.draw.line(screen, (0, 240, 255), header_rect.bottomleft, header_rect.bottomright, 2)

        title_text = "// SYSTEM CONFIGURATION //"
        if type(font) == userFont:
            title_surf = font.return_text(title_text, (0, 240, 255))
            screen.blit(title_surf, title_surf.get_rect(center=header_rect.center))

        elif type(font) == DynamicFont:
            title_surf, _ = font.render(
                title_text,
                (0, 240, 255),
                self.panel_rect
            )

            screen.blit(title_surf, title_surf.get_rect(center=header_rect.center))

        corner_len = 18
        pygame.draw.line(screen, (255, 255, 255), (self.panel_rect.left + 10, self.panel_rect.top + 10), (self.panel_rect.left + 10 + corner_len, self.panel_rect.top + 10), 2)
        pygame.draw.line(screen, (255, 255, 255), (self.panel_rect.left + 10, self.panel_rect.top + 10), (self.panel_rect.left + 10, self.panel_rect.top + 10 + corner_len), 2)
        pygame.draw.line(screen, (255, 255, 255), (self.panel_rect.right - 10, self.panel_rect.bottom - 10), (self.panel_rect.right - 10 - corner_len, self.panel_rect.bottom - 10), 2)
        pygame.draw.line(screen, (255, 255, 255), (self.panel_rect.right - 10, self.panel_rect.bottom - 10), (self.panel_rect.right - 10, self.panel_rect.bottom - 10 - corner_len), 2)

        # ---------------------------------------------------------
        # 3. İÇERİK ÇİZİMİ (SET_CLIP)
        # ---------------------------------------------------------
        screen.set_clip(self.content_rect)

        for key, element in self.elements.items():
            element: SettingElement

            if element.rect.bottom < self.content_rect.top - 20 or element.rect.top > self.content_rect.bottom + 20:
                continue

            name = self.names.get(key, key)
            if isinstance(name, Lang):
                name = name.get(self.values["language"].lower())

            text_str = str(name)
            if type(font) == userFont:
                text_shadow = font.return_text(text_str, (10, 14, 20))
                text_front = font.return_text(text_str, (185, 200, 220))
            
            elif type(font) == DynamicFont:
                text_shadow, _ = font.render(text_str, (10, 14, 20), self.panel_rect)
                text_front, _ = font.render(text_str, (185, 200, 220), self.panel_rect)

            text_pos = (element.rect.left - 40, element.rect.centery)
            shadow_rect = text_shadow.get_rect(midright=(text_pos[0] + 1, text_pos[1] + 1))
            front_rect = text_front.get_rect(midright=text_pos)

            screen.blit(text_shadow, shadow_rect)
            screen.blit(text_front, front_rect)

            element.draw(screen, font, self.values[key])
            element.draw_icon(screen)

        screen.set_clip(None)

        # ---------------------------------------------------------
        # 4. NEON SCROLLBAR
        # ---------------------------------------------------------
        if self.max_scroll > 0:
            sb_x = self.panel_rect.right - self.content_padding - self.scrollbar_w
            sb_y = self.content_rect.top
            sb_h = self.content_rect.height

            track_rect = pygame.Rect(sb_x, sb_y, self.scrollbar_w, sb_h)
            pygame.draw.rect(screen, (16, 22, 32), track_rect, border_radius=6)
            pygame.draw.rect(screen, (32, 44, 60), track_rect, width=1, border_radius=6)

            visible_ratio = self.content_rect.height / self.total_content_height
            thumb_h = max(30, int(sb_h * visible_ratio))
            scroll_progress = self.scroll_y / self.max_scroll
            thumb_y = sb_y + int((sb_h - thumb_h) * scroll_progress)

            thumb_rect = pygame.Rect(sb_x, thumb_y, self.scrollbar_w, thumb_h)
            pygame.draw.rect(screen, (0, 240, 255), thumb_rect, border_radius=6)
            pygame.draw.rect(screen, (200, 255, 255), thumb_rect.inflate(-4, -4), border_radius=4)
