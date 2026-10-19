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
        # KARAKTER ANİMASYONU & ÖNBELLEK
        # ---------------------------------
        self.character_scale = 0.0
        self.character_animation_time = 0.0
        self.character_animation_duration = 0.25
        self.character_max_height = 430

        # Performans için önbellek değişkenleri
        self.cached_character: pygame.Surface | None = None
        self.cached_char_w: int = 0
        self.cached_char_h: int = 0

        # Panel önbelleği (her karede yeniden oluşturulmaz)
        self.panel_surface: pygame.Surface | None = None
        self.last_screen_size: tuple[int, int] = (0, 0)

        # ---------------------------------
        # OK İKONU ANİMASYONU
        # ---------------------------------
        self.arrow_time = 0.0

    @property
    def current_dialogue(self):
        if not self.dialogues:
            return None
        return self.dialogues[self.dialogue_index]

    def start(self):
        if not self.dialogues:
            self.finished = True
            return

        self.active = True
        self.finished = False
        self.dialogue_index = 0

        self._load_dialogue()

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

        # Karakter görselini sadece DİYALOG DEĞİŞTİĞİNDE 1 kez ölçeklendir
        self._prepare_character_cache(dialogue.image)

        self.character_scale = 0.0
        self.character_animation_time = 0.0

    def _prepare_character_cache(self, image: pygame.Surface | None):
        if image is None:
            self.cached_character = None
            return

        orig_w, orig_h = image.get_size()
        if orig_w <= 0 or orig_h <= 0:
            self.cached_character = None
            return

        scale = self.character_max_height / orig_h
        target_w = int(orig_w * scale)
        target_h = int(orig_h * scale)

        # Karakterin tam boyutu hafızaya alınıyor (Her karede smoothscale yapılmayacak)
        self.cached_character = pygame.transform.smoothscale(image, (target_w, target_h))
        self.cached_char_w = target_w
        self.cached_char_h = target_h

    def update(self, dt: float, volume=None, play=True):
        if not self.active:
            return

        if self.msgbox is not None:
            self.msgbox.update(dt, self.typing_sound, volume, play)

        # Karakter giriş animasyonu
        if self.character_scale < 1.0:
            self.character_animation_time += dt
            t = min(1.0, self.character_animation_time / self.character_animation_duration)
            self.character_scale = self._ease_out_back(t)
            if t >= 1.0:
                self.character_scale = 1.0

        self.arrow_time += dt

    @staticmethod
    def _ease_out_back(t: float):
        c1 = 1.70158
        c3 = c1 + 1
        return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2

    def handle_event(self, event: pygame.event.Event):
        if self.msgbox is None:
            return

        if (
            event.type == pygame.MOUSEBUTTONDOWN and
            event.button == 1 or
            event.type == pygame.KEYDOWN and
            event.key == pygame.K_SPACE
        ):

            if not self.msgbox.finished:
                self.msgbox.skip_typing()
                return

            self.next_dialogue()

    def next_dialogue(self):
        self.dialogue_index += 1
        if self.dialogue_index >= len(self.dialogues):
            self.finish()
            return
        self._load_dialogue()

    def finish(self):
        self.active = False
        self.finished = True
        self.msgbox = None
        self.cached_character = None

    def _update_layout(self, screen_w: int, screen_h: int):
        panel_y = screen_h - self.panel_height
        self.msgbox.x = (screen_w - self.msgbox.width) // 2
        self.msgbox.y = panel_y + (self.panel_height - self.msgbox.height) // 2

    def _draw_character(self, surface: pygame.Surface, screen_w: int, screen_h: int):
        if self.cached_character is None:
            return

        panel_y = screen_h - self.panel_height

        # Animasyon tamamlandıysa doğrudan önbellekteki görseli çiz (CPU yükü sıfır)
        if self.character_scale >= 1.0:
            draw_img = self.cached_character
            draw_w, draw_h = self.cached_char_w, self.cached_char_h
        else:
            # Sadece ilk 0.25 saniyelik yaylanma sırasında tek sefer ölçekle
            draw_w = max(1, int(self.cached_char_w * self.character_scale))
            draw_h = max(1, int(self.cached_char_h * self.character_scale))
            draw_img = pygame.transform.scale(self.cached_character, (draw_w, draw_h))

        x = (screen_w - draw_w) // 2
        y = panel_y - draw_h + 40
        surface.blit(draw_img, (x, y))

    def _draw_panel(self, surface: pygame.Surface, screen_w: int, screen_h: int):
        # Yüzeyi sadece ekran boyutu değiştiğinde veya ilk seferde oluştur
        if self.panel_surface is None or self.last_screen_size != (screen_w, screen_h):
            self.panel_surface = pygame.Surface((screen_w, self.panel_height), pygame.SRCALPHA)
            self.panel_surface.fill((*self.panel_color, self.panel_alpha))
            self.last_screen_size = (screen_w, screen_h)

        surface.blit(self.panel_surface, (0, screen_h - self.panel_height))

    def _draw_arrow(self, surface: pygame.Surface, screen_w: int, screen_h: int):
        if self.msgbox is None or not self.msgbox.finished:
            return

        offset = math.sin(self.arrow_time * 5) * 6
        x = screen_w - 40
        y = screen_h - 32 + offset

        points = [
            (x - 18, y - 8),
            (x + 18, y - 8),
            (x, y + 13)
        ]
        pygame.draw.polygon(surface, (255, 210, 0), points)

    def draw(self, surface: pygame.Surface):
        if not self.active or self.msgbox is None:
            return

        screen_w, screen_h = surface.get_size()

        self._update_layout(screen_w, screen_h)
        self._draw_character(surface, screen_w, screen_h)
        self._draw_panel(surface, screen_w, screen_h)
        self.msgbox.draw(surface)
        self._draw_arrow(surface, screen_w, screen_h)