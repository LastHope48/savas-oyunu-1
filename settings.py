import pygame
import json
import sys
import os
from copy import deepcopy
from enum import Enum
from lang_support import Lang
from classes import userFont, Music

from basedir import BASE_DIR


desktop_size = pygame.display.get_desktop_sizes()[0]

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def is_json_serializable(value):
    try:
        json.dumps(value)
        return True
    except (TypeError, ValueError):
        return False


def make_json_serializable(value):

    # JSON'un doğrudan desteklediği tipler
    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    # Enum
    if isinstance(value, Enum):
        return make_json_serializable(value.value)

    # Dictionary
    if isinstance(value, dict):
        return {
            str(k): make_json_serializable(v)
            for k, v in value.items()
            if is_json_serializable(v)
        }

    # List / tuple
    if isinstance(value, (list, tuple)):
        return [
            make_json_serializable(v)
            for v in value
            if is_json_serializable(v)
        ]

    # Set
    if isinstance(value, set):
        return [
            make_json_serializable(v)
            for v in value
            if is_json_serializable(v)
        ]

    # Nesne
    if hasattr(value, "__dict__"):
        return make_json_serializable(value.__dict__)

    # JSON'a çevrilemiyorsa
    return None


class Icon:
    def __init__(self, image_name: str | os.PathLike, size: int | float):
        self.image_name = image_name
        self.size = size
        self.image = pygame.image.load(self.image_name)
        self.image = pygame.transform.scale_by(self.image, self.size)

    def draw(self, surface: pygame.Surface, x, y):

        rect = self.image.get_rect(center=(x, y))

        surface.blit(
            self.image,
            rect
        )


class SettingElement:
    default_size = (200, 40)

    def __init__(self, pos, image=None, size=None, icons: dict[str, Icon]=None):
        if size is None:
            size = self.default_size

        self.rect = pygame.Rect(
            pos,
            size
        )

        self.image = self.prepare_image(
            image,
            self.rect.size
        )

        self.icons: dict[str, Icon] = icons or []
        self.showing_icons: list[Icon] = []


    def prepare_image(self, image, size):
        if image is None:
            return None

        return pygame.transform.smoothscale(
            image,
            size
        )

    def draw_image(self, screen):
        if self.image:
            screen.blit(
                self.image,
                self.rect
            )

    def draw(self, screen, font, value):
        self.draw_image(screen)

    def draw_icon(self, screen):
        for icon in self.showing_icons:
            icon.draw(
                screen,
                self.rect.midright[0] + self.rect.width // 30,
                self.rect.midright[1]
            )

    def handle_event(self, event, value):
        return value


class Checkbox(SettingElement):
    default_size = (40, 40)

    def __init__(
        self,
        pos,
        checked_image=None,
        unchecked_image=None,
        size=None,
        icons=None,
        click_sound: pygame.mixer.Sound=None
    ):
        if size is None:
            size = self.default_size

        super().__init__(pos, size=size, icons=icons)

        self.checked_image = self.prepare_image(
            checked_image,
            self.rect.size
        )

        self.unchecked_image = self.prepare_image(
            unchecked_image,
            self.rect.size
        )

        self.click_sound = click_sound

    def draw(self, screen, font, value):

        image = (
            self.checked_image
            if value
            else self.unchecked_image
        )

        if image:
            screen.blit(image, self.rect)

        else:
            pygame.draw.rect(
                screen,
                (220, 220, 220),
                self.rect,
                2
            )

            if value:
                pygame.draw.rect(
                    screen,
                    (70, 200, 100),
                    self.rect.inflate(-8, -8)
                )

    def handle_event(self, event, value, *, volume: float = 0.0, play: bool = False):

        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and self.rect.collidepoint(event.pos)
        ):

            if play:
                self.click_sound.set_volume(volume)
                self.click_sound.play()
            
            return not value

        return value


