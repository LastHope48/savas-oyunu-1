import math
from dataclasses import dataclass

import pygame

from dfont import MsgBox, DynamicFont

@dataclass
class SceneDialogue:
    speaker: str
    text: str
    image: pygame.Surface


class Scene:

    def __init__(
        self,
        font: DynamicFont,
        dialogues: list[SceneDialogue],
        msgbox_width: int = 900,
        msgbox_height: int = 240,
        panel_height: int = 330,
        panel_alpha: int = 175,
        panel_color: tuple[int, int, int] = (255, 255, 255),
        msgbox_color: tuple[int, int, int] = (255, 255, 255),
        msgbox_border: int = 10,
        msgbox_padding: int = 15,
        text_color: tuple[int, int, int] | str = "black",
        typing_speed: float = 10.0,
        typing_sound: pygame.mixer.Sound = None,
    ):
        self.font = font
        self.dialogues = dialogues

        self.msgbox_width = msgbox_width
        self.msgbox_height = msgbox_height

        self.panel_height = panel_height
        self.panel_alpha = panel_alpha
        self.panel_color = panel_color

        self.msgbox_color = msgbox_color
        self.msgbox_border = msgbox_border
        self.msgbox_padding = msgbox_padding
        self.text_color = text_color
        self.typing_speed = typing_speed

        self.typing_sound = typing_sound

        # ---------------------------------
        # DURUM
        # ---------------------------------

        self.active = False
        self.finished = False

        self.dialogue_index = 0
        self.msgbox = None

        # ---------------------------------
        # KARAKTER ANİMASYONU
        # ---------------------------------

        self.character_scale = 0.0
        self.character_animation_time = 0.0
        self.character_animation_duration = 0.25

        # ---------------------------------
        # OK İKONU ANİMASYONU
        # ---------------------------------

        self.arrow_time = 0.0

        # ---------------------------------
        # KARAKTER AYARLARI
        # ---------------------------------

        self.character_max_height = 430

    # =========================================================
    # CURRENT DIALOGUE
    # =========================================================

    @property
    def current_dialogue(self):
        if not self.dialogues:
            return None

        return self.dialogues[self.dialogue_index]

    # =========================================================
    # START
    # =========================================================

    def start(self):
        if not self.dialogues:
            self.finished = True
            return

        self.active = True
        self.finished = False
        self.dialogue_index = 0

        self._load_dialogue()

    # =========================================================
    # LOAD DIALOGUE
    # =========================================================

    def _load_dialogue(self):

        dialogue = self.current_dialogue

        self.msgbox = MsgBox(
            text=dialogue.text,
            font=self.font,
            width=self.msgbox_width,
            height=self.msgbox_height,
            x=0,
            y=0,
            color=self.msgbox_color,
            border=self.msgbox_border,
            padding=self.msgbox_padding,
            text_color=self.text_color,
            typing_speed=self.typing_speed
        )

        self.msgbox.start_typing()

        # Yeni karakter geldiğinde animasyon baştan başlar
        self.character_scale = 0.0
        self.character_animation_time = 0.0

    # =========================================================
    # UPDATE
    # =========================================================

    def update(self, dt: float):

        if not self.active:
            return

        # ---------------------------------
        # MSGBOX
        # ---------------------------------

        if self.msgbox is not None:
            self.msgbox.update(
                dt,
                self.typing_sound
            )

        # ---------------------------------
        # KARAKTER ANİMASYONU
        # ---------------------------------

        if self.character_scale < 1.0:

            self.character_animation_time += dt

            t = (
                self.character_animation_time
                / self.character_animation_duration
            )

            t = min(1.0, t)

            # Ease-out-back benzeri küçük "pop"
            self.character_scale = self._ease_out_back(t)

        # ---------------------------------
        # OK ANİMASYONU
        # ---------------------------------

        self.arrow_time += dt

    # =========================================================
    # CHARACTER EASE
    # =========================================================

    @staticmethod
    def _ease_out_back(t: float):

        c1 = 1.70158
        c3 = c1 + 1

        return (
            1
            + c3 * (t - 1) ** 3
            + c1 * (t - 1) ** 2
        )

    # =========================================================
    # EVENT
    # =========================================================

    def handle_event(self, event: pygame.event.Event):

        if not self.active:
            return

        if event.type != pygame.MOUSEBUTTONDOWN:
            return

        # Sadece sol tık
        if event.button != 1:
            return

        if self.msgbox is None:
            return

        # ---------------------------------
        # YAZI HALA YAZILIYORSA
        # ---------------------------------

        if not self.msgbox.finished:

            self.msgbox.skip_typing()

            return

        # ---------------------------------
        # YAZI BİTTİYSE
        # ---------------------------------

        self.next_dialogue()

    # =========================================================
    # NEXT DIALOGUE
    # =========================================================

    def next_dialogue(self):

        self.dialogue_index += 1

        # ---------------------------------
        # SCENE BİTTİ
        # ---------------------------------

        if self.dialogue_index >= len(self.dialogues):

            self.finish()

            return

        # ---------------------------------
        # YENİ DİYALOG
        # ---------------------------------

        self._load_dialogue()

    # =========================================================
    # FINISH
    # =========================================================

    def finish(self):

        self.active = False
        self.finished = True
        self.msgbox = None

    # =========================================================
    # LAYOUT
    # =========================================================

    def _update_layout(self, surface: pygame.Surface):

        screen_width, screen_height = surface.get_size()

        panel_y = screen_height - self.panel_height

        # MsgBox tam panelin ortasında
        self.msgbox.x = (
            screen_width - self.msgbox.width
        ) // 2

        self.msgbox.y = (
            panel_y
            + (self.panel_height - self.msgbox.height) // 2
        )

    # =========================================================
    # DRAW CHARACTER
    # =========================================================

    def _draw_character(self, surface: pygame.Surface):

        dialogue = self.current_dialogue

        if dialogue is None:
            return

        image = dialogue.image

        if image is None:
            return

        # ---------------------------------
        # Karakterin oranını koruyarak
        # maksimum yüksekliğini belirle
        # ---------------------------------

        original_width = image.get_width()
        original_height = image.get_height()

        if original_width <= 0 or original_height <= 0:
            return

        scale = (
            self.character_max_height
            / original_height
        )

        target_width = int(original_width * scale)
        target_height = int(original_height * scale)

        # Önce maksimum boyuta getir
        image = pygame.transform.smoothscale(
            image,
            (target_width, target_height)
        )

        # Sonra Scene animasyon scale'i
        animated_width = max(
            1,
            int(target_width * self.character_scale)
        )

        animated_height = max(
            1,
            int(target_height * self.character_scale)
        )

        image = pygame.transform.smoothscale(
            image,
            (animated_width, animated_height)
        )

        screen_width, screen_height = surface.get_size()

        # Karakter ekranın ortasında
        x = (
            screen_width - image.get_width()
        ) // 2

        # Panelin üstüne oturt
        panel_y = screen_height - self.panel_height

        y = (
            panel_y
            - image.get_height()
            + 40
        )

        surface.blit(
            image,
            (x, y)
        )

    # =========================================================
    # DRAW PANEL
    # =========================================================

    def _draw_panel(self, surface: pygame.Surface):

        screen_width, screen_height = surface.get_size()

        panel = pygame.Surface(
            (
                screen_width,
                self.panel_height
            ),
            pygame.SRCALPHA
        )

        panel.fill(
            (
                self.panel_color[0],
                self.panel_color[1],
                self.panel_color[2],
                self.panel_alpha
            )
        )

        surface.blit(
            panel,
            (
                0,
                screen_height - self.panel_height
            )
        )

    # =========================================================
    # DRAW ARROW
    # =========================================================

    def _draw_arrow(self, surface: pygame.Surface):

        if self.msgbox is None:
            return

        # Yazı henüz bitmediyse ok gösterme
        if not self.msgbox.finished:
            return

        screen_width, screen_height = surface.get_size()

        # Sürekli yukarı-aşağı hareket
        offset = math.sin(
            self.arrow_time * 5
        ) * 6

        x = screen_width - 40
        y = screen_height - 32 + offset

        points = [
            (x - 18, y - 8),
            (x + 18, y - 8),
            (x, y + 13)
        ]

        pygame.draw.polygon(
            surface,
            (255, 210, 0),
            points
        )

    # =========================================================
    # DRAW
    # =========================================================

    def draw(self, surface: pygame.Surface):

        if not self.active:
            return

        if self.msgbox is None:
            return

        # Ekran boyutuna göre yerleşimi güncelle
        self._update_layout(surface)

        # Karakter
        self._draw_character(surface)

        # Alt beyaz alan
        self._draw_panel(surface)

        # MsgBox
        self.msgbox.draw(surface)

        # Sarı ok
        self._draw_arrow(surface)