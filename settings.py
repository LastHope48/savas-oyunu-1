import pygame
import json
import sys
import os
from fonts import font3
from copy import deepcopy
from enum import Enum
from lang_support import Lang
from classes import userFont


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


class SettingElement:
    default_size = (200, 40)

    def __init__(self, pos, image=None, size=None):
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

    def handle_event(self, event, value):
        return value


class Checkbox(SettingElement):
    default_size = (40, 40)

    def __init__(
        self,
        pos,
        checked_image=None,
        unchecked_image=None,
        size=None
    ):
        if size is None:
            size = self.default_size

        super().__init__(pos, size=size)

        self.checked_image = self.prepare_image(
            checked_image,
            self.rect.size
        )

        self.unchecked_image = self.prepare_image(
            unchecked_image,
            self.rect.size
        )

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

    def handle_event(self, event, value):

        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and self.rect.collidepoint(event.pos)
        ):
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
        size=None
    ):
        if size is None:
            size = self.default_size

        super().__init__(
            pos,
            background_image,
            size
        )

        self.min = min_value
        self.max = max_value
        self.step = step

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

    def handle_event(self, event, value):

        if event.type == pygame.MOUSEBUTTONDOWN:

            if self.rect.collidepoint(event.pos):
                self.dragging = True

                return self.calculate_value(
                    event.pos[0]
                )

        elif event.type == pygame.MOUSEBUTTONUP:

            self.dragging = False

        elif event.type == pygame.MOUSEMOTION:

            if self.dragging:
                return self.calculate_value(
                    event.pos[0]
                )

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
    default_size = (300, 40)

    def __init__(
        self,
        pos,
        max_length=20,
        font: userFont=None,
        image=None,
        size=None
    ):
        if size is None:
            size = self.default_size

        super().__init__(
            pos,
            image,
            size
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
        size=None
    ):
        if size is None:
            size = self.default_size
        self.font = font

        super().__init__(
            pos,
            image,
            size
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
            "music": False,
            "sfx": True,
            "music_volume": 0.7,
            "sfx_volume": 0.8,
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
                }
            },

            "music": {
                "type": "checkbox",
                "images": {
                    "checked": resource_path(r"settings_images/checkbox_on.png"),
                    "unchecked": resource_path(r"settings_images/checkbox_off.png")
                }
            },

            "sfx": {
                "type": "checkbox",
                "images": {
                    "checked": resource_path(r"settings_images/checkbox_on.png"),
                    "unchecked": resource_path(r"settings_images/checkbox_off.png")
                }
            },

            "music_volume": {
                "type": "slider",
                "min": 0.0,
                "max": 1.0,
                "step": 0.1
            },

            "sfx_volume": {
                "type": "slider",
                "min": 0.0,
                "max": 1.0,
                "step": 0.1
            },

            "other_music": {
                "type": "textbox",
                "max_length": 75,
                "font": font3
            },

            "fps": {
                "type": "slider",
                "min": 30,
                "max": 240,
                "step": 10
            },

            "language": {
                "type": "select",
                "values": [
                    "Türkçe",
                    "English"
                ],
                "font": font3
            }
        }

        # ---------------------------------
        # ADLAR
        # ---------------------------------

        self.names = {
            "fullscreen": Lang(türkçe="Tam Ekran", english="Full Screen"),
            "music": Lang(türkçe="Müzik", english="Music"),
            "sfx": "SFX",
            "music_volume": Lang(türkçe="Müzik Sesi", english="Music Volume"),
            "sfx_volume": Lang(türkçe="SFX Sesi", english="SFX Volume"),
            "other_music": Lang(türkçe="Bilgisayardan Müzik", english="Music Path"),
            "fps": "FPS",
            "language": Lang(türkçe="Dil", english="Language")
        }

        self.active_textbox = None

        self.elements = {}

        self.create_elements()

        self.load()

    # =================================================
    # DEĞER İŞLEMLERİ
    # =================================================

    def get(self, name):
        return self.values[name]

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

    # =================================================
    # EVENT
    # =================================================

    def handle_event(self, event):

        for key, element in self.elements.items():

            element: SettingElement

            old_value = self.values[key]

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

                images = option.get("images", {})

                checked_image = self.load_image(
                    images.get("checked")
                )

                unchecked_image = self.load_image(
                    images.get("unchecked")
                )

                element = Checkbox(
                    (element_x, y),
                    checked_image,
                    unchecked_image
                )

            elif element_type == "slider":

                images = option.get("images", {})

                background_image = self.load_image(
                    images.get("background")
                )

                knob_image = self.load_image(
                    images.get("knob")
                )
                element = Slider(
                    (element_x, y),
                    option["min"],
                    option["max"],
                    option.get("step", 1),
                    background_image,
                    knob_image
                )

            elif element_type == "select":

                
    
                element = Select(
                    (element_x, y),
                    option["values"],
                    font=option["font"],
                )

                size_x = max(*(element.font.font.size(val)[0] for val in option["values"]))

                element.rect.width=(size_x + 20)

            elif element_type == "textbox":

                element = TextBox(
                    (element_x, y),
                    option.get("max_length", 20),
                    font=option.get("font", None)
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