class Slider(SettingElement):
    default_size = (300, 40)

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
        slide_sfx: pygame.mixer.Sound=None
    ):
        if size is None:
            size = self.default_size

        super().__init__(
            pos,
            background_image,
            size,
            icons=icons
        )

        self.min = min_value
        self.max = max_value
        self.step = step

        self.slide_sfx = slide_sfx

        self.knob_image = self.prepare_knob(
            knob_image
        )

        self.empty_surface = pygame.Surface(
            self.rect.size,
            pygame.SRCALPHA
        )

        self.filled_surface = pygame.Surface(
            self.rect.size,
            pygame.SRCALPHA
        )

        pygame.draw.rect(
            self.empty_surface,
            (80, 80, 80),
            (
                0,
                self.rect.height // 2 - 4,
                self.rect.width,
                8
            ),
            border_radius=4
        )


        # DOLU ÇİZGİ
        pygame.draw.rect(
            self.filled_surface,
            (70, 180, 100),
            (
                0,
                self.rect.height // 2 - 4,
                self.rect.width,
                8
            ),
            border_radius=4
        )

        self.dragging = False

    def prepare_knob(self, image):

        if image is None:
            return None

        # Knob da kendi boyutunu koruyarak
        # rect'in yüksekliğine göre ölçeklenebilir.
        height = self.rect.height

        ratio = image.get_width() / image.get_height()

        width = int(height * ratio)

        return pygame.transform.smoothscale(
            image,
            (width, height)
        )

    def draw(self, screen, font, value):

        ratio = (
            (value - self.min)
            / (self.max - self.min)
        )

        ratio = max(0, min(1, ratio))

        # Boş bölüm
        screen.blit(
            self.empty_surface,
            self.rect
        )

        # Dolu bölüm
        filled_width = int(
            self.rect.width * ratio
        )

        if filled_width > 0:

            source_rect = pygame.Rect(
                0,
                0,
                filled_width,
                self.rect.height
            )

            screen.blit(
                self.filled_surface,
                self.rect,
                source_rect
            )

        # Dış kasa
        self.draw_image(screen)

        # Knob
        if self.knob_image:

            knob_x = (
                self.rect.left
                + int(self.rect.width * ratio)
            )

            knob_rect = self.knob_image.get_rect(
                center=(
                    knob_x,
                    self.rect.centery
                )
            )

            screen.blit(
                self.knob_image,
                knob_rect
            )

        else:
            # Görsel yoksa varsayılan knob
            knob_x = (
                self.rect.left
                + int(self.rect.width * ratio)
            )

            pygame.draw.circle(
                screen,
                (255, 255, 255),
                (knob_x, self.rect.centery),
                self.rect.height // 2
            )

    def handle_event(
        self,
        event,
        value,
        *,
        volume: float = 0.0,
        play: bool = False
    ):
        if event.type == pygame.MOUSEBUTTONDOWN:

            if self.rect.collidepoint(event.pos):
                self.dragging = True

                new_value = self.calculate_value(event.pos[0])

                if new_value != value:
                    if self.slide_sfx is not None and play:
                        self.slide_sfx.set_volume(volume)
                        self.slide_sfx.play()

                return new_value

        elif event.type == pygame.MOUSEBUTTONUP:

            self.dragging = False

        elif event.type == pygame.MOUSEMOTION:

            if self.dragging:

                new_value = self.calculate_value(event.pos[0])

                # Sadece slider değeri değiştiyse ses çal
                if new_value != value:

                    if self.slide_sfx is not None and play:
                        self.slide_sfx.set_volume(volume)
                        self.slide_sfx.play()

                    return new_value

        return value

    def calculate_value(self, mouse_x):

        ratio = (
            mouse_x - self.rect.left
        ) / self.rect.width

        ratio = max(0, min(1, ratio))

        value = (
            self.min
            + ratio * (self.max - self.min)
        )

        value = round(
            value / self.step
        ) * self.step

        return max(
            self.min,
            min(self.max, value)
        )


class TextBox(SettingElement):
    default_size = (300, 50)

    def __init__(
        self,
        pos,
        max_length=20,
        font: userFont=None,
        image=None,
        size=None,
        icons=None
    ):
        if size is None:
            size = self.default_size

        size = (
            desktop_size[0] * size[0],
            font.font.get_height()
        )

        super().__init__(
            pos,
            image,
            size,
            icons=icons
        )

        self.font = font
        self.max_length = max_length
        self.active = False

    def draw(self, screen: pygame.Surface, font: userFont, value):

        pygame.draw.rect(
            screen,
            (40, 40, 40),
            self.rect
        )

        pygame.draw.rect(
            screen,
            (100, 180, 255)
            if self.active
            else (150, 150, 150),
            self.rect,
            2
        )

        if self.font is not None:
            text = self.font.return_text(
                str(value),
                (255, 255, 255)
            )
        else:
            text = font.return_text(
                str(value),
                (255, 255, 255)
            )

        screen.blit(
            text,
            (
                self.rect.x + 10,
                self.rect.centery
                - text.get_height() // 2
            )
        )

    def handle_event(self, event: pygame.event.Event, value):

        if event.type == pygame.MOUSEBUTTONDOWN:

            self.active = self.rect.collidepoint(
                event.pos
            )

        if (
            event.type == pygame.KEYDOWN
            and self.active
        ):

            if event.key == pygame.K_BACKSPACE:

                value = value[:-1]

            elif event.key == pygame.K_RETURN:

                self.active = False

            elif (
                event.unicode.isprintable()
                and len(value) < self.max_length
            ):

                value += event.unicode

        return value


class Select(SettingElement):
    default_size = (200, 40)

    def __init__(
        self,
        pos,
        values,
        font: userFont=None,
        image=None,
        size=None,
        icons=None
    ):
        if size is None:
            size = self.default_size
        self.font = font

        super().__init__(
            pos,
            image,
            size,
            icons=icons
        )

        self.index = 0
        self.values = values

    def draw(self, screen, font: userFont, value):

        if self.image:
            self.draw_image(screen)

        else:
            pygame.draw.rect(
                screen,
                (50, 50, 50),
                self.rect
            )

            pygame.draw.rect(
                screen,
                (200, 200, 200),
                self.rect,
                2
            )

        if self.font is not None:
            text = self.font.return_text(
                str(value),
                (255, 255, 255)
            )
        else:
            text = font.return_text(
                str(value),
                (255, 255, 255)
            )

        text_rect = text.get_rect(
            center=self.rect.center
        )

        screen.blit(text, text_rect)

    def handle_event(self, event: pygame.event.Event, value):

        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and self.rect.collidepoint(event.pos)
        ):

            self.index += 1

            if self.index >= len(self.values):
                self.index = 0

            return self.values[self.index]

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
        }

        # ---------------------------------
        # TİPLER
        # ---------------------------------

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
        }

        # ---------------------------------
        # UI TİPLERİ
        # ---------------------------------

        self.options = {

            "fullscreen": {
                "type": "checkbox",
                "images": {
                    "checked": resource_path(r"settings_images/checkbox_on.png"),
                    "unchecked": resource_path(r"settings_images/checkbox_off.png")
                },

                "click_sound": pygame.mixer.Sound(os.path.join(BASE_DIR, r"sounds/click.wav"))
            },

            "music": {
                "type": "checkbox",
                "images": {
                    "checked": resource_path(r"settings_images/checkbox_on.png"),
                    "unchecked": resource_path(r"settings_images/checkbox_off.png")
                },

                "click_sound": pygame.mixer.Sound(os.path.join(BASE_DIR, r"sounds/click.wav"))
            },

            "sfx": {
                "type": "checkbox",
                "images": {
                    "checked": resource_path(r"settings_images/checkbox_on.png"),
                    "unchecked": resource_path(r"settings_images/checkbox_off.png")
                },

                "click_sound": pygame.mixer.Sound(os.path.join(BASE_DIR, r"sounds/click.wav"))
            },

            "music_volume": {
                "type": "slider",
                "min": 0.0,
                "max": 1.0,
                "step": 0.1,
                "slide_sfx": pygame.mixer.Sound(os.path.join(BASE_DIR, r"sounds/slide_bar_sfx.wav"))
            },

            "sfx_volume": {
                "type": "slider",
                "min": 0.0,
                "max": 1.0,
                "step": 0.1,
                "slide_sfx": pygame.mixer.Sound(os.path.join(BASE_DIR, r"sounds/slide_bar_sfx.wav"))
            },

            "music_source": {
                "type": "select",
                "values": [
                    Lang(türkçe="Seçilen Müzik", english="Selected Music", arabic="موسيقى مختارة", sanskrit="चयनितं सङ्गीतम्"),
                    Lang(türkçe="Bilgisayardan Müzik", english="Music Path", arabic="موسيقى من الكمبيوتر", sanskrit="सङ्गणकात् सङ्गीतम्")
                ],
                "font_size": 30
            },

            "selected_music": {
                "type": "select",
                "values": [
                    Music(
                        os.path.join(BASE_DIR, r"musics/holding_out_for_a_hero.mp3"),
                        "Adam akıllı müzik"
                    ),
                    Music(
                        os.path.join(BASE_DIR, r"musics/eba_phonk.mp3"),
                        "Eba Fank"
                    ),
                    Music(
                        os.path.join(BASE_DIR, r"musics/bouncing_seals.mp3"),
                        "Zıplayan foklar"
                    ),
                    Music(
                        os.path.join(BASE_DIR, r"musics/miguel_phonk.mp3"),
                        "Miguel Phonk"
                    ),
                    Music(
                        os.path.join(BASE_DIR, r"musics/verity_obesity.mp3"),
                        "Obez Verity"
                    )
                ],
                "font_size": 30
            },

            "other_music": {
                "type": "textbox",
                "max_length": desktop_size[0] // 50,
                "icons": {
                    "path_found": Icon(resource_path(r"settings_images/tick.png"), 0.1),
                    "path_not_found": Icon(resource_path(r"settings_images/x.png"), 0.1)
                }
            },

            "fps": {
                "type": "slider",
                "min": 30,
                "max": 240,
                "step": 10,
                "slide_sfx": pygame.mixer.Sound(os.path.join(BASE_DIR, r"sounds/slide_bar_sfx.wav"))
            },

            "language": {
                "type": "select",
                "values": [
                    "Türkçe",
                    "English",
                    "Arabic",
                    "Sanskrit"
                ],
                "font_size": 30
            }
        }

        # ---------------------------------
        # ADLAR
        # ---------------------------------

        self.names = {
            "fullscreen": Lang(türkçe="Tam Ekran", english="Full Screen", arabic="ملء الشاشة", sanskrit="पूर्णपर्दे"),
            "music": Lang(türkçe="Müzik", english="Music", arabic="موسيقى", sanskrit="संगीतं"),
            "sfx": "SFX",
            "music_volume": Lang(türkçe="Müzik Sesi", english="Music Volume", arabic="صوت الموسيقى",sanskrit="संगीतध्वनिः"),
            "sfx_volume": Lang(türkçe="SFX Sesi", english="SFX Volume", arabic="مؤثر صوتي", sanskrit="SFX शब्दः"),
            "music_source": Lang(türkçe="Müzik Kaynağı", english="Music Source", arabic="مصدر الموسيقى", sanskrit="सङ्गीतस्य स्रोतः"),
            "selected_music": Lang(türkçe="Seçilen Müzik",english="Selected Music", arabic="موسيقى مختارة", sanskrit="चयनितं सङ्गीतम्"),
            "other_music": Lang(türkçe="Bilgisayardan Müzik", english="Music Path", arabic="موسيقى من الكمبيوتر", sanskrit="सङ्गणकात् सङ्गीतम्"),
            "fps": "FPS",
            "language": Lang(türkçe="Dil", english="Language", arabic="لغة", sanskrit="भाषा")
        }

        self.active_textbox = None

        self.elements = {}

        self.create_elements()

        self.load()

    # =================================================
    # DEĞER İŞLEMLERİ
    # =================================================

    @property
    def height(self):
        if not self.elements:
            return 0

        first = next(iter(self.elements.values()))
        last = next(reversed(self.elements.values()))


        return last.rect.bottom - first.rect.top

    @property
    def y(self):
        if not self.elements:
            return 0

        first = next(iter(self.elements.values()))
        return first.rect.top

    def get(self, name):
        return self.values[name]

    def get_element(self, name: str) -> SettingElement | None:
        return self.elements.get(name)

    def set(self, name, value):

        if name not in self.values:
            return

        expected_type = self.types[name]

        if not type(value) is expected_type:
            return

        self.values[name] = value

    # =================================================
    # SAVE / LOAD
    # =================================================

    def save(self):

        values = deepcopy(self.values)

        values = make_json_serializable(values)

        with open(self.file, "w", encoding="utf-8") as file:
            json.dump(
                values,
                file,
                ensure_ascii=False,
                indent=4
            )

    def load(self):

        try:

            with open(
                self.file,
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(file)

        except (FileNotFoundError, json.JSONDecodeError):

            return

        for key, value in data.items():

            if key not in self.values:
                continue

            expected_type = self.types[key]

            if type(value) is not expected_type:
                continue

            self.values[key] = value

    # =================================================
    # DRAW
    # =================================================

    def draw(self, screen: pygame.Surface, font: userFont):

        for key, element in self.elements.items():

            element: SettingElement

            name = self.names.get(key, key)

            if isinstance(name, Lang):
                name = name.get(self.values["language"].lower())

            text = font.return_text(
                name,
                (255, 255, 255)
            )

            # Yazının sağ tarafı elemanın solundan
            # 30 piksel önce bitsin.
            text_rect = text.get_rect(
                midright=(
                    element.rect.left - 30,
                    element.rect.centery
                )
            )

            screen.blit(text, text_rect)

            # Ayar elemanını çiz
            element.draw(
                screen,
                font,
                self.values[key]
            )

            element.draw_icon(screen)

    # =================================================
    # EVENT
    # =================================================

    def handle_event(self, event):

        for key, element in self.elements.items():

            element: SettingElement

            old_value = self.values[key]

            if type(element) == Checkbox:
                new_value = element.handle_event(
                    event,
                    old_value,
                    volume=self.get("sfx_volume"),
                    play=self.get("sfx")
                )

            elif type(element) == Slider:
                new_value = element.handle_event(
                    event,
                    old_value,
                    volume=self.get("sfx_volume"),
                    play=self.get("sfx")
                )

            else:

                new_value = element.handle_event(
                    event,
                    old_value
                )

            self.values[key] = new_value

    def create_elements(self):

        # Ayar elemanlarının başlayacağı sabit X
        element_x = 700

        # İlk elemanın Y konumu
        y = 200

        # Elemanlar arasındaki dikey boşluk
        gap = 20

        for key, option in self.options.items():

            element_type = option["type"]

            if element_type == "checkbox":

                images: dict = option.get("images", {})

                checked_image = self.load_image(
                    images.get("checked")
                )

                unchecked_image = self.load_image(
                    images.get("unchecked")
                )

                click_sound = option.get("click_sound", None)

                icons = option.get("icons", {})

                element = Checkbox(
                    (element_x, y),
                    checked_image,
                    unchecked_image,
                    icons=icons,
                    click_sound=click_sound
                )

            elif element_type == "slider":

                images = option.get("images", {})

                background_image = self.load_image(
                    images.get("background")
                )

                knob_image = self.load_image(
                    images.get("knob")
                )

                slide_sfx = option.get("slide_sfx")

                icons = option.get("icons", {})

                element = Slider(
                    (element_x, y),
                    option["min"],
                    option["max"],
                    option.get("step", 1),
                    background_image,
                    knob_image,
                    icons=icons,
                    slide_sfx=slide_sfx
                )

            elif element_type == "select":

                icons = option.get("icons", {})

                font = userFont(os.path.join(BASE_DIR, r"fonts/unifont-18.0.01.otf"), option.get("font_size", 30))
    
                element = Select(
                    (element_x, y),
                    option["values"],
                    font=font,
                    icons=icons
                )
                print(type(option["values"]))
                print(option["values"])

                size_x = max((element.font.font.size(val.__str__())[0] for val in option["values"]))

                element.rect.width=(size_x + 20)

            elif element_type == "textbox":

                icons = option.get("icons", {})

                font = userFont(os.path.join(BASE_DIR, r"fonts/unifont-18.0.01.otf"), option.get("font_size", TextBox.default_size[1]))

                element = TextBox(
                    (element_x, y),
                    option.get("max_length", 20),
                    font=font,
                    icons=icons
                )

                size_x = element.font.font.size("W" * option.get("max_length", 20))[0]

                element.rect.width = size_x + 20

            else:
                continue

            self.elements[key] = element

            y += element.rect.height + gap

    def load_image(self, path):
        if not path:
            return None

        try:
            return pygame.image.load(path).convert_alpha()

        except (pygame.error, FileNotFoundError) as e:
            print(f"Görsel yüklenemedi: {path}")
            print(e)
            return None
