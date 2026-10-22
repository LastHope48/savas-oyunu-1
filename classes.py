import pygame
import colours
import os
import math
import random
from zaman import after
import copy
import uuid
import logging
from exceptions import EnemyPositionError, LevelPrepareError
from enum import Enum, auto
import _pickle
from cooldown import Cooldown
from helper_funcs import draw_aa_line
from screens.types import ScreenType
from userfont import userFont
from basedir import BASE_DIR
from val_manager import ValueManager
from animations import AnimationController
from sound_manager import SoundPoolFX, SoundFX
from lang_support import Lang
from dfont import DynamicFont
from combo_meter import ComboMeter
from enemy_telegraph import EnemyTelegraph
from settings import Settings
from calcs import scale, SCALE
import time
from collections import deque
from flags import *

from typing import Final, Literal


logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(filename)s: %(lineno)d [%(funcName)s] | %(message)s',
    level=logging.INFO,
    filename="game.log"
)

logger = logging.getLogger()
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
info = pygame.display.Info()


class LimitedNumber:
    def __init__(self, deger: float, minimum: float, maksimum: float):
        self.min = minimum
        self.max = maksimum
        self.deger = deger

    @property
    def deger(self):
        return self._deger

    @deger.setter
    def deger(self, yeni):
        self._deger = max(self.min, min(yeni, self.max))


class Slot:
    slots = []

    def __init__(self, id, display=None):
        self.id = id
        self.display = display
        self.display: Button

        self.used = False
        self.version = "Unknown"
        self.info = None
        self.unknown = False
        self.unusable = False
        self.corrupted = False
        self.slots.append(self)

    @classmethod
    def update_infos(cls, save_manager):
        infos = save_manager.get_all_infos()

        for slot in cls.slots:
            slot: Slot
            slot.info = infos.get(slot.id)

            slot.used = slot.info is not None

            try:
                save_manager.get_info(slot.id)
            except _pickle.UnpicklingError:
                slot.corrupted = True
            except EOFError:
                logging.warning(f"Slot {slot.id} caused EOFError.")
                slot.used = False

            except AttributeError:
                logging.warning(f"Slot {slot.id} caused AttributeError, the slot could be old.")
                slot.unusable = True

            except Exception as e:
                logging.error(e)
                slot.unknown = True

    @staticmethod
    def create_slots(save_manager, font):
        for i in range(70):
            # Zaten otomatik listeye ekliyor
            Slot(
                i,
                display=Button(
                            0, 0, 600, 200, f"Slot {i+1}",
                            font,
                            colours.BLUE,
                            colours.WHITE,
                            [ScreenType.LOAD, ScreenType.SAVE],
                            colours.darker(colours.BLUE, 20),
                            border_radius=5
                        )
            )
        Slot.update_infos(save_manager)

    @classmethod
    def delete_slots(cls):
        cls.slots.clear()


class AlignedRect:
    rects = []

    def __init__(self, x: int, y: int, width: int, height: int, font: userFont, color, text=None, text_color=None, on_mouse_color=None, border_radius=10, plus_data=None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rect = pygame.Rect(x-width//2, y-height//2, width, height)
        self.text = text or ""
        self.font = font
        self.color = color
        self.origin_color = color
        self.text_color = text_color
        self.on_mouse_color = on_mouse_color or colours.darker(color, 20)
        self.border_radius = border_radius
        self.clicking = False
        self.plus_data = plus_data
        self.rects.append(self)

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect, border_radius=self.border_radius)

        lines = self.text.splitlines()

        line_height = self.font.font.get_height()
        total_height = len(lines) * line_height

        y = self.rect.centery - total_height // 2

        for line in lines:
            text_surface = self.font.font.render(line, True, self.text_color)
            text_rect = text_surface.get_rect(center=(self.rect.centerx, y + line_height // 2))
            surface.blit(text_surface, text_rect)
            y += line_height

    def set_center(self, x, y):
        self.rect.center = (x, y)

    def set_topleft(self, x, y):
        self.rect.topleft = (x, y)

    def on_mouse(self):
        if self.clicking:
            return
        mouse_pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(mouse_pos):
            if self.on_mouse_color is not None:
                self.color = self.on_mouse_color
            return True
        else:
            self.color = self.origin_color
            return False


class Button:
    buttons = []

    def __init__(
            self,
            x: int,
            y: int,
            width: int,
            height: int,
            text,
            font: userFont | DynamicFont,
            color,
            text_color,
            game_state: list,
            on_mouse_color=None,
            on_click_color=None,
            border_radius=10,
            plus_data=None,
            design=None
        ):

        self.id = 0 if self.buttons == [] else self.buttons[-1].id + 1
        self.x = x
        self.y = y
        self.rect = pygame.Rect(x-width//2, y-height//2, width, height)

        self.text: str = text
        self.font = font
        self.color = color
        self.origin_color = color
        self.text_color = text_color
        self.on_mouse_color = on_mouse_color or colours.darker(color, 20)
        self.on_click_color = on_click_color or colours.darker(color, 50)
        self.border_radius = border_radius
        self.game_state = game_state
        self.plus_data = plus_data
        self.clicking = False
        self.design = design

    @property
    def width(self):
        return self.rect.width

    @width.setter
    def width(self, value):
        self.rect.width = value

    @property
    def height(self):
        return self.rect.height

    @height.setter
    def height(self, value):
        self.rect.height = value
            
    def clicked(self, event, state):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if state in self.game_state:
                if event.button == 1 and self.rect.collidepoint(event.pos):
                    self.clicking = True

                    if self.on_click_color is not None:
                        self.color = self.on_click_color

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.clicking:
                self.clicking = False

                if self.rect.collidepoint(event.pos):
                    if self.on_mouse_color is not None:
                        self.color = self.on_mouse_color
                    else:
                        self.color = self.origin_color
                    return True
                else:
                    self.color = self.origin_color

        return False

    def on_mouse(self):
        if self.clicking:
            return
        mouse_pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(mouse_pos):
            if self.on_mouse_color is not None:
                self.color = self.on_mouse_color
            return True
        else:
            self.color = self.origin_color
            return False

    def draw(self, surface: pygame.Surface):
        if self.design is None:
            pygame.draw.rect(surface, self.color, self.rect, border_radius=self.border_radius)

        elif self.design == "bevel":
            light = colours.lighter(self.color, 35)
            dark = colours.darker(self.color, 35)

            pygame.draw.rect(
                surface,
                dark,
                self.rect,
                border_radius=self.border_radius
            )

            inner_rect = self.rect.inflate(-6, -6)

            pygame.draw.rect(
                surface,
                self.color,
                inner_rect,
                border_radius=self.border_radius
            )

            pygame.draw.polygon(
                surface,
                light,
                [
                    self.rect.topleft,
                    self.rect.topright,
                    inner_rect.topright,
                    inner_rect.topleft
                ]
            )

            pygame.draw.polygon(
                surface,
                light,
                [
                    self.rect.topleft,
                    inner_rect.topleft,
                    inner_rect.bottomleft,
                    self.rect.bottomleft
                ]
            )

            pygame.draw.polygon(
                surface,
                dark,
                [
                    self.rect.bottomleft,
                    self.rect.bottomright,
                    inner_rect.bottomright,
                    inner_rect.bottomleft
                ]
            )

            pygame.draw.polygon(
                surface,
                dark,
                [
                    self.rect.topright,
                    self.rect.bottomright,
                    inner_rect.bottomright,
                    inner_rect.topright
                ]
            )
        

        if type(self.font) == userFont:
            lines = self.text.splitlines()

            line_height = self.font.font.get_height()
            total_height = len(lines) * line_height

            y = self.rect.centery - total_height // 2

            for line in lines:
                text_surface = self.font.font.render(line, True, self.text_color)
                text_rect = text_surface.get_rect(center=(self.rect.centerx, y + line_height // 2))
                surface.blit(text_surface, text_rect)
                y += line_height

        elif type(self.font) == DynamicFont:

            lines, line_height = self.font.render(
                self.text,
                self.text_color,
                self.rect,
                breaklines=True
            )

            total_height = len(lines) * line_height

            y = self.rect.centery - total_height // 2

            for line in lines:

                line: pygame.Surface
                text_rect = line.get_rect(center=(self.rect.centerx, y + line_height // 2))

                surface.blit(
                    line,
                    text_rect
                )
                
                y += line_height

    def set_center(self, x, y):
        self.rect.center = (x, y)

    def set_topleft(self, x, y):
        self.rect.topleft = (x, y)


class Music:
    def __init__(self, filename: str | os.PathLike, name: str | None = None):
        self.filename = filename
        self.name = name or self.filename

    def play(self, volume: float, loops: int = -1):
        pygame.mixer.music.load(self.filename)
        pygame.mixer.music.set_volume(volume)

        pygame.mixer.music.play(loops=loops)

    def __str__(self):
        return self.name


class InputBox:
    def __init__(self, x, y, width, height, color: tuple, font: userFont, waiting_font: userFont = None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rect = pygame.Rect(
            self.x,
            self.y,
            self.width,
            self.height
        )
        self.rect.midleft = (self.x, self.y)
        self.color = color
        self.text = ""
        self.active = False
        self.font = font
        self.waiting_font = waiting_font or font

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.key == 1:
                if self.rect.collidepoint(event.pos):
                    self.active = True
                else:
                    self.active = False
            else:
                self.active = False
        if self.active:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    self.text[-1]=""
                else:
                    if event.unicode.isprintable():
                        self.text += event.unicode

    def draw(self, surface: pygame.Surface):
        pygame.draw.rect(surface, self.color, self.rect, 3)
        self.font.draw_text(self.text, (self.x + 10, self.y), surface, colours.WHITE, hiza="midleft")
        

class MaterialFlags(Enum):
    WOODEN = auto()
    ROCK = auto()
    IRON = auto()
    BRONZE = auto()
    SILVER = auto()
    GOLDEN = auto()
    DIAMOND = auto()
    OTHER = auto()
    SPECIAL = auto()

material_order = {
        MaterialFlags.WOODEN: 1,
        MaterialFlags.ROCK: 2,
        MaterialFlags.IRON: 3,
        MaterialFlags.BRONZE: 4,
        MaterialFlags.SILVER: 5,
        MaterialFlags.GOLDEN: 6,
        MaterialFlags.DIAMOND: 7,
        MaterialFlags.OTHER: 8,
        MaterialFlags.SPECIAL: 9
}


class Sword:
    def __init__(self, name: str, attack: int, color: tuple, dash_speed, material):
        self.name = name
        self.attack = attack
        self.material = material
        self.color = color
        self.dash_speed = dash_speed

        # -------------------------------------------------------------
        # KILIÇ İZİ (PROCEDURAL RIBBON TRAIL) AYARLARI
        # -------------------------------------------------------------
        # Her eleman: ((tip_x, tip_y), (base_x, base_y), olusturma_zamani)
        self.trail_points = deque()
        self.trail_lifetime = 0.14       # İzin ekranda kalma süresi (sn)
        self.min_tip_dist = 4.0 * SCALE  # Hareketsizken boşuna nokta eklememe eşiği
        self.trail_enabled = True        # İstenirse sadece saldırıda açılabilir

    def clear_trail(self):
        """Karakter ışınlandığında veya animasyon aniden değiştiğinde izi sıfırlar."""
        self.trail_points.clear()

    def _draw_trail(self, surface: pygame.Surface, now: float):
        """Son karelerdeki koordinatları birleştirip neon ışık şeridi oluşturur."""
        if len(self.trail_points) < 2:
            return

        # 1. Bounding Box (Kapsayıcı Alan) Tespiti
        # Tüm ekran boyutunda yüzey açıp FPS düşürmemek için sadece izin kapladığı alanı hesaplıyoruz
        all_points = []
        for p in self.trail_points:
            all_points.append(p[0])
            all_points.append(p[1])

        min_x = min(pt[0] for pt in all_points) - 4
        max_x = max(pt[0] for pt in all_points) + 4
        min_y = min(pt[1] for pt in all_points) - 4
        max_y = max(pt[1] for pt in all_points) + 4

        surf_w = int(max_x - min_x)
        surf_h = int(max_y - min_y)

        if surf_w <= 0 or surf_h <= 0:
            return

        # Sadece izin kapladığı küçük şeffaf yüzey (60+ FPS dostu)
        trail_surf = pygame.Surface((surf_w, surf_h), pygame.SRCALPHA)

        # 2. Şerit Poligonlarını (Mesh) Sırayla Çiz
        pts = list(self.trail_points)
        num_segments = len(pts) - 1

        for i in range(num_segments):
            p_curr = pts[i]      # Daha yeni nokta
            p_next = pts[i + 1]  # Daha eski nokta

            # Noktanın ömrüne göre yumuşak sönümleme (Fade Out)
            age = now - p_next[2]
            progress = min(1.0, max(0.0, age / self.trail_lifetime))
            alpha = int(190 * (1.0 - progress))  # 190 -> 0

            if alpha <= 0:
                continue

            # Koordinatları yerel trail_surf koordinatına ötele
            tip1 = (p_curr[0][0] - min_x, p_curr[0][1] - min_y)
            base1 = (p_curr[1][0] - min_x, p_curr[1][1] - min_y)
            tip2 = (p_next[0][0] - min_x, p_next[0][1] - min_y)
            base2 = (p_next[1][0] - min_x, p_next[1][1] - min_y)
            
            quad = [tip1, tip2, base2, base1]

            # A) Neon Gövde (Kılıcın kendi renginde saydam dalga)
            trail_color = (*self.color[:3], alpha)
            pygame.draw.polygon(trail_surf, trail_color, quad)

            # B) Keskin Dış Kenar Işıltısı (Kılıcın ucuna vuran parlak hat)
            core_alpha = int(240 * (1.0 - progress))
            pygame.draw.line(trail_surf, (255, 255, 255, core_alpha), tip1, tip2, max(1, int(2 * SCALE)))

        # 3. İzi ana ekrana bas (Kılıcın arkasında kalır)
        surface.blit(trail_surf, (min_x, min_y), special_flags=pygame.BLEND_ALPHA_SDL2)

    def draw(self, surface: pygame.Surface, x: float, y: float, angle: float, scale_factor: float = 1.0, trail=True):
        # -------------------------------------------------------------
        # 1. GEOMETRİ HESAPLAMALARI
        # -------------------------------------------------------------
        effective_scale = SCALE * scale_factor
        blade_length = 55 * effective_scale
        blade_width = 8 * effective_scale
        handle_length = 16 * effective_scale
        guard_width = 22 * effective_scale

        rad = math.radians(angle)
        dx = math.cos(rad)
        dy = math.sin(rad)

        px = -dy
        py = dx

        # Bıçak ucu ve kabza başlangıcı
        tip_x = x + dx * blade_length
        tip_y = y + dy * blade_length
        base_x = x + dx * (blade_length * 0.15)  # İzin başladığı kabza önü
        base_y = y + dy * (blade_length * 0.15)

        # -------------------------------------------------------------
        # 2. İZ NOKTALARINI GÜNCELLE VE ESKİYENLERİ SİL
        # -------------------------------------------------------------
        now = time.time()

        # Süresi dolan (self.trail_lifetime'dan eski) noktaları kuyruktan at
        while self.trail_points and (now - self.trail_points[-1][2] > self.trail_lifetime):
            self.trail_points.pop()

        # Sadece kılıç gerçekten hareket ettiğinde yeni nokta ekle (hareketsizken kasmaması için)
        should_add = True
        if self.trail_points:
            last_tip = self.trail_points[0][0]
            dist = math.hypot(tip_x - last_tip[0], tip_y - last_tip[1])
            if dist < self.min_tip_dist:
                should_add = False

        if self.trail_enabled and should_add:
            self.trail_points.appendleft(((tip_x, tip_y), (base_x, base_y), now))

        # -------------------------------------------------------------
        # 3. ÖNCE İZİ ÇİZ (Kılıcın Arkasında Kalsın)
        # -------------------------------------------------------------
        if trail:
            self._draw_trail(surface, now)

        # -------------------------------------------------------------
        # 4. KILICIN KENDİSİNİ ÇİZ
        # -------------------------------------------------------------
        blade = [
            (x + px * blade_width / 2, y + py * blade_width / 2),
            (x - px * blade_width / 2, y - py * blade_width / 2),
            (tip_x - px * blade_width / 2, tip_y - py * blade_width / 2),
            (tip_x, tip_y),
            (tip_x + px * blade_width / 2, tip_y + py * blade_width / 2)
        ]

        # Bıçak Gövdesi
        pygame.draw.polygon(surface, self.color, blade)

        # Bıçak Orta Işık Çizgisi (Neon derinlik)
        pygame.draw.line(surface, (255, 255, 255), (x, y), (tip_x, tip_y), max(1, int(1.5 * effective_scale)))

        # Kabza (Geriye uzanan ahşap sap)
        handle_x = x - dx * handle_length
        handle_y = y - dy * handle_length
        pygame.draw.line(surface, (110, 70, 30), (x, y), (handle_x, handle_y), int(6 * effective_scale))

        # El koruması (Guard - Altın sarısı)
        pygame.draw.line(
            surface,
            (255, 215, 0),
            (x + px * guard_width / 2, y + py * guard_width / 2),
            (x - px * guard_width / 2, y - py * guard_width / 2),
            max(2, int(5 * effective_scale))
        )

        # Kabza ucu (Pommel)
        pygame.draw.circle(surface, (180, 180, 180), (int(handle_x), int(handle_y)), int(4 * effective_scale))


class CyberKatana(Sword):
    """
    Özel nadir kılıç: Katana tarzı örgülü kabza (tsuka-ito), 
    açılı aerodinamik koruma (tsuba), prizmatik güç kristali ve iki tonlu neon bıçak.
    """
    def __init__(self, name="Aether Katana", attack=120, color=(0, 220, 255), dash_speed=1100, material="crystal"):
        super().__init__(name, attack, color, dash_speed, material)
        # Özel kılıcın izi biraz daha uzun ve daha yoğun neon kalsın
        self.trail_lifetime = 0.18

    def draw(self, surface: pygame.Surface, x: float, y: float, angle: float, scale_factor: float = 1.0, trail=True):
        effective_scale = SCALE * scale_factor

        # -------------------------------------------------------------
        # 1. BOYUT VE VEKTÖR HESAPLAMALARI
        # -------------------------------------------------------------
        # Normal kılıçtan daha uzun ve daha ince, jilet gibi bir profil
        blade_length = 72 * effective_scale
        blade_width = 7 * effective_scale
        handle_length = 22 * effective_scale
        guard_width = 24 * effective_scale

        rad = math.radians(angle)
        dx = math.cos(rad)
        dy = math.sin(rad)

        # Teğet (dik) vektör
        px = -dy
        py = dx

        # Kritik Noktalar
        tip_x = x + dx * blade_length
        tip_y = y + dy * blade_length
        base_x = x + dx * (blade_length * 0.12)
        base_y = y + dy * (blade_length * 0.12)

        # -------------------------------------------------------------
        # 2. İZ (TRAIL) GÜNCELLEMESİ
        # -------------------------------------------------------------
        now = time.time()
        while self.trail_points and (now - self.trail_points[-1][2] > self.trail_lifetime):
            self.trail_points.pop()

        should_add = True
        if self.trail_points:
            last_tip = self.trail_points[0][0]
            dist = math.hypot(tip_x - last_tip[0], tip_y - last_tip[1])
            if dist < self.min_tip_dist:
                should_add = False

        if self.trail_enabled and should_add:
            self.trail_points.appendleft(((tip_x, tip_y), (base_x, base_y), now))

        # Kılıcın arkasındaki şerit izi çiz
        if trail:
            self._draw_trail(surface, now)

        # -------------------------------------------------------------
        # 3. KABZA (TSUKA) VE KATANA ÖRGÜSÜ (TSUKA-ITO)
        # -------------------------------------------------------------
        handle_end_x = x - dx * handle_length
        handle_end_y = y - dy * handle_length

        # Kabza ana gövdesi (Koyu karbon/titanyum altlık)
        pygame.draw.line(
            surface,
            (15, 20, 28),
            (x, y),
            (handle_end_x, handle_end_y),
            max(2, int(6 * effective_scale))
        )

        # Katana Baklava Çapraz Örgüleri (Tsuka-ito dokusu)
        wrap_segments = 4
        for i in range(wrap_segments):
            t = (i + 0.5) / wrap_segments
            wx = x - dx * (handle_length * t)
            wy = y - dy * (handle_length * t)
            offset = 3 * effective_scale

            # Çapraz bağcık dikişleri (Açık camgöbeği/gümüş bağcık)
            pygame.draw.line(
                surface,
                (0, 180, 220),
                (wx + px * offset, wy + py * offset),
                (wx - px * offset, wy - py * offset),
                max(1, int(1.5 * effective_scale))
            )
            pygame.draw.circle(
                surface,
                (220, 245, 255),
                (int(wx), int(wy)),
                max(1, int(1.2 * effective_scale))
            )

        # -------------------------------------------------------------
        # 4. KABZA UCU (KASHIRA / POMMEL)
        # -------------------------------------------------------------
        # Düz daire yerine sivri köşeli prizmatik uçluk
        kashira_w = 4 * effective_scale
        kashira_h = 5 * effective_scale
        kashira_pts = [
            (handle_end_x + px * kashira_w, handle_end_y + py * kashira_w),
            (handle_end_x - px * kashira_w, handle_end_y - py * kashira_w),
            (handle_end_x - dx * kashira_h, handle_end_y - dy * kashira_h)
        ]
        pygame.draw.polygon(surface, (30, 42, 58), kashira_pts)
        pygame.draw.polygon(surface, (0, 240, 255), kashira_pts, max(1, int(1 * effective_scale)))

        # -------------------------------------------------------------
        # 5. BIÇAK GÖVDESİ (ÇİFT TONLU JİLET KESKİNLİK)
        # -------------------------------------------------------------
        tanto_tip_x = tip_x - dx * (6 * effective_scale)
        tanto_tip_y = tip_y - dy * (6 * effective_scale)

        # Sırt (koyu çelik gövde) ve ağız (parlak neon kesici kenar)
        edge_pts = [
            (x + px * blade_width / 2, y + py * blade_width / 2),
            (tanto_tip_x + px * blade_width / 2, tanto_tip_y + py * blade_width / 2),
            (tip_x, tip_y),
            (x, y)
        ]
        spine_pts = [
            (x - px * blade_width / 2, y - py * blade_width / 2),
            (tanto_tip_x - px * blade_width / 2, tanto_tip_y - py * blade_width / 2),
            (tip_x, tip_y),
            (x, y)
        ]

        # Alt gövde: Derin Gece Mavisi (Kraliyet altını yerine asil karanlık çelik)
        pygame.draw.polygon(surface, (12, 32, 60), spine_pts)
        # Keskin kenar: Canlı Siber Camgöbeği
        pygame.draw.polygon(surface, (0, 160, 240), edge_pts)

        # Dış keskin kontur çizgisi
        pygame.draw.lines(
            surface,
            (180, 245, 255),
            False,
            [
                (x + px * blade_width / 2, y + py * blade_width / 2),
                (tanto_tip_x + px * blade_width / 2, tanto_tip_y + py * blade_width / 2),
                (tip_x, tip_y)
            ],
            max(1, int(1.5 * effective_scale))
        )

        # Omurga Işıltısı (Fuller / Kan oluğu boyunca uzanan beyaz foton çizgisi)
        pygame.draw.line(
            surface,
            (240, 255, 255),
            (x + dx * 10 * effective_scale, y + dy * 10 * effective_scale),
            (tanto_tip_x, tanto_tip_y),
            max(1, int(1.2 * effective_scale))
        )

        # -------------------------------------------------------------
        # 6. SİBER EL KORUMASI (KANATLI TSUBA)
        # -------------------------------------------------------------
        # Düz çizgi yerine ileriye doğru hafif eğimli aerodinamik siber kanatlar
        wing_fwd = 5 * effective_scale
        guard_poly = [
            (x, y - dy * 2),
            (x + px * guard_width / 2 + dx * wing_fwd, y + py * guard_width / 2 + dy * wing_fwd),
            (x + px * (guard_width / 2 + 3 * effective_scale), y + py * (guard_width / 2 + 3 * effective_scale)),
            (x, y + dy * 3),
            (x - px * (guard_width / 2 + 3 * effective_scale), y - py * (guard_width / 2 + 3 * effective_scale)),
            (x - px * guard_width / 2 + dx * wing_fwd, y - py * guard_width / 2 + dy * wing_fwd),
        ]
        # Titanyum guard gövdesi
        pygame.draw.polygon(surface, (20, 28, 40), guard_poly)
        # Neon cyan dış çerçeve
        pygame.draw.polygon(surface, (0, 240, 255), guard_poly, max(1, int(1.5 * effective_scale)))

        # -------------------------------------------------------------
        # 7. NADİR GÜÇ KRİSTALİ (PRİZMATİK ELMAS ÇEKİRDEK)
        # -------------------------------------------------------------
        # Bıçağın hemen başlangıç yuvasında ışıldayan geometrik mineral
        gem_cx = x + dx * (8 * effective_scale)
        gem_cy = y + dy * (8 * effective_scale)
        gem_h = 6 * effective_scale
        gem_w = 4 * effective_scale

        # Kristal Yuvası (Koyu gölge çerçeve)
        socket_rect = [
            (gem_cx + dx * (gem_h + 1), gem_cy + dy * (gem_h + 1)),
            (gem_cx + px * (gem_w + 1), gem_cy + py * (gem_w + 1)),
            (gem_cx - dx * (gem_h + 1), gem_cy - dy * (gem_h + 1)),
            (gem_cx - px * (gem_w + 1), gem_cy - py * (gem_w + 1)),
        ]
        pygame.draw.polygon(surface, (10, 14, 22), socket_rect)

        # Kristal Gövdesi (Koyu Safir)
        gem_facets = [
            (gem_cx + dx * gem_h, gem_cy + dy * gem_h),
            (gem_cx + px * gem_w, gem_cy + py * gem_w),
            (gem_cx - dx * gem_h, gem_cy - dy * gem_h),
            (gem_cx - px * gem_w, gem_cy - py * gem_w),
        ]
        pygame.draw.polygon(surface, (0, 110, 220), gem_facets)

        # İç Işık Çekirdeği (Yoğun Cyan)
        inner_h = gem_h * 0.55
        inner_w = gem_w * 0.55
        inner_facets = [
            (gem_cx + dx * inner_h, gem_cy + dy * inner_h),
            (gem_cx + px * inner_w, gem_cy + py * inner_w),
            (gem_cx - dx * inner_h, gem_cy - dy * inner_h),
            (gem_cx - px * inner_w, gem_cy - py * inner_w),
        ]
        pygame.draw.polygon(surface, (0, 245, 255), inner_facets)

        # Kristal Parıltı Noktası (Beyaz Speküler Işık)
        pygame.draw.circle(
            surface,
            (255, 255, 255),
            (int(gem_cx + px * (inner_w * 0.3)), int(gem_cy + py * (inner_w * 0.3))),
            max(1, int(1.2 * effective_scale))
        )


class SwapValue:
    def __init__(self, value=None):
        self.value = value


class Charm:
    def __init__(self, name: str, image_name: str | os.PathLike, image_size, passive_effects: list, active_effects: list, cooldown: int):
        self.name = name
        self.image_name = image_name
        self.image_r = pygame.image.load(self.image_name)
        self.image_l = pygame.image.load(self.image_name.replace(f"r.{self.image_name.split('.')[-1]}", f"l.{self.image_name.split('.')[-1]}"))

        self.image_size = image_size
        self.image_r = pygame.transform.scale_by(self.image_r, image_size)
        self.image_l = pygame.transform.scale_by(self.image_l, image_size)

        self.image = self.image_r

        self.passive_effects = passive_effects
        self.active_effects = active_effects
        self.or_cooldown = cooldown
        self.cooldown = cooldown
        self.used = False
        self.texts = []
        self.effected = False
        self.old_player = None

    def draw(self, surface: pygame.Surface, x: int, y: int):
        for text in self.texts:
            text: dict
            rendered = text["font"].return_text(text["text"], colours.darker(colours.GREEN, 130))
            rendered: pygame.Surface
            rendered.set_alpha(text["progress"])
            surface.blit(rendered, text["pos"])
        surface.blit(self.image, (x, y))

    def update(self, angle, dt):
        if angle < 45 and angle > -45:
            self.image = self.image_r

        if angle < 180 and angle < -135 or angle < 180 and angle > 135:
            self.image = self.image_l

        for text in self.texts:
            text: dict
            text["pos"].y -= 80 * dt
            if text["progress"] - dt * 63.75 > 0:
                text["progress"] -= dt * 63.75
            else:
                self.texts.remove(text)
            

    def copy(self):
        return copy.deepcopy(self)

    def equip(self, player):
        self.old_values = {}

        for effect in self.passive_effects:
            attribute = effect.effect_appending

            if attribute is not None:
                self.old_values[attribute] = getattr(player, attribute)

            effect.use(player, ())

        self.effected = True

    def unequip(self, player):
        if not self.effected:
            return

        for attribute, old_value in self.old_values.items():
            setattr(player, attribute, old_value)

        self.old_values.clear()
        self.effected = False

    def draw_copy(self, surface: pygame.Surface, x: int, y: int):
        surface.blit(self.image, (x, y))

    def use_active(self, player, dt):
        player: Player
        self.cooldown -= dt
        pos = pygame.mouse.get_pos()
        if pygame.mouse.get_pressed()[0] and self.cooldown <= 0:
            for effect in self.active_effects:
                effect: Effect
                effect.use(player, ())

            self.texts.append(
                {
                    "text": f"{'+' if Item.APPENDER in effect.flags else '-'}{effect.effect}{effect.effect_appending}",
                    "pos": pygame.Vector2(pos[0], pos[1]),
                    "progress": 255,
                    "font": userFont("arial", 50),
                    "font_conf": {"name": "arial", "size": 50}
                }
            )
            self.cooldown = self.or_cooldown

    def __getstate__(self):
        state = self.__dict__.copy()

        del state["image"]
        del state["image_r"]
        del state["image_l"]

        state["texts"] = []

        for text in self.texts:
            text_copy = text.copy()

            text_copy["font"] = None

            state["texts"].append(text_copy)

        return state

    def __setstate__(self, state):
        self.__dict__.update(state)

        self.image_r = pygame.image.load(self.image_name)
        self.image_l = pygame.image.load(self.image_name.replace(f"r.{self.image_name.split('.')[-1]}", f"l.{self.image_name.split('.')[-1]}"))

        self.image_size = self.image_size
        self.image_r = pygame.transform.scale_by(self.image_r, self.image_size)
        self.image_l = pygame.transform.scale_by(self.image_l, self.image_size)

        self.image = self.image_r

        for text in self.texts:
            text["font"] = userFont(
                text["font_conf"]["name"],
                text["font_conf"]["size"]
            )


class Bullet:
    def __init__(
        self,
        x, y,
        image_name: str,
        attack: int,
        speed,
        mx, my,
        range: float | int | None,
        material: str
    ):
        self.x = x
        self.y = y

        self.image_name = image_name
        self.image = pygame.image.load(self.image_name).convert_alpha()

        self.angle = 360
        self.speed = speed

        self.rotated = None
        self.rotated_rect = None

        self.attack = attack
        self.material = material

        range_map = {
            MaterialFlags.BRONZE: 800,
            MaterialFlags.SILVER: 1200,
            "__deflected__": 100_000
        }


        self.range = range or range_map[material]
        self.travelled = 0

        self.mx = mx
        self.my = my

        self.deleted = False

        # Mouse yönünü hesapla
        dx = mx - x
        dy = my - y

        length = math.hypot(dx, dy)

        if length != 0:
            self.dir_x = dx / length
            self.dir_y = dy / length
        else:
            self.dir_x = 0
            self.dir_y = 0
    
    def get_mouse_pos(self):
        self.mx, self.my = pygame.mouse.get_pos()

    def update(self, world, dt, enemies: list, player=None, gun_combo=False):
        if self.mx is not None and self.my is not None:
            self.dx = self.mx - self.x
            self.dy = self.my - self.y
            self.angle = math.degrees(math.atan2(-self.dy, self.dx))

            self.image_rect = self.image.get_rect(center=(self.x, self.y))
            rect = self.rotated_rect or self.image_rect

            rect.topleft = (self.x, self.y)

            move_distance = self.speed * dt

            remaining = self.range - self.travelled

            if move_distance >= remaining:
                self.x += self.dir_x * remaining
                self.y += self.dir_y * remaining
                self.travelled = self.range
                self.deleted = True
            else:
                if rect.collidelist(world.rocks_rects) == -1:
                    self.x += self.dir_x * move_distance
                    self.y += self.dir_y * move_distance
                    self.travelled += move_distance
                else:
                    self.deleted = True

            for enemy in enemies:
                enemy: Enemy

                if rect.colliderect(enemy.image_rect) and enemy.living:
                    if Enemy.DAMAGE_BULLET in enemy.damagables or self.material == "__deflected__":
                        enemy.hp -= self.attack
                    else:
                        if (
                            Enemy.DAMAGE_BRONZE_BULLET in enemy.damagables
                            and self.material == MaterialFlags.BRONZE
                        ) or (
                            Enemy.DAMAGE_SILVER_BULLET in enemy.damagables
                            and self.material == MaterialFlags.SILVER
                        ):
                            enemy.hp -= self.attack

                    self.deleted = True

                    if gun_combo:
                        if getattr(player, "combo_meter", None):
                            player.combo_meter.add_hit(count=1, swidth=info.current_w, sheight=info.current_h) # Kombo + 1
                    break

                if self.material != "__deflected__":
                    # Doğrudan listeyi gezmek yerine temas eden varsa kır
                    for arrow in list(enemy.arrows):
                        arrow_rect = arrow.rotated_rect or arrow.image_rect
                        if rect.colliderect(arrow_rect):
                            enemy.arrows.remove(arrow)
                            self.deleted = True
                            break

            self.rotated = pygame.transform.rotate(self.image, self.angle)
            self.rotated_rect = self.rotated.get_rect(center=(self.x, self.y))
    
    def draw(self, surface: pygame.Surface):
        if self.rotated is not None:
            surface.blit(self.rotated, self.rotated_rect)
        else:
            surface.blit(self.image, (self.x, self.y))
    
    def __getstate__(self):
        state = self.__dict__.copy()
        del state["image"]
        del state["rotated"]
        return state
    
    def __setstate__(self, state):
        self.__dict__.update(state)
        self.image = pygame.image.load(self.image_name).convert_alpha()
        self.rotated = None


class Gun:
    def __init__(self, name: str, color: tuple, attack: int, bullet_speed: int, image_name: os.PathLike, bullet_name: os.PathLike, cooldown: int, material, img_size: float=1.0):
        self.name = name
        self.color = color
        self.attack = attack
        self.bullet_speed = bullet_speed
        self.image_name = image_name
        self.image_size = img_size

        image = pygame.image.load(self.image_name)
        self.image = pygame.transform.scale_by(image, 0.5)
        self.image = pygame.transform.scale_by(self.image, self.image_size)
        self.bullet_name = bullet_name
        self.bullets = []
        self.rotated = None
        self.rotated_rect = None
        self.dash_duration = Cooldown(0.3)
        self.angle = 360
        self.x = None
        self.y = None
        self.origin_cooldown = cooldown
        self.cooldown = self.origin_cooldown
        self.dashing = False
        self.material = material

    def draw(self, surface: pygame.Surface, x: int, y: int):
        self.x = x
        self.y = y
        if self.rotated_rect is None and self.rotated is None:
            surface.blit(self.image, (x, y))
        else:
            surface.blit(self.rotated, self.rotated_rect)
        # if angle < 90 and angle > -90:
        #     self.image_name: str
        #     self.image_name = self.image_name.replace("l.png", "r.png")
        # else:
        #     self.image_name = self.image_name.replace("r.png", "l.png")

        for bullet in self.bullets:
            bullet: Bullet
            bullet.draw(surface)
    
    def draw_copy(self, surface: pygame.Surface, x: int, y: int):
        surface.blit(self.image, (x, y))
    
    def update(self, world, dt, enemies: list, player, gun_combo=False):
        self.cooldown -= dt
        self.dash_duration.reduce(dt)

        if self.dash_duration.check():
            self.dashing = False
            player.drawing = False
            player.old_x = None
            player.old_y = None

        world: World
        mx, my = pygame.mouse.get_pos()
        if self.x is not None:
            dx, dy = mx - self.x, my - self.y
        else:
            return
        for bullet in self.bullets:
            bullet: Bullet
            bullet.update(world, dt, enemies, player, gun_combo)
            if bullet.deleted:
                self.bullets.remove(bullet)
        if not self.dashing:
            self.angle = math.degrees(math.atan2(-dy, dx))
        self.rotated = pygame.transform.rotate(self.image, self.angle)
        self.rotated_rect = self.rotated.get_rect(center=(self.x, self.y))

    def fire(self):
        if self.cooldown <= 0:
            if self.x is not None:
                self.bullets.append(
                    Bullet(
                        self.x,
                        self.y,
                        self.bullet_name,
                        self.attack,
                        self.bullet_speed,
                        pygame.mouse.get_pos()[0],
                        pygame.mouse.get_pos()[1],
                        None,
                        self.material
                    )
                )
            self.cooldown = self.origin_cooldown
    
    def dash_attack(self, player):
        player: Player

        if self.x is None: return

        mx, my = pygame.mouse.get_pos()
        dx, dy = mx - self.x, my - self.y
        self.angle = math.degrees(math.atan2(-dy, dx))
        self.dashing = True
        # if self.x is not None:
        #     if self.angle < 90 and self.angle > -90:
        #         self.angle = -90
        #     else:
        #        self.angle = 180
        self.angle = -90
        player.speed = player.speed_max + 130
        self.dash_duration.refresh()
        player.drawing = True
        self.rotated = pygame.transform.rotate(self.image, self.angle)
        self.rotated_rect = self.rotated.get_rect(center=(self.x, self.y))

    def __getstate__(self):
        state = self.__dict__.copy()

        del state["image"]
        if self.__dict__.get("rotated"):
            del state["rotated"]

        return state
    
    def __setstate__(self, state):
        self.__dict__.update(state)

        image = pygame.image.load(self.image_name)
        self.image = pygame.transform.scale(image, (image.get_width() / 2, image.get_height() / 2))
        self.image = pygame.transform.scale_by(self.image, self.image_size)
        self.rotated = None
        self.rotated_rect = None


class Effect:
    def __init__(self, effect_appending, effect, seconds: int, append_to_list: list=None, appending=[], flags: tuple = ()):
        self.effect = effect
        self.effect_appending = effect_appending
        self.append_to_list = append_to_list
        self.appending = appending
        self.seconds = seconds
        self.flags = flags
    
    def use_global(self, flags, varlik):
        if self.append_to_list is None:
            try:
                if Item.APPENDER in flags:
                    if self.seconds <= 0:
                        setattr(varlik, self.effect_appending, getattr(varlik, self.effect_appending)+self.effect)
                    else:
                        after(setattr, varlik, self.effect_appending, getattr(varlik, self.effect_appending)+self.effect, secs=self.seconds)
                if Item.EQUALER in flags:
                    if self.seconds <= 0:
                        setattr(varlik, self.effect_appending, self.effect)
                    else:
                        after(setattr, varlik, self.effect_appending, self.effect, secs=self.seconds)
                if Item.REDUCER in flags:
                    if self.seconds <= 0:
                        setattr(varlik, self.effect_appending, getattr(varlik, self.effect_appending)-self.effect)
                    else:
                        after(setattr, varlik, self.effect_appending, getattr(varlik, self.effect_appending)-self.effect, secs=self.seconds)
            except AttributeError:
                print(f"No attribute {self.effect_appending} in {varlik}")
        
        else:
            for append in self.appending:
                self.append_to_list.append(append)
    
    def use(self, player, flags):
        player: Player
        if self.append_to_list is None:
            if Item.APPENDER in flags or Item.APPENDER in self.flags:
                if self.seconds <= 0:
                    setattr(player, self.effect_appending, min(getattr(player, self.effect_appending)+self.effect, player.max_hp))
                else:
                    after(setattr, player, self.effect_appending, min(getattr(player, self.effect_appending)+self.effect, player.max_hp), secs=self.seconds)
            if Item.EQUALER in flags or Item.EQUALER in self.flags:
                if self.seconds <= 0:
                    setattr(player, self.effect_appending, self.effect)
                else:
                    after(setattr, player, self.effect_appending, self.effect, secs=self.seconds)
            if Item.REDUCER in flags or Item.REDUCER in self.flags:
                if self.seconds <= 0:
                    setattr(player, self.effect_appending, min(getattr(player, self.effect_appending)-self.effect, player.max_hp))
                else:
                    after(setattr, player, self.effect_appending, min(getattr(player, self.effect_appending)-self.effect, player.max_hp), secs=self.seconds)
        else:
            for append in self.appending:
                self.append_to_list.append(append)

    def copy(self):
        return copy.deepcopy(self)


class Item:
    APPENDER = 1
    EQUALER = 2
    REDUCER = 3
    YUVARLAK_IKSIR = 4
    TUP_IKSIR = 5

    def __init__(self, name: str, color: tuple, effects: list, *flags, pickable=None, font=None):
        self.x = 0
        self.y = 0
        self.rect = None
        self.name = name
        self.color = color
        self.effects = effects
        self.flags = flags
        self.used = False
        self.pickable = pickable or True if self.YUVARLAK_IKSIR in self.flags else False
        self.picked = False
        self.touching = False
        self.drag_to_player = True
        self.mouse_getted = False
        self.effect_rect = None
        self.font = font
        self.use_timer_started = False

        if self.font is not None:
            self.font_name = self.font.name
            self.font_size = self.font.size
            self.font: userFont

        if self.YUVARLAK_IKSIR in self.flags:
            self.speed = 900

        self.show_text = False
    
    def set_pos(self, world):
        count = 0

        while True:
            count += 1

            if count > 50:
                print("ITEM YER BULAMADI", self.name)
                return

            self.x = random.randint(200, info.current_w - 200)
            self.y = random.randint(200, info.current_h - 200)

            self.rect = pygame.Rect(self.x, self.y, 20, 50)

            if self.rect.collidelist(world.rocks_rects) == -1 and not world.dirt_rect.colliderect(self.rect):
                break

    def draw(self, surface: pygame.surface.Surface, font: userFont, player):
        if self.used:
            return

        # -------------------------------------------------------------
        # 0. YAZI GÖSTERİM KONTROLÜ (Hover veya Yakınlık)
        # -------------------------------------------------------------
        if not self.picked:
            # İksirin türüne göre merkez noktası
            if self.y is None or self.x is None or self.rect is None: return
            item_cx = self.x + 10 if Item.TUP_IKSIR in self.flags else self.x
            item_cy = self.y + 25 if Item.TUP_IKSIR in self.flags else self.y

            # 1. Fare iksirin üzerinde mi?
            mx, my = pygame.mouse.get_pos()
            if Item.TUP_IKSIR in self.flags:
                hover_rect = self.rect.inflate(16, 16)
                mouse_hover = hover_rect.collidepoint(mx, my)
            else:
                # Yuvarlak iksir için 24px yarıçaplı dairesel alan
                mouse_hover = math.hypot(mx - item_cx, my - item_cy) <= 24

            # 2. Oyuncu yaklaştı mı? (~130 piksel mesafe)
            player_dist = math.hypot(player.x - item_cx, player.y - item_cy)
            player_near = player_dist <= 130

            self.show_text = mouse_hover or player_near
        else:
            self.show_text = False

        # -------------------------------------------------------------
        # 1. POZİSYON GÜNCELLEMESİ (Sürükleme)
        # -------------------------------------------------------------
        if self.picked and self.drag_to_player:
            self.x = player.x
            self.y = player.y
            if hasattr(self, "rect") and self.rect is not None:
                self.rect.topleft = (self.x, self.y)

        # -------------------------------------------------------------
        # 2. ZEMİN GÖLGESİ
        # -------------------------------------------------------------
        if not self.picked:
            if Item.TUP_IKSIR in self.flags:
                shadow_rect = pygame.Rect(self.x - 3, self.y + 44, 26, 8)
            else:
                shadow_rect = pygame.Rect(self.x - 18, self.y + 14, 36, 10)
            
            pygame.draw.ellipse(surface, (14, 18, 22), shadow_rect)

        # -------------------------------------------------------------
        # 3. İSİM ETİKETİ (Sadece show_text True Olduğunda Çizilir)
        # -------------------------------------------------------------
        if not self.picked and self.show_text:
            use_font = self.font if self.font is not None else font
            text_w, text_h = use_font.font.size(self.name)
            
            badge_w = text_w + 24
            badge_h = text_h + 10
            badge_cx = self.x + 10 if Item.TUP_IKSIR in self.flags else self.x
            badge_rect = pygame.Rect(0, 0, badge_w, badge_h)
            badge_rect.center = (badge_cx, self.y - 42)

            # Kapsül 3D Gölgesi
            pygame.draw.rect(surface, (10, 14, 18), badge_rect.move(0, 3), border_radius=8)
            # Kapsül Gövdesi (Koyu grafit)
            pygame.draw.rect(surface, (24, 28, 36), badge_rect, border_radius=8)
            # İnce Panel Çerçevesi
            pygame.draw.rect(surface, (55, 65, 80), badge_rect, width=2, border_radius=8)

            # Sol Kenarda İksir Renginde Neon Gösterge Noktası
            pygame.draw.circle(surface, self.color, (badge_rect.left + 9, badge_rect.centery), 4)

            # Metin Gölgesi ve Beyaz Başlık
            use_font.draw_text(self.name, (badge_rect.left + 19, badge_rect.centery + 1), surface, (15, 18, 24), hiza="midleft")
            use_font.draw_text(self.name, (badge_rect.left + 18, badge_rect.centery), surface, (240, 244, 250), hiza="midleft")

        # -------------------------------------------------------------
        # 4. TÜP İKSİR (TUP_IKSIR) ÇİZİMİ
        # -------------------------------------------------------------
        if Item.TUP_IKSIR in self.flags:
            # Mantar Tıpa
            cork_rect = pygame.Rect(self.x + 5, self.y - 6, 10, 10)
            pygame.draw.rect(surface, (110, 72, 42), cork_rect, border_radius=3)
            pygame.draw.line(surface, (175, 125, 80), (cork_rect.left + 2, cork_rect.top + 2), (cork_rect.right - 2, cork_rect.top + 2), 2)
            pygame.draw.rect(surface, (55, 35, 20), cork_rect, width=1, border_radius=3)

            # Şişe Tabanı ve Sıvı
            pygame.draw.rect(surface, colours.darker(self.color, 45), self.rect, border_radius=10)
            liquid_fill = self.rect.inflate(-4, -4)
            pygame.draw.rect(surface, self.color, liquid_fill, border_radius=8)

            # Cam Parlaması
            pygame.draw.line(surface, (255, 255, 255), (self.x + 4, self.y + 8), (self.x + 4, self.y + 36), 2)
            pygame.draw.circle(surface, (255, 255, 255), (self.x + 4, self.y + 40), 1)

            # Çerçeve Konturu
            pygame.draw.rect(surface, (215, 230, 245), self.rect, width=2, border_radius=10)
            pygame.draw.rect(surface, (30, 38, 50), self.rect, width=1, border_radius=10)

        # -------------------------------------------------------------
        # 5. YUVARLAK İKSİR (YUVARLAK_IKSIR) ÇİZİMİ
        # -------------------------------------------------------------
        elif Item.YUVARLAK_IKSIR in self.flags:
            # Şişe Boynu ve Tıpa
            neck_start = (self.x + 10, self.y - 10)
            neck_end = (self.x + 22, self.y - 22)
            pygame.draw.line(surface, (215, 230, 245), neck_start, neck_end, 8)
            pygame.draw.line(surface, (30, 38, 50), neck_start, neck_end, 10)
            pygame.draw.line(surface, (215, 230, 245), neck_start, neck_end, 7)

            cork_start = (self.x + 18, self.y - 18)
            cork_end = (self.x + 26, self.y - 26)
            pygame.draw.line(surface, (110, 72, 42), cork_start, cork_end, 6)
            pygame.draw.line(surface, (175, 125, 80), (cork_start[0], cork_start[1] - 1), (cork_end[0], cork_end[1] - 1), 2)

            # Gövde & Sıvı
            pygame.draw.circle(surface, (30, 38, 50), (self.x, self.y), 21)
            pygame.draw.circle(surface, colours.darker(self.color, 45), (self.x, self.y), 20)
            pygame.draw.circle(surface, self.color, (self.x, self.y - 1), 17)

            # Cam Işıltısı
            pygame.draw.circle(surface, (255, 255, 255), (self.x - 7, self.y - 7), 3)
            pygame.draw.circle(surface, (255, 255, 255), (self.x - 11, self.y - 4), 1)

            # Çerçeve
            pygame.draw.circle(surface, (215, 230, 245), (self.x, self.y), 20, width=2)

        # -------------------------------------------------------------
        # 6. ALAN / TEMAS EFEKTİ
        # -------------------------------------------------------------
        if self.touching:
            self.effect_rect = pygame.Rect(0, 0, 200, 200)
            self.effect_rect.center = (self.x, self.y)

            pygame.draw.circle(surface, colours.darker(self.color, 35), (self.x, self.y), 102, width=1)
            pygame.draw.circle(surface, self.color, (self.x, self.y), 100, width=3)
            pygame.draw.circle(surface, colours.lighter(self.color, 50), (self.x, self.y), 97, width=1)

    def update(self, varliklar: list):
        if not self.used:
            if self.effect_rect is not None:
                for varlik in varliklar:
                    if self.effect_rect.colliderect(varlik.image_rect):
                        try:
                            for effect in self.effects:
                                effect: Effect
                                effect.use_global(self.flags, varlik)
                        except AttributeError:
                            print(f"No attribute in {varlik}")
                        self.used = True

    def handle_event(self, event: pygame.event.Event):
        if self.picked and self.pickable:
            if event.type == pygame.MOUSEBUTTONDOWN and not self.mouse_getted:
                if event.button == 3:
                    self.drag_to_player = False
    
    def update_pos(self, dt):
        if not self.drag_to_player and not self.used:
            if not self.mouse_getted:
                self.mx, self.my = pygame.mouse.get_pos()
            self.mouse_getted = True

            self.dx = self.mx - self.x
            self.dy = self.my - self.y

            self.distance = math.hypot(self.dx, self.dy)
            if self.distance > 1.0:
                self.touching = False
                move_distance = self.speed * dt
                if move_distance >= self.distance:
                    self.x = self.mx
                    self.y = self.my
                    self.touching = True
                else:
                    self.x += (self.dx / self.distance) * move_distance
                    self.y += (self.dy / self.distance) * move_distance
            else:
                self.touching = True

        if not self.use_timer_started and self.touching and not self.used:
            self.use_timer_started = True
    
    def use(self, player):
        if not self.used and not self.pickable:
            for effect in self.effects:
                effect: Effect
                effect.use(player, self.flags)
            self.used = True
        if not self.picked:
            if not self.used and self.pickable:
                self.picked = True
                self.drag_to_player = True
    
    def copy(self):
        return copy.deepcopy(self)
    
    def __getstate__(self):
        state = self.__dict__.copy()
        if state.get("font"):
            del state["font"]
        return state
    
    def __setstate__(self, state):
        self.__dict__.update(state)
        if not self.__dict__.get("font") and self.__dict__.get("font_name"):
            self.font = userFont(self.font_name, self.font_size)



class Player:
    SETTINGS: Settings = None

    # Her kare için: (el_x, el_y, kılıç_açısı)
    # Açı referansı: 0 = düz sağa uzanmış, 90 = dik yukarı, -45 = aşağı eğik
    SWORD_SOCKETS = {
        # Saldırı komboları (Tam istediğin gibi, kesinlikle dokunulmadı)
        "attack": [
            {"pos": (33, 58), "angle": -75},
            {"pos": (80, 52), "angle": 15},
            {"pos": (60, 26), "angle": -80},
            {"pos": (89, 58), "angle": 0},
        ],

        # --- NORMAL HAREKETLER (ARTIK TERS / SIRTA VE ARKAYA DÖNÜK) ---
        "idle": [
            # Beklerken kılıç omzun gerisinde / sırtta dinlenir (yukarı-arkaya doğru)
            {"pos": (44, 60), "angle": -135},
        ],
        "run": [
            # Koşarken kılıç anime/ninja koşusu gibi gövdenin arkasına yatar
            {"pos": (45, 58), "angle": 155},
        ],
        "dash": [
            # Atılırken mermi hızında tam arkaya doğru yatay uzanır
            {"pos": (45, 55), "angle": 175},
        ],

        # --- DEFLECT (OK SEKTİRME / KARŞILAMA) SOKETLERİ ---
        # 1. Q'ya basıp bekleme anı (Kılıç göğüs hizasında 55° çapraz gardda)
        "deflect_ready": [
            {"pos": (69, 51), "angle": 55},
        ],

        # 2. Ok çarptığı an oynayan 10 karelik karşılama savurması:
        "deflect": [
            {"pos": (68, 51), "angle": 55},    # 0: Temas anı (Darbe garda vurur)
            {"pos": (71, 49), "angle": 68},    # 1: Şok dalgası (Kılıç dikleşir)
            {"pos": (78, 40), "angle": 35},    # 2: Karşı savurma ivmesi başlar
            {"pos": (85, 33), "angle": -15},   # 3: Tam savurma (Kılıç oku ileri-yukarı biçer)
            {"pos": (86, 39), "angle": -48},   # 4: Hamle uzanışı
            {"pos": (81, 48), "angle": -75},   # 5: Enerji dağılımı
            {"pos": (74, 54), "angle": -102},  # 6: Geri toparlanma
            {"pos": (69, 56), "angle": -120},  # 7: Kılıç sırta doğru çekilir
            {"pos": (65, 58), "angle": -130},  # 8: Garda yaklaşma
            {"pos": (64, 56), "angle": -135},  # 9: Normal bekleme (idle) açısına kilitlenme
        ],
    }

    def __init__(
        self,
        hp,
        using_gun: Sword,
        image_name: os.PathLike,
        val_manager: ValueManager | None,
        speed_normal=400,
        speed_max=600,
        anim_dir: os.PathLike | None = None,
        anim_speeds: dict | None = None
    ):
        self.max_hp = 200
        self.hp = hp
        self.val_manager = val_manager
        self.items = []
        self.using_gun = using_gun
        self.speed_normal = scale(speed_normal)
        self.speed_max = scale(speed_max)
        self.speed = self.speed_max
        self.image_name = image_name

        # Dinamik Animasyon Kontrolcüsü
        self.anim_dir = anim_dir
        # Animasyon hızlarına deflect ekle (10 kare için saniyede 18 kare akıcı bir hızdır)
        self.anim_speeds = anim_speeds or {
            "idle": 4.0,
            "run": 8.0,
            "dash": 12.0,
            "combat": 6.0,
            "attack": 10.0,
            "deflect": 18.0,        # <-- YENİ
            "deflect_ready": 6.0     # <-- YENİ
        }

        # Sektirme animasyon durum değişkenleri
        self.is_deflecting_anim = False
        self.deflect_anim_frame = 0.0
        
        if self.anim_dir and os.path.exists(self.anim_dir):
            self.anim = AnimationController(self.anim_dir, speeds=self.anim_speeds, target_scale=0.7 * SCALE)
            initial_frame = self.anim.get_frame()
            self.image = initial_frame if initial_frame is not None else pygame.transform.scale_by(pygame.image.load(self.image_name), SCALE)
        else:
            self.anim = None
            self.image = pygame.image.load(self.image_name)
            w = int(self.image.get_width() * SCALE)
            h = int(self.image.get_height() * SCALE)
            self.image = pygame.transform.smoothscale(self.image, (w, h))

        self.image_rect = self.image.get_rect()
        self.rotated = None
        self.rotated_rect = None
        self.touching = False
        self._maximized = False
        self.change_angle = True
        self.angle = 360
        self.distance = None
        self.drawing = False
        self.teleport_drawing = False
        self.teleport_mx, self.teleport_my = None, None
        self.teleporting = False
        self.last_pressed = None
        self.damaged_cooldown = 0.6
        self.ability_healing = False
        self.available_guns = [self.using_gun]
        self.heal_cooldown_orig = 8
        self.heal_cooldown = self.heal_cooldown_orig
        self.sword_attacking = False
        self.hand_spot = 30
        self.sword_rect = None
        self.deflecting = False
        self.sword_angle = None
        self.cd_deflect = 0
        self.cd_deflect_orig = 2
        # Saldırı Kombo Sistemi
        self.attack_frame_idx = 0
        self.attack_idle_timer = 0.0     # Tıklama yapılmadığında sayan sayaç
        self.ATTACK_TIMEOUT = 0.7       # 0.7 saniye sonra normale dön

        self._init_sounds()

        self.parlama_image_orig = pygame.image.load(os.path.join(BASE_DIR,r"images/parlama.png"))
        self.parlama_image = pygame.transform.scale_by(self.parlama_image_orig, 0.18)
        self.parlama_image2 = pygame.transform.scale_by(self.parlama_image_orig, 0.12)
        self.parlama_rect = None
        self.parlama_rect2 = None
        self.parlama_image_angle = 0
        self.parlama_image_angle2 = 0
        self.parlama_rotate_speed_conf = (
            1600,
            240
        )
        self.parlama_rotate_speed = 1600
        self.look_dir = "right"
        self.old_x = None
        self.old_y = None
        self.movable = True
        self.deflect_bullets = []

        self.combo_meter = ComboMeter()

        # Available Guns
        self.transparency_hover = 0

        self.ghost_trail = []       # Hayalet izleri listesi
        self.ghost_spawn_timer = 0.0

    @classmethod
    def set_settings_manager(cls, settings):

        cls.SETTINGS = settings

    def set_pos(self, world):
        world: World
        while True:
            x = random.randint(200, info.current_w - 200)
            y = random.randint(200, info.current_h - 200)
            self.image_rect = pygame.image.load(self.image_name).get_rect(topleft=(x, y))
            if not self.image_rect.collidelist(world.rocks_rects) != -1 and not self.image_rect.colliderect(world.dirt_rect):
                self.x = x
                self.y = y
                break

    def perform_attack_click(self):
        if self.drawing:
            return

        total_attack_frames = len(self.anim.animations.get("attack", []))
        if total_attack_frames == 0:
            return

        if not self.sword_attacking:
            self.sword_attacking = True
            self.attack_frame_idx = 0
        else:
            self.attack_frame_idx = (self.attack_frame_idx + 1) % total_attack_frames

        self.attack_idle_timer = 0.0

        # O anki karenin (0, 1, 2 veya 3) sesini çal:
        swing_sound = self.attack_swings.get(self.attack_frame_idx)
        if swing_sound:
            if Player.SETTINGS is not None:
                swing_sound.set_volume(Player.SETTINGS.get("sfx_volume"))

            if Player.SETTINGS is not None:
                if Player.SETTINGS.get("sfx"):
                    swing_sound.play()

            else:
                swing_sound.play()

    def draw(self, surface: pygame.Surface):
        for g in self.ghost_trail:
            ghost_surf = g["image"].copy()
            ghost_surf.set_alpha(int(g["alpha"]))
            # Neon mavi bir tonlama vermek istersen:
            ghost_surf.fill((0, 200, 255), special_flags=pygame.BLEND_RGB_MULT)
            surface.blit(ghost_surf, g["rect"])
            
        # 1. Mevcut animasyon durumunu kontrol et
        curr_state = getattr(self.anim, "current_state", "idle") if getattr(self, "anim", None) else "idle"
        is_deflecting = curr_state in ("deflect", "deflect_ready") or getattr(self, "is_deflecting_anim", False)

        def draw_sword():
            if isinstance(self.using_gun, Sword) and getattr(self, "anim", None):
                state = self.anim.current_state
                sockets = Player.SWORD_SOCKETS.get(state, Player.SWORD_SOCKETS.get("idle", []))
                if not sockets:
                    return

                frame_idx = int(self.anim.frame_index) % len(sockets)
                socket = sockets[frame_idx]

                # ---------------------------------------------------------
                # 1. KRİTİK DÜZELTME: Karakter ölçeği (0.7 * SCALE) ile eşitle
                # ---------------------------------------------------------
                char_scale = 0.7 * SCALE
                hand_rel_x = int(socket["pos"][0] * char_scale)
                hand_rel_y = int(socket["pos"][1] * char_scale)
                base_angle = socket["angle"]

                # ---------------------------------------------------------
                # 2. SAĞ / SOL YÖN HİZALAMASI
                # ---------------------------------------------------------
                if self.look_dir == "left":
                    # Karakter sola döndüğünde X ekseninde simetri al
                    hand_x = self.image_rect.right - hand_rel_x
                    final_angle = 180 - base_angle
                else:
                    hand_x = self.image_rect.left + hand_rel_x
                    final_angle = base_angle

                hand_y = self.image_rect.top + hand_rel_y

                # ---------------------------------------------------------
                # 3. KABZA ORTALAMA OFSETİ (TUTUŞ HİSSİ)
                # ---------------------------------------------------------
                # Kılıcın merkez noktası guard olduğu için, elin kabzayı kavraması
                # adına kılıcı açısına doğru 4-5 piksel ileri itiyoruz:
                rad = math.radians(final_angle)
                grip_offset = 5 * char_scale
                sword_anchor_x = hand_x + math.cos(rad) * grip_offset
                sword_anchor_y = hand_y + math.sin(rad) * grip_offset

                # ---------------------------------------------------------
                # 4. KILIÇ ÇİZİMİ
                # ---------------------------------------------------------
                self.using_gun.draw(surface, sword_anchor_x, sword_anchor_y, final_angle, scale_factor=0.7)

                # =========================================================
                # DEBUG MODU (Gerektiğinde True yapıp elin tam yerini gör):
                # =========================================================
                # pygame.draw.circle(surface, (255, 0, 0), (int(hand_x), int(hand_y)), 3)

        # 2. Katman sıralaması
        if is_deflecting:
            # Deflect anında: Önce kılıç çizilir, ardından karakter + beyaz çizgi kılıcın ÜSTÜNE basılır
            draw_sword()
            if self.image:
                surface.blit(self.image, self.image_rect)
        else:
            # Normal durumlarda: Karakter gövdesi altta, kılıç elde üstte durur
            if self.image:
                surface.blit(self.image, self.image_rect)
            draw_sword()

        # 3. Sektirilen mermiler
        for bullet in self.deflect_bullets:
            bullet.draw(surface)

        self.combo_meter.draw(surface)

    def get_hitbox_at(self, x: float, y: float) -> pygame.Rect:
        """Karakterin gövdesi yerine sadece ayak tabanındaki dar alanı döndürür."""
        # Karakterin genişliğinin yarısı, boyunun ise 1/3'ü kadar taban alanı
        box_w = max(16, int(self.image_rect.width * 0.45))
        box_h = max(12, int(self.image_rect.height * 0.35))
        
        hitbox = pygame.Rect(0, 0, box_w, box_h)
        # Hitbox karakterin ayak ucunda ortalanır:
        hitbox.centerx = int(x)
        hitbox.bottom = int(y + self.image_rect.height * 0.45)
        return hitbox

    def update(self, mouse_pos, world, dt, swidth: int, sheight: int, enemies: list):
        # İz bırakma
        alive_ghosts = []
        for g in self.ghost_trail:
            g["alpha"] -= 600 * dt  # Çok hızlı solar
            if g["alpha"] > 0:
                alive_ghosts.append(g)
        self.ghost_trail = alive_ghosts

        if self.drawing:
            self.ghost_spawn_timer += dt
            if self.ghost_spawn_timer >= 0.04:
                self.ghost_spawn_timer = 0.0
                if getattr(self, "image", None):
                    self.ghost_trail.append({
                        "image": self.image.copy(),
                        "rect": self.image_rect.copy(),
                        "alpha": 180.0
                    })

        # 1. Mermi sektirme (Deflect) güncellemeleri
        for bullet in self.deflect_bullets:
            bullet: Bullet
            bullet.update(world, dt, enemies)
            if bullet.deleted:
                self.deflect_bullets.remove(bullet)

        if not self.drawing:
            self.speed = self.speed_normal

        # 2. Hareket ve Pozisyon Hesaplamaları
        is_moving = False

        if self.movable:
            if isinstance(self.using_gun, Sword) or type(self.using_gun) == Charm:
                if self.change_angle:
                    self.mx, self.my = mouse_pos
                    self.dx = self.mx - self.x
                    self.dy = self.my - self.y
                    self.distance = math.hypot(self.dx, self.dy)

                if not self.teleporting:
                    if self.distance is not None and self.distance > 8:
                        self.touching = False
                        move_dist = self.speed * dt
                        step = min(move_dist, self.distance)

                        radians = math.atan2(self.dy, self.dx)
                        move_x = math.cos(radians)
                        move_y = math.sin(radians)

                        target_vx = move_x * step
                        target_vy = move_y * step

                        # --- ADIM 1: X EKSENİ TESTİ (Yatay Kayma) ---
                        test_x = self.x + target_vx
                        hitbox_x = self.get_hitbox_at(test_x, self.y)

                        if hitbox_x.collidelist(world.rocks_rects) == -1 and not hitbox_x.colliderect(world.dirt_rect):
                            self.x = test_x
                            is_moving = True

                        # --- ADIM 2: Y EKSENİ TESTİ (Dikey Kayma) ---
                        test_y = self.y + target_vy
                        hitbox_y = self.get_hitbox_at(self.x, test_y)

                        if hitbox_y.collidelist(world.rocks_rects) == -1 and not hitbox_y.colliderect(world.dirt_rect):
                            self.y = test_y
                            is_moving = True
                    else:
                        self.touching = True
                        is_moving = False

                    # Fareye göre bakış açısı
                    if self.change_angle and not self.sword_attacking:
                        self.angle = math.degrees(math.atan2(-self.dy, self.dx))
                    
                    if -45 < self.angle < 45:
                        self.look_dir = "right"
                    elif self.angle > 135 or self.angle < -135:
                        self.look_dir = "left"

            elif type(self.using_gun) == Gun:
                keys = pygame.key.get_pressed()
                vx = 0
                vy = 0

                if not self.drawing:
                    if keys[pygame.K_w]: vy -= self.speed * dt; self.last_pressed = "w"
                    if keys[pygame.K_s]: vy += self.speed * dt; self.last_pressed = "s"
                    if keys[pygame.K_a]: vx -= self.speed * dt; self.look_dir = "left"; self.last_pressed = "a"
                    if keys[pygame.K_d]: vx += self.speed * dt; self.look_dir = "right"; self.last_pressed = "d"
                else:
                    if self.last_pressed == "w": vy -= self.speed * dt
                    elif self.last_pressed == "s": vy += self.speed * dt
                    elif self.last_pressed == "a": vx -= self.speed * dt; self.look_dir = "left"
                    elif self.last_pressed == "d": vx += self.speed * dt; self.look_dir = "right"

                # X Ekseninde Kayma
                if vx != 0:
                    new_x = max(0, min(self.x + vx, swidth))
                    hb_x = self.get_hitbox_at(new_x, self.y)
                    if hb_x.collidelist(world.rocks_rects) == -1 and not hb_x.colliderect(world.dirt_rect):
                        self.x = new_x
                        is_moving = True

                # Y Ekseninde Kayma
                if vy != 0:
                    new_y = max(0, min(self.y + vy, sheight))
                    hb_y = self.get_hitbox_at(self.x, new_y)
                    if hb_y.collidelist(world.rocks_rects) == -1 and not hb_y.colliderect(world.dirt_rect):
                        self.y = new_y
                        is_moving = True

            # 3. Animasyon Durumu ve Görsel Güncellemesi (TÜM HAREKETLER BİTTİKTEN SONRA)
            # --- Saldırı Zaman Aşımı (Timeout) Kontrolü ---
            # 1. 2 saniye tıklanmazsa saldırıdan çık
            if self.sword_attacking:
                safe_dt = dt / 1000.0 if dt > 1.0 else dt
                self.attack_idle_timer += safe_dt
                if self.attack_idle_timer >= self.ATTACK_TIMEOUT:
                    self.sword_attacking = False
                    self.attack_idle_timer = 0.0
                    self.attack_frame_idx = 0

            # 2. Durum Belirleme ve Animasyon
            if getattr(self, "anim", None) is not None:
                # ÖNCELİK 1: Ok sektirme animasyonu (10 kare tamamlanana kadar oynar)
                if self.is_deflecting_anim:
                    target_state = "deflect"
                    self.anim.current_state = "deflect"
                    self.deflect_anim_frame += self.anim_speeds["deflect"] * dt
                    
                    if int(self.deflect_anim_frame) >= 10:
                        self.is_deflecting_anim = False
                        self.deflect_anim_frame = 0.0
                        self.anim.frame_index = 0.0
                    else:
                        self.anim.frame_index = self.deflect_anim_frame

                # ÖNCELİK 2: Q basılıyken gardda bekleme
                elif self.deflecting:
                    target_state = "deflect_ready"
                    self.anim.frame_index = 0.0
                    self.anim.update(target_state, dt)

                # ÖNCELİK 3: Dash hareketi
                elif self.drawing:
                    target_state = "dash"
                    self.anim.update(target_state, dt)

                # ÖNCELİK 4: Kılıç tıklama kombosu
                elif self.sword_attacking:
                    target_state = "attack"
                    self.anim.current_state = "attack"
                    self.anim.frame_index = float(self.attack_frame_idx)

                # ÖNCELİK 5: Koşma ve Bekleme
                elif is_moving:
                    target_state = "run"
                    self.anim.speeds["run"] = (self.speed / self.speed_normal) * 14.0
                    self.anim.update(target_state, dt)
                else:
                    target_state = "idle"
                    self.anim.update(target_state, dt)

                # Kareyi al ve gövdeyi güncelle
                frame = self.anim.get_frame(facing_left=(self.look_dir == "left"))
                if frame is not None:
                    self.image = frame
                    self.image_rect = self.image.get_rect(center=(self.x, self.y))

            self.combo_meter.update(dt)

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:

                if isinstance(self.using_gun, Sword):
                    self.perform_attack_click()
        
    def heal(self, dt):
        if self.ability_healing:
            self.heal_cooldown -= dt
            if self.heal_cooldown <= 0:
                self.hp = min(self.max_hp, self.hp + 10)
                self.heal_cooldown = self.heal_cooldown_orig

    def deflect(self, enemies: list, dt):
        if not isinstance(self.using_gun, Sword):
            return

        keys = pygame.key.get_pressed()
        # Q tuşuna basıldığında gard (deflect_ready) başlar
        if keys[pygame.K_q] and not self.deflecting and not self.is_deflecting_anim:
            self.deflecting = True
            self.cd_deflect = self.cd_deflect_orig

        if self.deflecting:
            self.cd_deflect -= dt
            if self.cd_deflect > 0:
                rect = pygame.Rect(self.x - 100, self.y - 100, 250, 250)
                rect.center = (self.x, self.y)

                for enemy in enemies:
                    enemy: Enemy
                    for arrow in enemy.arrows:
                        arrow: Arrow
                        arrow_rect = arrow.rotated_rect or arrow.image_rect
                        if rect.colliderect(arrow_rect):
                            enemy.arrows.remove(arrow)

                            # 1. Yeni mermiyi yönlendirip oluştur
                            new_bullet = Bullet(
                                self.x, self.y, arrow.image_name,
                                arrow.attack * 3, arrow.speed + 700,
                                enemy.x, enemy.y, 2000, "__deflected__"
                            )
                            new_bullet.angle = math.degrees(math.atan2(-(enemy.y - self.y), (pygame.mouse.get_pos()[0] - self.x)))
                            new_bullet.rotated = pygame.transform.rotate(new_bullet.image, new_bullet.angle)
                            new_bullet.rotated_rect = new_bullet.rotated.get_rect(center=(new_bullet.x, new_bullet.y))
                            self.deflect_bullets.append(new_bullet)

                            # 2. Beklemeyi bitir, 10 KARELİK SEKTİRME VURUŞUNU BAŞLAT!
                            self.deflecting = False
                            self.cd_deflect = 0
                            self.is_deflecting_anim = True
                            self.deflect_anim_frame = 0.0

                            # Varsa sektirme sesini patlat
                            if getattr(self, "sfx_deflect", None):
                                self.sfx_deflect.play()
                            break
            else:
                self.deflecting = False

    def dash(self):
        if isinstance(self.using_gun, Sword):
            # Saldırıyı anında iptal et ve sıfırla
            self.sword_attacking = False
            self.attack_frame_idx = 0
            self.attack_idle_timer = 0.0
            self.sword_rect = None

            def reduce():
                nonlocal self
                if not self._maximized:
                    self.speed = self.speed_normal
                else:
                    self.speed = self.speed_max
                self.change_angle = True
                self.drawing = False

            self.old_x = self.x
            self.old_y = self.y
            self.speed += self.using_gun.dash_speed
            self.change_angle = False
            self.drawing = True
            self.damaged = False
            after(reduce, secs=0.2)
    
    def teleport(self, world):

        def go():
            nonlocal self
            self.x = self.teleport_mx
            self.y = self.teleport_my
            self.teleport_drawing = False
            self.teleporting = False

        if not self.teleporting:
            mx, my = pygame.mouse.get_pos()
            mouse_rect = pygame.Rect(mx, my, self.image.get_width(), self.image.get_height())
            if mouse_rect.collidelist(world.rocks_rects) != -1:
                print("TAŞA DEĞİYOR")
                return
            self.teleport_drawing = True
            self.teleport_mx = mx
            self.teleport_my = my
            after(go, secs=1.75)
        self.teleporting = True

    def draw_teleport(self, surface: pygame.Surface):
        if self.teleport_drawing:
            if self.teleport_mx is not None and self.teleport_my is not None:
                pygame.draw.circle(surface, colours.BLUE, (self.teleport_mx, self.teleport_my), 20, 3)
                pygame.draw.circle(surface, colours.LIGHT_BLUE, (self.teleport_mx, self.teleport_my), 8, 3)
    
    def draw_dash(self, surface: pygame.Surface):
        if self.drawing and type(self.using_gun) == Sword and self.old_x is not None and self.old_y is not None:
            draw_aa_line(surface, colours.WHITE, (int(self.old_x), int(self.old_y)), (int(self.x), int(self.y)), 5)
    
    def damage(self, enemies: list, dt, menu=False):
        if menu:
            return

        self.damaged_cooldown -= dt

        if isinstance(self.using_gun, Sword):
            # 1. DASH SALDIRISI
            if self.drawing:
                if self.damaged_cooldown <= 0:
                    hit_anyone = False
                    for enemy in enemies:
                        enemy: Enemy

                        if not enemy.living: continue

                        if Enemy.DAMAGE_SWORD_DASH in enemy.damagables:
                            if self.image_rect.colliderect(enemy.image_rect):
                                enemy.hp -= self.using_gun.attack
                                enemy.flash_timer = 0.07

                                hit_anyone = True

                                # Dash vuruşunda hafif geri tepme
                                if hasattr(enemy, "recoil_vx"):
                                    dx = enemy.x - self.x
                                    dy = enemy.y - self.y
                                    dist = math.hypot(dx, dy) or 1.0
                                    enemy.recoil_vx = (dx / dist) * 600.0
                                    enemy.recoil_vy = (dy / dist) * 300.0

                    if hit_anyone:
                        self.damaged_cooldown = 0.2
                        if getattr(self, "hit_sfx_pool", None):
                            if Player.SETTINGS is not None:
                                self.hit_sfx_pool.play(Player.SETTINGS.get("sfx_volume"), Player.SETTINGS.get("sfx"))

                            else:
                                self.hit_sfx_pool.play()

            # 2. NORMAL KILIÇ KOMBO SALDIRISI
            elif self.sword_attacking:
                # Sadece vuruş savurma karelerinde (Kare 1 ve Kare 3) hasar ver
                if self.attack_frame_idx in (1, 3):
                    if self.damaged_cooldown <= 0:
                        hit_anyone = False

                        # Vurma alanı (Hitbox)
                        if self.look_dir == "right":
                            hit_box = pygame.Rect(self.x, self.y - 35, 85, 70)
                        else:
                            hit_box = pygame.Rect(self.x - 85, self.y - 35, 85, 70)

                        for enemy in enemies:
                            enemy: Enemy

                            if not enemy.living: continue

                            if Enemy.DAMAGE_SWORD in enemy.damagables:
                                if hit_box.colliderect(enemy.image_rect):
                                    enemy.hp -= self.using_gun.attack
                                    enemy.flash_timer = 0.07

                                    hit_anyone = True

                                    # Geri tepme (Kare 3 bitirici vuruş ise daha sert iter)
                                    force = 900.0 if self.attack_frame_idx == 3 else 550.0
                                    dx = enemy.x - self.x
                                    dy = enemy.y - self.y
                                    dist = math.hypot(dx, dy) or 1.0

                                    if hasattr(enemy, "recoil_vx"):
                                        enemy.recoil_vx = (dx / dist) * force
                                        enemy.recoil_vy = ((dy / dist) - 0.2) * (force * 0.4)
                                    else:
                                        enemy.recoil = 0.43
                                        enemy.recoil_dir = self.look_dir

                        # En az bir düşmana isabet ettiyse sesi patlat
                        if hit_anyone:
                            self.damaged_cooldown = 0.15
                            if getattr(self, "combo_meter", None):
                                self.combo_meter.add_hit(count=1, swidth=info.current_w, sheight=info.current_h) # Kombo + 1

                            if getattr(self, "hit_sfx_pool", None):
                                if Player.SETTINGS is not None:
                                    self.hit_sfx_pool.play(Player.SETTINGS.get("sfx_volume"), Player.SETTINGS.get("sfx"))
                                else:
                                    self.hit_sfx_pool.play()

        if type(self.using_gun) == Gun:
            if self.drawing:
                if self.damaged_cooldown <= 0:
                    for enemy in enemies:
                        enemy: Enemy
                        if Enemy.DAMAGE_BRONZE_GUN in enemy.damagables and self.using_gun.material == MaterialFlags.BRONZE or Enemy.DAMAGE_SILVER_GUN in enemy.damagables and self.using_gun.material == MaterialFlags.SILVER:
                            self.using_gun: Gun
                            if enemy.living:
                                if enemy.image_rect is not None and self.using_gun.rotated_rect is not None:
                                    if self.using_gun.rotated_rect.colliderect(enemy.image_rect):
                                        enemy.hp -= self.using_gun.attack + 12

                                        self.damaged_cooldown = 0.2
                                        break

    def reset(self, world, default_gun):
        self.max_hp = 200
        self.hp = 200
        self.items = []
        self.using_gun = default_gun
        self.set_pos(world)
        self.speed_normal = self.speed_normal
        self.speed_max = self.speed_max
        if self._maximized:
            self.speed = self.speed_max
        else:
            self.speed = self.speed_normal
        self.image = pygame.image.load(self.image_name)
        self.rotated = None
        self.rotated_rect = None
        self.touching = False
        self._maximized = False
        self.angle = 0
        self.available_guns.clear()
        self.available_guns.append(self.using_gun)
    
    def draw_statistics(self, surface: pygame.Surface, font: userFont, info, clock: pygame.time.Clock):

        langs = {
            "hp": Lang(türkçe="Can", english="Hp", arabic="حياة", sanskrit="जीवनम्‌"),
            "weapon": Lang(türkçe="Silah", english="Weapon", arabic="سلاح", sanskrit="अस्त्रम्"),
            "speed": Lang(türkçe="Hız", english="Speed", arabic="سرعة", sanskrit="गति")
        }

        # ---------------------------------------------------------
        # TÜM ÖLÇÜLERİN DİNAMİK ORANLANMASI (1:1 Görsel Koruma)
        # ---------------------------------------------------------
        y = info.current_h - int(scale(120))
        h = max(18, int(scale(28)))

        bar_padding = int(scale(20))
        item_padding = int(scale(18))
        fps_padding = int(scale(15))
        min_gap = max(1, int(scale(6)))

        # Kart & Çerçeve Ölçekleri
        shadow_offset = max(1, int(scale(4)))
        r_outer = 9
        r_inner = 9
        border_w = max(1, int(scale(2)))
        inner_pad = max(2, int(scale(8)))
        min_fill_w = max(2, int(scale(6)))

        # Metin & Vurgu Çizgisi Ölçekleri
        accent_w = max(1, int(scale(3)))
        accent_x = int(scale(8))
        accent_y = max(2, int(scale(5)))
        text_start_pad = int(scale(18))
        text_shadow_off = max(1, int(scale(1)))

        in_pad = scale(16) # İstatistik kutusunun kenar yumuşatması yüzünden yazının taşmasını engellemek için.

        # ---------------------------------------------------------
        # 1. DİNAMİK GENİŞLİK HESAPLAMALARI
        # ---------------------------------------------------------
        raw_items: list[tuple[str, int, dict]] = []

        # CAN BARI
        hp_max_text = f"{langs['hp']()}: {self.max_hp:.1f}"
        hp_width = font.font.size(hp_max_text)[0] + bar_padding 
        raw_items.append(("hp", hp_width, {}))

        # HEAL BARI
        if self.ability_healing:
            raw_items.append(("heal", hp_width, {}))

        # SİLAH
        w_lbl = f"{langs['weapon']()}: "
        w_val = f"{self.using_gun.name}"
        weapon_width = font.font.size(w_lbl + w_val)[0] + item_padding + in_pad
        raw_items.append(("weapon", weapon_width, {"lbl": w_lbl, "val": w_val}))

        # HIZ
        s_lbl = f"{langs['speed']()}: "
        s_val = f"{int(self.speed / 100)}"
        speed_width = font.font.size(s_lbl + s_val)[0] + item_padding + in_pad
        raw_items.append(("speed", speed_width, {"lbl": s_lbl, "val": s_val}))

        # FPS
        fps_lbl = "FPS: "
        fps_val = f"{int(clock.get_fps())}"
        fps_max_val = f"{Player.SETTINGS.get('fps')}"
        fps_width = font.font.size(fps_lbl + fps_max_val)[0] + fps_padding + in_pad
        raw_items.append(("fps", fps_width, {"lbl": fps_lbl, "val": fps_val}))

        # ---------------------------------------------------------
        # 2. EŞİT BOŞLUK (GAP) VE YERLEŞİM
        # ---------------------------------------------------------
        total_content_width = sum(w for _, w, _ in raw_items)
        num_items = len(raw_items)
        gap = max(min_gap, (info.current_w - total_content_width) // (num_items + 1))

        elements: list[tuple[str, pygame.Rect, dict]] = []
        current_x = gap

        for element_name, width, meta in raw_items:
            rect = pygame.Rect(current_x, y, width, h)
            elements.append((element_name, rect, meta))
            current_x += width + gap

        # ---------------------------------------------------------
        # 3. ÇİZİM DÖNGÜSÜ
        # ---------------------------------------------------------
        for element, rect, meta in elements:

            # Ortak Kart Gölgesi
            shadow_rect = rect.move(0, shadow_offset)
            pygame.draw.rect(surface, (12, 14, 18), shadow_rect, border_radius=r_outer)

            # Ortak Kart Gövdesi
            pygame.draw.rect(surface, (24, 28, 36), rect, border_radius=r_outer)

            # -----------------------------------------------------
            # A) CAN BARI (HP)
            # -----------------------------------------------------
            if element == "hp":
                percent = max(0.0, min(1.0, self.hp / self.max_hp)) if self.max_hp > 0 else 0

                # İç oyuk hazne (Track)
                inner_rect = rect.inflate(-inner_pad, -inner_pad)
                pygame.draw.rect(surface, (45, 16, 20), inner_rect, border_radius=r_inner)

                # Doldurulan Can Barı
                if percent > 0:
                    fill_w = max(min_fill_w, int(inner_rect.width * percent))
                    fill_rect = pygame.Rect(inner_rect.left, inner_rect.top, fill_w, inner_rect.height)
                    
                    hp_color = (235, 48, 64) if percent > 0.25 else (245, 95, 35)
                    pygame.draw.rect(surface, hp_color, fill_rect, border_radius=r_inner)

                    # Üst Cam Parlaması (Glossy Highlight)
                    sheen_h = max(2, fill_rect.height // 3)
                    sheen_rect = pygame.Rect(fill_rect.left, fill_rect.top, fill_rect.width, sheen_h)
                    pygame.draw.rect(surface, (255, 120, 130), sheen_rect, border_top_left_radius=r_inner, border_top_right_radius=r_inner)

                # Dış metalik çerçeve çizgisi
                pygame.draw.rect(surface, (70, 78, 92), rect, width=border_w, border_radius=r_outer)

                # Metin ve Metin Gölgesi
                hp_str = f"{langs['hp']()}: {self.hp:.1f}"
                font.draw_text(hp_str, (rect.centerx + text_shadow_off, rect.centery + text_shadow_off), surface, (20, 20, 20), hiza="center")
                font.draw_text(hp_str, rect.center, surface, colours.WHITE, hiza="center")

            # -----------------------------------------------------
            # B) İYİLEŞME BARI (HEAL)
            # -----------------------------------------------------
            elif element == "heal":
                percent_heal = max(0.0, min(1.0, self.heal_cooldown / self.heal_cooldown_orig)) if self.heal_cooldown_orig > 0 else 0

                inner_rect = rect.inflate(-inner_pad, -inner_pad)
                pygame.draw.rect(surface, (18, 32, 54), inner_rect, border_radius=r_inner)

                if percent_heal > 0:
                    fill_w = max(min_fill_w, int(inner_rect.width * percent_heal))
                    fill_rect = pygame.Rect(inner_rect.left, inner_rect.top, fill_w, inner_rect.height)
                    pygame.draw.rect(surface, (40, 135, 245), fill_rect, border_radius=r_inner)

                    sheen_h = max(2, fill_rect.height // 3)
                    sheen_rect = pygame.Rect(fill_rect.left, fill_rect.top, fill_rect.width, sheen_h)
                    pygame.draw.rect(surface, (110, 190, 255), sheen_rect, border_top_left_radius=r_inner, border_top_right_radius=r_inner)

                pygame.draw.rect(surface, (60, 85, 120), rect, width=border_w, border_radius=r_outer)

                heal_str = f"{self.heal_cooldown:.2f}s"
                font.draw_text(heal_str, (rect.centerx + text_shadow_off, rect.centery + text_shadow_off), surface, (15, 20, 30), hiza="center")
                font.draw_text(heal_str, rect.center, surface, (220, 240, 255), hiza="center")

            # -----------------------------------------------------
            # C) METİN KARTLARI (SİLAH / HIZ / FPS)
            # -----------------------------------------------------
            else:
                lbl = meta["lbl"]
                val = meta["val"]

                pygame.draw.rect(surface, (50, 58, 70), rect, width=border_w, border_radius=r_outer)

                # Sol neon vurgusu (Kenarlardan accent_y kadar boşluk bırakılarak kart boyuna ortalanır)
                accent_color = (255, 205, 50) if element == "weapon" else ((65, 220, 240) if element == "speed" else (80, 230, 120))
                line_x = rect.left + accent_x
                pygame.draw.line(
                    surface,
                    accent_color,
                    (line_x, rect.top + accent_y),
                    (line_x, rect.bottom - accent_y),
                    width=accent_w
                )

                # Metin Konumlandırma
                lbl_w = font.font.size(lbl)[0]
                text_start_x = rect.left + text_start_pad

                font.draw_text(lbl, (text_start_x, rect.centery), surface, (155, 168, 185), hiza="midleft")
                font.draw_text(val, (text_start_x + lbl_w, rect.centery), surface, accent_color, hiza="midleft")

    def copy(self):
        return copy.deepcopy(self)
    
    def draw_available_guns(self, surface: pygame.Surface):
        parca_sayisi = len(self.available_guns)
        if parca_sayisi == 0:
            return

        if not hasattr(self, "wheel_hover_offsets") or len(self.wheel_hover_offsets) != parca_sayisi:
            self.wheel_hover_offsets = [0.0] * parca_sayisi

        hovered_index = getattr(self, "hovered_gun_index", -1)

        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        center = (info.current_w / 2, info.current_h / 2)
        self.center_wheel = center
        yari_cap = 400

        if parca_sayisi > 1:
            aci = 360 / parca_sayisi

            # ---------------------------------------------------------
            # 1. DİLİM ARKA PLANLARI VE AYIRICILAR
            # ---------------------------------------------------------
            for i in range(parca_sayisi):
                bitis = math.radians((i + 1) * aci)
                noktalar = [center]

                derece = i * aci
                while derece <= (i + 1) * aci:
                    r = math.radians(derece)
                    x = center[0] + math.cos(r) * yari_cap
                    y = center[1] + math.sin(r) * yari_cap
                    noktalar.append((x, y))
                    derece += 2

                x_end = center[0] + math.cos(bitis) * yari_cap
                y_end = center[1] + math.sin(bitis) * yari_cap
                noktalar.append((x_end, y_end))

                # Hover edilen dilim daha aydınlık
                slice_alpha = 95 if i == hovered_index else 45
                pygame.draw.polygon(overlay, (255, 255, 255, slice_alpha), noktalar)
                pygame.draw.line(surface, (50, 60, 75), center, (x_end, y_end), 2)

            # ---------------------------------------------------------
            # 2. DIŞ ÇEMBER VE HOVER KENARLIĞI
            # ---------------------------------------------------------
            # Genel dış çember (gri sınır)
            pygame.draw.circle(surface, (70, 85, 105), center, yari_cap, 6)

            # Hover edilen dilimin dış kenarındaki yay (kalın siyah)
            if hovered_index != -1:
                arc_points = []
                deg = hovered_index * aci
                while deg <= (hovered_index + 1) * aci:
                    rad = math.radians(deg)
                    arc_x = center[0] + math.cos(rad) * yari_cap
                    arc_y = center[1] + math.sin(rad) * yari_cap
                    arc_points.append((arc_x, arc_y))
                    deg += 1.0

                if len(arc_points) >= 2:
                    pygame.draw.lines(surface, colours.BLACK, False, arc_points, width=12)

            # Saydam katmanı ekrana bas
            surface.blit(overlay, (0, 0))

            # ---------------------------------------------------------
            # 3. SİLAHLAR VE İSİM KAPSÜLLERİ
            # ---------------------------------------------------------
            active_font = getattr(self, "font3", getattr(self, "font", getattr(self, "font2", None)))

            for i, gun in enumerate(self.available_guns):
                orta_aci = i * aci + aci / 2
                radyan = math.radians(orta_aci)
                r = yari_cap * 0.65

                base_x = center[0] + math.cos(radyan) * r
                base_y = center[1] + math.sin(radyan) * r

                # Update fonksiyonundan hesaplanan yumuşak yukarı kayma
                anim_y = base_y - self.wheel_hover_offsets[i]

                # Silahı çiz
                if isinstance(gun, Sword):
                    gun: Sword

                    gun.draw(surface, int(base_x), int(anim_y), -90, trail=False)
                elif type(gun) == Gun:

                    gun.draw_copy(surface, int(base_x), int(anim_y))
                elif type(gun) == Charm:
                    
                    gun.draw(surface, int(base_x), int(anim_y))

                # İsim etiketi (hover anında görünür)
                offset = self.wheel_hover_offsets[i]
                if offset > 1.5:
                    gun_name = getattr(gun, "name", "Silah")
                    if callable(gun_name):
                        gun_name = gun_name()

                    text_str = str(gun_name)
                    if hasattr(active_font, "return_text"):
                        text_surf = active_font.return_text(text_str, (245, 250, 255))
                    elif hasattr(active_font, "render"):
                        text_surf, _ = active_font.render(text_str, (245, 250, 255), None)
                    else:
                        text_surf = pygame.font.Font(None, 24).render(text_str, True, (245, 250, 255))

                    badge_w = text_surf.get_width() + 20
                    badge_h = text_surf.get_height() + 10
                    badge_rect = pygame.Rect(0, 0, badge_w, badge_h)
                    badge_rect.center = (int(base_x), int(anim_y + 46))

                    pygame.draw.rect(surface, (12, 16, 24), badge_rect, border_radius=6)
                    pygame.draw.rect(surface, (0, 240, 255), badge_rect, width=2, border_radius=6)
                    surface.blit(text_surf, text_surf.get_rect(center=badge_rect.center))

        else:
            # Tek silah durumu
            gun = self.available_guns[0]
            anim_y = center[1] - self.wheel_hover_offsets[0]
            gun.draw(surface, int(center[0]), int(anim_y), angle=0, dashing=False)

            if self.wheel_hover_offsets[0] > 1.5:
                active_font = getattr(self, "font3", getattr(self, "font", None))
                gun_name = getattr(gun, "name", "Silah")
                text_str = str(gun_name() if callable(gun_name) else gun_name)
                text_surf = active_font.return_text(text_str, (245, 250, 255)) if hasattr(active_font, "return_text") else pygame.font.Font(None, 24).render(text_str, True, (245, 250, 255))
                surface.blit(text_surf, text_surf.get_rect(center=(center[0], anim_y + 45)))

    def update_available_guns(self, dt: float):
        parca_sayisi = len(self.available_guns)
        if parca_sayisi == 0:
            self.hovered_gun_index = -1
            return

        # Animasyon hafızasını başlat veya uzunluk değiştiyse eşitle
        if not hasattr(self, "wheel_hover_offsets") or len(self.wheel_hover_offsets) != parca_sayisi:
            self.wheel_hover_offsets = [0.0] * parca_sayisi

        center = (info.current_w / 2, info.current_h / 2)
        self.center_wheel = center
        yari_cap = 400

        # Fare pozisyonu ve merkeze göre uzaklık/açı hesabı
        mx, my = pygame.mouse.get_pos()
        dx = mx - center[0]
        dy = my - center[1]
        mouse_dist = math.hypot(dx, dy)

        self.hovered_gun_index = -1

        # Merkezdeki ölü alan (50px) ile çember sınırı arasında ise
        if 50 <= mouse_dist <= yari_cap and parca_sayisi > 1:
            fare_acisi = math.degrees(math.atan2(dy, dx)) % 360
            dilim_acisi = 360 / parca_sayisi
            self.hovered_gun_index = int(fare_acisi // dilim_acisi)
        elif mouse_dist <= yari_cap and parca_sayisi == 1:
            self.hovered_gun_index = 0

        # Her silahın yukarı kayma mesafesini (lerp) güncelle
        for i in range(parca_sayisi):
            target_offset = 24.0 if i == self.hovered_gun_index else 0.0
            self.wheel_hover_offsets[i] += (target_offset - self.wheel_hover_offsets[i]) * min(1.0, 14.0 * dt)

    def weapon_wheel_get_mouse(self, weapon_choosing: bool):
        if weapon_choosing:
            mx, my = pygame.mouse.get_pos()
            if self.center_wheel is None:
                return None
            dx = mx - self.center_wheel[0]
            dy = my - self.center_wheel[1]

            mesafe = math.hypot(dx, dy)
            if mesafe <= 400:
                aci = math.degrees(math.atan2(dy, dx))

                if aci < 0:
                    aci += 360

                secilen = int(aci // (360 / len(self.available_guns)))

                return secilen
        else:
            return None


    def _init_sounds(self):
        """Kayıttan yükleme veya başlatma anında sesleri sıfırdan bağlar."""

        sfx_dir = os.path.join(BASE_DIR, "sounds")
        self.step_timer = 0.0

        def load_sfx(filename, volume=1.0, pitch_range=(0.92, 1.08)):
            path = os.path.join(sfx_dir, filename)
            return SoundFX(path, volume=volume, pitch_range=pitch_range) if os.path.exists(path) else None

        # 1. Saldırı sesleri
        self.attack_swings = {
            0: load_sfx("swing_0.wav", volume=0.7, pitch_range=(0.95, 1.05)),
            1: load_sfx("swing_1.wav", volume=0.85, pitch_range=(0.90, 1.10)),
            2: load_sfx("swing_2.wav", volume=0.75, pitch_range=(0.92, 1.08)),
            3: load_sfx("swing_3.wav", volume=1.0, pitch_range=(0.85, 1.05)),
        }

        # 2. Tekil hareketler
        '''
        self.sfx_dash = load_sfx("dash.wav", volume=0.85, pitch_range=(0.95, 1.05))
        self.sfx_deflect = load_sfx("deflect.wav", volume=1.0, pitch_range=(0.90, 1.10))
        self.sfx_teleport_start = load_sfx("teleport_start.wav", volume=0.6)
        self.sfx_teleport_end = load_sfx("teleport_end.wav", volume=0.9)
        self.sfx_heal = load_sfx("heal.wav", volume=0.6)
        self.sfx_step = load_sfx("step.wav", volume=0.3, pitch_range=(0.85, 1.15))       
        '''


        # 3. Vuruş havuzu
        hit_files = [
            os.path.join(sfx_dir, f"stab_{i}.wav")
            for i in (1, 2, 3)
            if os.path.exists(os.path.join(sfx_dir, f"stab_{i}.wav"))
        ]
        self.hit_sfx_pool = SoundPoolFX(hit_files, volume=0.95, pitch_range=(0.88, 1.12)) if hit_files else None


    def __getstate__(self):
        state = self.__dict__.copy()
        state.pop("image", None)
        state.pop("rotated", None)
        state.pop("rotated_rect", None)
        state.pop("parlama_image", None)
        state.pop("parlama_image2", None)
        state.pop("parlama_image_orig", None)
        state.pop("anim", None)

        # Hayalet iz siliniyor
        self.ghost_trail.clear()
        
        # Tüm ses değişkenlerini pickle dışı bırakıyoruz:
        state.pop("attack_swings", None)
        state.pop("hit_sfx_pool", None)
        for sfx_name in ["sfx_dash", "sfx_deflect", "sfx_teleport_start", "sfx_teleport_end", "sfx_heal", "sfx_step"]:
            state.pop(sfx_name, None)

        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        if self.anim_dir and os.path.exists(self.anim_dir):
            self.anim = AnimationController(self.anim_dir, speeds=self.anim_speeds, target_scale=0.7 * SCALE)
            self.image = self.anim.get_frame(facing_left=(self.look_dir == "left"))
        else:
            self.anim = None
            self.image = pygame.image.load(self.image_name)

        self.rotated = None
        self.rotated_rect = None

        if pygame.display.get_surface() is not None:
            self.anim.convert_alpha()
            self.image.convert_alpha()

        self._init_sounds()


class World:

    def __init__(
            self,
            terrain_color: tuple,
            rock0: tuple,
            rock1: tuple,
            items: list,
            terrain_image: os.PathLike=None,
            dirt_image: os.PathLike=None, 
            theme: str = DefaultWorld(),
            levels: dict[
                Literal["levels", "levels_sword_map", "levels_item_map"],
                list[list["Enemy"]] | dict[str, Sword] | dict[str, Item]
            ] = None
        ):
        self.rocks = []
        self.rocks_rects = []

        self.theme = theme

        if type(self.theme) == DefaultWorld or self.theme == DefaultWorld:
            pass

        else:
            self.levels_data: dict[
                Literal["levels", "levels_sword_map", "levels_item_map"],
                list[list[Enemy]] | dict[str, Sword] | dict[str, Item]
            ] = levels or {}
            self.current_level = 0

        self.terrain_color = terrain_color
        self.rock0 = rock0
        self.rock1 = rock1
        self.rockChance = random.randint(3, 7)
        self.rockNum = random.randint(5, 13)
        self.items = copy.deepcopy(items)
        self.terrain_image_name = terrain_image

        if self.terrain_image_name:
            self.terrain_image = pygame.image.load(self.terrain_image_name)
            self.terrain_image = pygame.transform.scale(self.terrain_image, (info.current_w, info.current_w))
        else:
            self.terrain_image = None

        self.dirt_image_name = dirt_image
        if self.dirt_image_name:
            self.dirt_image = pygame.image.load(self.dirt_image_name)
            self.dirt_image = pygame.transform.scale(self.dirt_image, (info.current_w, info.current_h/5))
            self.dirt_rect = self.dirt_image.get_rect(topleft=(0, info.current_h/5*4))
        else:
            self.dirt_image = None
        self.id = str(uuid.uuid4())

    def create_rocks(self, screen_x: int, screen_y: int):
        for _ in range(self.rockNum):
            deneme = 0
            uyarildi = False
            while True:
                deneme += 1
                rolled = random.randint(0, 10)
                x = random.randint(0, screen_x)
                y = random.randint(0, screen_y)

                width = random.randint(scale(40), scale(125))
                height = random.randint(scale(20), scale(70))

                rect = pygame.Rect(x, y, width, height)

                if not rect.colliderect(self.dirt_rect):
                    if rolled < self.rockChance:
                        # GÖRSEL RECT: Çizim için tam boyut
                        # HITBOX: Köşe boşluklarından ve taşın tepesinden geçebilmek için
                        # genişlikten 14px, yükseklikten 10px kırpılmış taban kutusu
                        collision_rect = rect.inflate(-14, -10)
                        # Taban temasını hissettirmek için hitbox'ı hafif aşağı kaydır
                        collision_rect.centery = rect.centery + 3

                        rockData = {
                            "x": x,
                            "y": y,
                            "color": random.choice([self.rock0, self.rock1]),
                            "width": width,
                            "height": height,
                            "rect": rect,
                            "hitbox": collision_rect
                        }

                        self.rocks.append(rockData)
                        # Çarpışma listesine tam rect yerine optimize hitbox'ı ekle
                        self.rocks_rects.append(collision_rect)
                        break

                if deneme > 20 and not uyarildi:
                    logging.warning(f"Creating rocks try exceed 20. Try: {deneme}")
                if deneme > 50:
                    logging.error(f"Creating rocks limit. Try: {deneme}")
                    break

    def draw(self, screen: pygame.Surface):
        # 1. Zemin Çizimi
        if self.terrain_image_name:
            screen.blit(self.terrain_image, (0, 0))
        else:
            screen.fill(self.terrain_color)

        if self.dirt_image_name:
            screen.blit(self.dirt_image, (0, info.current_h / 5 * 4))

        # 2. Taşların Çizimi (HUD ile Birebir Uyumlu Stil)
        for rock in self.rocks:
            # Önceden tanımlı rect'i doğrudan kullan (her karede yeni Rect üretmeyip FPS korur)
            rock_rect = rock.get("rect")
            if rock_rect is None:
                rock_rect = pygame.Rect(rock["x"], rock["y"], rock["width"], rock["height"])

            base_color = rock["color"]
            
            # Taşın boyutuna göre estetik köşe kavisi (küçük taşlar bozulmaz)
            radius = max(6, min(14, rock_rect.height // 5))

            # -------------------------------------------------------------
            # ADIM 1: ZEMİN GÖLGESİ (HUD'daki Kapsül Gölgesi ile Aynı Mantık)
            # -------------------------------------------------------------
            # Hafif aşağı-sağa düşen koyu gölge (zemine temas hissi verir)
            shadow_rect = rock_rect.move(3, 6)
            shadow_color = colours.darker(self.terrain_color, 45)
            pygame.draw.rect(screen, shadow_color, shadow_rect, border_radius=radius)

            # -------------------------------------------------------------
            # ADIM 2: TAŞIN ANA GÖVDESİ
            # -------------------------------------------------------------
            pygame.draw.rect(screen, base_color, rock_rect, border_radius=radius)

            # -------------------------------------------------------------
            # ADIM 3: ALT DERİNLİK (3D Alt Gölgelendirme / Inset Bevel)
            # -------------------------------------------------------------
            # Taşın alt %35'lik dilimine düşen gölge
            bottom_shade_h = max(4, rock_rect.height // 3)
            bottom_shade_rect = pygame.Rect(
                rock_rect.left,
                rock_rect.bottom - bottom_shade_h,
                rock_rect.width,
                bottom_shade_h
            )
            pygame.draw.rect(
                screen,
                colours.darker(base_color, 35),
                bottom_shade_rect,
                border_bottom_left_radius=radius,
                border_bottom_right_radius=radius
            )

            # -------------------------------------------------------------
            # ADIM 4: ÜST CAM/KENAR IŞIĞI (Glossy Rim Highlight)
            # -------------------------------------------------------------
            # Üst kenara vuran açık renkli cilalı parıltı çizgisi
            pygame.draw.line(
                screen,
                colours.lighter(base_color, 55),
                (rock_rect.left + radius, rock_rect.top + 3),
                (rock_rect.right - radius, rock_rect.top + 3),
                width=3
            )

            # -------------------------------------------------------------
            # ADIM 5: KABARTMALI MİNERAL ÇATLAĞI (Embossed Facet)
            # -------------------------------------------------------------
            # İki katmanlı kırık çizgisi: koyu tarafı derinlik, açık tarafı parlama verir
            crack_x = rock_rect.left + int(rock_rect.width * 0.42)
            crack_y = rock_rect.top + int(rock_rect.height * 0.28)
            crack_len = int(rock_rect.width * 0.22)

            # Çatlağın gölgesi
            pygame.draw.line(
                screen,
                colours.darker(base_color, 45),
                (crack_x, crack_y),
                (crack_x + crack_len, crack_y + int(rock_rect.height * 0.35)),
                width=2
            )
            # Çatlağın ışık vuran kenarı (1 piksel yukarısı)
            pygame.draw.line(
                screen,
                colours.lighter(base_color, 45),
                (crack_x, crack_y - 1),
                (crack_x + crack_len, crack_y + int(rock_rect.height * 0.35) - 1),
                width=1
            )

            # -------------------------------------------------------------
            # ADIM 6: DIŞ ÇERÇEVE KONTURU (Netlik ve Ayırt Edilebilirlik)
            # -------------------------------------------------------------
            pygame.draw.rect(
                screen,
                colours.darker(base_color, 60),
                rock_rect,
                width=2,
                border_radius=radius
            )
    
    def draw_items(self, surface: pygame.Surface, font: userFont, player):
        for item in self.items:
            item.draw(surface, font, player)

    def update(self, enemy_list: list):
        self.items = [
            item for item in self.items
            if not item.used
        ]
        enemy_list = [
            enemy for enemy in enemy_list
            if enemy.living
        ]
        return enemy_list

    def next_level(self) -> tuple[list["Enemy"], Sword | NoSword, list[Item] | NoItem] | Literal[True] | DefaultWorld:
        if type(getattr(self, "current_level", False)) == int:
            self.current_level += 1

            try:
                level = self.levels_data["levels"][self.current_level]
                sword = self.levels_data["levels_sword_map"].get(f"level{self.current_level + 1}", NoSword())
                items = self.levels_data["levels_item_map"].get(f"level{self.current_level + 1}", NoItem())

                return level, sword, items

            except IndexError:
                win = True
                return win

            except Exception as e:
                print(f"Bilinmeyen hata: {e}")
                logging.error(f"Getting next level on world caused error:")
                logging.exception(e)

                raise LevelPrepareError(self.current_level, e)

        else:
            return DefaultWorld()

    def __getstate__(self):
        state = self.__dict__.copy()
        if state.get("terrain_image"):
            del state["terrain_image"]
        if state.get("dirt_image"):
            del state["dirt_image"]
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        if self.terrain_image_name:
            self.terrain_image = pygame.image.load(self.terrain_image_name)
            self.terrain_image = pygame.transform.scale(self.terrain_image, (info.current_w, info.current_w))
        if self.dirt_image_name:
            self.dirt_image = pygame.image.load(self.dirt_image_name)
            self.dirt_image = pygame.transform.scale(self.dirt_image, (info.current_w, info.current_h/5))


class Arrow:

    def __init__(self, x, y, image_name: str, attack=10):
        self.x = x
        self.y = y
        self.attack = attack
        self.rotated = None
        self.image_name = image_name
        self.image = pygame.image.load(self.image_name).convert_alpha()
        self.image = pygame.transform.scale_by(self.image, SCALE)

        self.image_rect = self.image.get_rect()
        self.rotated_rect = None
        self.touching = False
        self.angle = 360
        self.speed = scale(450)

    def update(self, player: Player, dt):
    
        self.mx, self.my = player.x, player.y

        self.dx = self.mx - self.x
        self.dy = self.my - self.y

        self.distance = math.hypot(self.dx, self.dy)
        if self.distance > 2:
            new_x = self.x + (self.dx / self.distance) * self.speed * dt
            new_y = self.y + (self.dy / self.distance) * self.speed * dt
            self.image_rect = self.image.get_rect(topleft=(new_x, new_y))
            if self.rotated_rect is None:
                self.x += (self.dx / self.distance) * self.speed * dt
                self.y += (self.dy / self.distance) * self.speed * dt
            else:
                self.rotated_rect.topleft = (new_x, new_y)
                self.x += (self.dx / self.distance) * self.speed * dt
                self.y += (self.dy / self.distance) * self.speed * dt
        else:
            self.touching = True
        self.angle = math.degrees(math.atan2(-self.dy, self.dx))
        self.rotated = pygame.transform.rotate(self.image, self.angle)
        self.rotated_rect = self.rotated.get_rect(center=(self.x, self.y))
        if self.touching:
            player.hp -= self.attack
    
    def draw(self, surface: pygame.Surface):
        if self.rotated_rect is not None:
            surface.blit(self.rotated, self.rotated_rect)
        else:
            surface.blit(self.image, (self.x, self.y))
    
    def __getstate__(self):
        state = self.__dict__.copy()
        if state.get("image"):
            del state["image"]
            del state["rotated"]
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.image = pygame.image.load(self.image_name).convert_alpha()


class Bomb:
    def __init__(self, attack, x, y, color=colours.YELLOW, radius=200, progress_per_sec = 23):
        self.attack = attack
        self.x = x
        self.y = y
        self.progress = 0
        self.color = color
        self.radius = radius
        self.progress_per_sec = progress_per_sec
        self.rect = None
        self.deleted = False

    def draw(self, surface: pygame.Surface):
        pygame.draw.circle(surface, self.color, (self.x, self.y), self.radius, 4)
        pygame.draw.circle(
            surface,
            colours.lighter(self.color, 40),
            (self.x, self.y),
            self.radius / 100 * self.progress
        )
        self.rect = pygame.Rect(0, 0, self.radius / 2, self.radius / 2)
        self.rect.center = (self.x, self.y)
    
    def update(self, player, dt):
        player: Player
        self.progress += self.progress_per_sec * dt
        if self.progress >= 100:
            if self.rect.colliderect(player.image_rect):
                player.hp -= self.attack
            self.deleted = True


class SplitGround:
    __slots__ = (
        "x", "y", "pos",
        "attack",
        "image_name",
        "image",
        "angle",
        "destroyed",
        "copy_cd",
        "orig_copy_cd",
        "player_x",
        "player_y",
        "speed",
        "copies",
        "copy_master",
        "image_rect",
        "destroy_cd",
        "vx",
        "vy",
        "copied",
    )

    def __init__(
        self,
        attack: int,
        x,
        y,
        image_name: os.PathLike,
        angle: int,
        player_x,
        player_y,
        copy_cd=0.04,
        *,
        image=None,
        copied=False
    ):
        self.x = x
        self.y = y
        self.pos = (x, y)

        self.attack = attack
        self.image_name = image_name
        self.angle = angle

        # Aynı image Surface'i paylaş
        if image is None:
            image = pygame.transform.scale_by(pygame.image.load(image_name).convert_alpha(), SCALE)
            image = pygame.transform.rotate(image, angle)

        self.image = image

        self.destroyed = False

        self.copy_cd = copy_cd
        self.orig_copy_cd = copy_cd

        self.player_x = player_x
        self.player_y = player_y

        self.copied = copied
        self.copy_master = None

        # Sadece ana SplitGround kopya listesi tutar
        self.copies = [] if not copied else None

        self.speed = scale(700)
        self.destroy_cd = 2.3

        self.image_rect = self.image.get_rect(
            midtop=(x, y)
        )

        dx = player_x - x
        dy = player_y - y
        distance = math.hypot(dx, dy)

        if distance:
            self.vx = dx / distance
            self.vy = dy / distance
        else:
            self.vx = 0
            self.vy = 0

    def create_copy(self):
        """
        deepcopy yerine sadece gerekli bilgileri kullanarak
        hafif bir kopya oluşturur.
        """

        dx = self.player_x - self.x
        dy = self.player_y - self.y

        distance = math.hypot(dx, dy)

        if distance:
            x = self.x + (dx / distance) * 10
            y = self.y + (dy / distance) * 10
        else:
            x = self.x
            y = self.y

        return SplitGround(
            attack=self.attack,
            x=x,
            y=y,
            image_name=self.image_name,
            angle=self.angle,
            player_x=self.player_x,
            player_y=self.player_y,
            copy_cd=self.orig_copy_cd,
            image=self.image,
            copied=True
        )

    def draw(self, surface: pygame.Surface):
        if self.destroyed:
            return

        surface.blit(self.image, self.image_rect)

        # Recursive draw yerine düz liste
        if self.copies:
            for sg in self.copies:
                if not sg.destroyed:
                    surface.blit(
                        sg.image,
                        sg.image_rect
                    )

    def update(self, dt):

        if self.destroyed:
            return

        self.destroy_cd -= dt

        if self.destroy_cd <= 0:
            self.destroyed = True

            # Ana objenin kopyalarını da temizle
            if self.copies:
                self.copies.clear()

            return

        # Hareket
        movement = self.speed * dt

        self.x += self.vx * movement
        self.y += self.vy * movement

        self.image_rect.midtop = (
            self.x,
            self.y
        )

        # Kopyalama
        self.copy_cd -= dt

        if self.copy_cd <= 0:

            new_copy = self.create_copy()

            self.copies.append(new_copy)

            self.copy_cd = self.orig_copy_cd

    def update_collision(self, player: Player):

        if self.destroyed:
            return

        # Ana obje
        if player.image_rect.colliderect(self.image_rect):
            player.hp -= self.attack
            self.destroyed = True
            return

        # Kopyalar
        if not self.copies:
            return

        for sg in self.copies:

            if sg.destroyed:
                continue

            if player.image_rect.colliderect(sg.image_rect):
                player.hp -= sg.attack
                sg.destroyed = True

                # Senin eski kodundaki davranışı koruyor:
                # ana obje de yok oluyor.
                self.destroyed = True

                break

    def __getstate__(self):
        state = {}

        for slot in self.__slots__:
            value = getattr(self, slot)

            # pygame Surface pickle edilmesin
            if slot != "image":
                state[slot] = value

        return state

    def __setstate__(self, state):

        for key, value in state.items():
            setattr(self, key, value)

        self.image = pygame.image.load(
            self.image_name
        ).convert_alpha()

        self.image = pygame.transform.rotate(
            self.image,
            self.angle
        )


class SCRLazerBeam:
    def __init__(self, attack, color: tuple[int, int, int], start_pos: tuple, end_pos: tuple):
        self.duration = Cooldown(1.4)
        self.attack = attack
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.color = color
        self.dark_color = colours.darker(self.color, 50)
        self.rect = None
        self.destroyed = False

        self.damage_cd = Cooldown(0.9)
        self.damage_cd.cooldown = 0

    def draw(self, surface: pygame.Surface):
        if self.destroyed: return

        self.rect = pygame.draw.line(
            surface,
            self.color,
            self.start_pos,
            self.end_pos,
            info.current_w // 300
        )

        pygame.draw.line(
            surface,
            self.dark_color,
            self.start_pos,
            self.end_pos,
            int(info.current_w // 250 * (self.duration.cooldown / self.duration.durations[0]))
        )

    def update(self, player: Player, dt):
        self.duration.reduce(dt)
        self.damage_cd.reduce(dt)

        if self.duration.check():
            self.destroyed = True
            return

        if self.rect is not None:
            if self.rect.colliderect(player.image_rect) and not self.destroyed and self.damage_cd.check():
                player.hp -= self.attack
                self.damage_cd.refresh()


class Sneeze:
    def __init__(self):
        self.x = random.randint(0, info.current_w)
        self.y = random.randint(0, info.current_h)

        self.radius = info.current_w // 100

        self.rect = pygame.Rect(
            self.x, self.y, self.radius, self.radius
        )

        self.moving = False

        self.deleted = False
        self.wait_cd = Cooldown(3)

    def draw(self, surface: pygame.Surface):
        if self.deleted: return

        pygame.draw.circle(
            surface,
            colours.darker((0, 255, 0), random.randint(3, 70)),
            (self.x, self.y),
            self.radius
        )

        pygame.draw.circle(
            surface,
            colours.darker((0, 255, 0), 120),
            (self.x, self.y),
            self.radius,
            4
        )

    def update(self, dt, player: Player):
        if self.deleted: return

        self.wait_cd.reduce(dt)

        if self.wait_cd.check():
            self.moving = True

        if self.moving:
            # 1. Oyuncunun merkezine olan uzaklık farkı
            dx = player.x - self.x
            dy = player.y - self.y

            # 2. Aradaki açıyı hesapla (radyan cinsinden)
            angle = math.atan2(dy, dx)

            # 3. cos yatay ekseni, sin dikey ekseni temsil eder
            self.x += math.cos(angle) * 700 * dt
            self.y += math.sin(angle) * 700 * dt

            self.rect.center = (self.x, self.y)

            if player.image_rect.colliderect(self.rect):
                player.hp -= 0.02
                self.deleted = True


class EnemyAbilities(Enum):
    ABILITY_BOMBING = auto()
    ABILITY_ARROWS = auto()
    ABILITY_SNEEZE = auto()
    ABILITY_SPLIT_GROUND = auto()
    ABILITY_CAT_JUMP = auto()
    ABILITY_SCR_LAZER_BEAM = auto()

print(type(EnemyAbilities.ABILITY_ARROWS))


class Enemy:
    THEMES = {
        "arrow": {
            "core": (255, 60, 60),      # Kırmızı (Standart ok)
            "glow": (255, 20, 40),
            "duration": 2
        },
        "bombing": {
            "core": (255, 170, 30),     # Turuncu / Altın (Ağır darbe)
            "glow": (255, 110, 0),
            "duration": 1.75
        },
        "split_ground": {
            "core": (60, 58, 58),     # Mor / Eflatun (Büyü atışı)
            "glow": (43, 39, 39),
            "duration": 1.3
        },
        "cat_jump": {
            "core": (70, 245, 110),     # Zehir Yeşili
            "glow": (30, 200, 70),
            "duration": 0.9
        },
        "scr_lazer_beam": {
            "core": (80, 220, 255),     # Neon Cyan (Hızlı elektrik atışı)
            "glow": (20, 160, 255),
            "duration": 3.2
        }
    }

    VAL_MNGR = None

    DAMAGE_SWORD_DASH = "4"
    DAMAGE_BULLET = "5"
    DAMAGE_BRONZE_BULLET = "6"
    DAMAGE_SILVER_BULLET = "7"
    DAMAGE_BRONZE_GUN = "8"
    DAMAGE_SILVER_GUN = "9"
    DAMAGE_SWORD = "10"
    
    def __init__(
            self,
            hp: int,
            attack: int,
            abilities: list = None,
            r_image_name: os.PathLike = os.path.join(BASE_DIR,"images/enemyr.png"),
            l_image_name: os.PathLike = os.path.join(BASE_DIR, r"images/enemyl.png"),
            size = 100,
            speed=300,
            damage_cooldown: Cooldown=Cooldown(2),
            cooldown: Cooldown = Cooldown(10),
            collisions=True,
            damagables=[
                DAMAGE_BULLET,
                DAMAGE_BRONZE_GUN,
                DAMAGE_SILVER_GUN,
                DAMAGE_SWORD_DASH,
                DAMAGE_SWORD
            ],
            cooldown_arrow: Cooldown = None,
            arrow_image=os.path.join(BASE_DIR,r"images/arrow.png"),
            drops: list = None
        ):

        self.hp = hp
        self.x = None
        self.y = None

        self.origin_hp = hp
        self.attack = attack
        self.living = True
        self.rimage_name = r_image_name
        self.limage_name = l_image_name
        self.image_size = size

        fallback_r = os.path.join(BASE_DIR, r"images/fallback_enemyr.png")
        fallback_l = os.path.join(BASE_DIR, r"images/fallback_enemyr.png")

        try:
            self.image_r = pygame.image.load(self.rimage_name)

        except FileNotFoundError:
            self.image_r = pygame.image.load(fallback_r)

        try:
            self.image_l = pygame.image.load(self.limage_name)

        except FileNotFoundError:
            self.image_l = pygame.image.load(fallback_l)

        # Ekranın yüzde kaçını kaplayacak
        screen_fill_percentage = 0.06

        base_target_h = int(1080 * screen_fill_percentage * (self.image_size / 100.0))  # 1080p için ideal boy
        target_h = max(30, int(base_target_h * SCALE))

        # En-boy oranını bozmadan ölçekle:
        ratio_r = target_h / self.image_r.get_height()
        target_w_r = int(self.image_r.get_width() * ratio_r)
        self.image_r = pygame.transform.smoothscale(self.image_r, (target_w_r, target_h))

        ratio_l = target_h / self.image_l.get_height()
        target_w_l = int(self.image_l.get_width() * ratio_l)
        self.image_l = pygame.transform.smoothscale(self.image_l, (target_w_l, target_h))

        self.uimage = self.image_r
        self.speed = scale(speed)
        self.image_rect = self.uimage.get_rect()
        self.rotated_rect = None
        self.angle = 0
        self.damaged = False
        self.damage_cooldown = damage_cooldown

        self.abilities = abilities if abilities is not None else []

        assert type(self.abilities) == list, f"{self}.abilities is not list"

        self.arrow_image_name = arrow_image

        self.arrow_image = pygame.image.load(self.arrow_image_name)
        self.arrow_image = pygame.transform.scale_by(self.arrow_image, SCALE)

        self.rotated_rect_arrow = self.arrow_image.get_rect()
        self.arrows = []
        self.origin_cooldown = cooldown
        self.cooldown = self.origin_cooldown
        self.arrow_cooldown = cooldown_arrow
        self.summon_cooldown = self.origin_cooldown
        self.summoned = False
        self.bombing_cooldown = self.origin_cooldown + 3
        self.split_ground_cd = self.origin_cooldown + 2
        self.cat_jump_cd = self.origin_cooldown + 4

        self.scr_lazer_beam_cd = self.origin_cooldown + 6
        self.lazer_beam_inside_cd = Cooldown(0.1)
        self.scr_lazer_beam_counter = 0

        self.cat_jumping = False
        self.bombs = []
        self.drops = drops or []
        self.collisions = collisions
        self.damagables = damagables
        self.id = str(uuid.uuid4())
        self.sgrounds: list[SplitGround] = []
        self.recoil = 0
        self.recoil_dir = None
        self.cat_jumping_y_dir = "up"
        self.c_jump_player_pos = None
        self.c_jumping_duration = Cooldown(2)
        self.c_jump_dx = None

        self.scr_lazers: list[SCRLazerBeam] = []
        self.scr_lazer_beam_firing = False  # Lazerler yaylım ateşindeyken True olur

        self.claimed_death = False

        self.mx = 0
        self.my = 0
        self.telegraph = EnemyTelegraph()
        self.charging_ability = None

        self.sneeze: list[Sneeze] = []
        self.flash_timer = 0.0 # Darbe beyazlama sayacı

    @classmethod
    def set_val_manager(cls, val_manager: ValueManager):
        cls.VAL_MNGR = val_manager

    def set_pos(self, world, info):
        for _ in range(1000):
            x = random.randint(200, info.current_w - 200)
            y = random.randint(200, info.current_h - 200)

            rect = pygame.Rect(x, y, self.uimage.get_width(), self.uimage.get_height())

            if rect.collidelist(world.rocks_rects) == -1 and not rect.colliderect(world.dirt_rect):
                self.x = x
                self.y = y
                return
        level = "Unknown"

        for name, variable in globals().items():
            if isinstance(variable, dict):
                for in_var in variable.values():
                    if in_var == world:
                        level = variable.get("Level", "Unknown")

        raise EnemyPositionError(self.id, _, level)
    
    def update_arrows(self, player: Player, dt):
        for arrow in self.arrows:
            arrow.update(player, dt)
        # Güvenli ve hızlı toplu temizlik (Döngü içinde silme yok)
        self.arrows = [a for a in self.arrows if not a.touching]

    def update_bombs(self, player: Player, dt):
        for bomb in self.bombs:
            bomb.update(player, dt)
        self.bombs = [b for b in self.bombs if not b.deleted]
    
    def update_sgrounds(self, player: Player, dt):
        for sg in self.sgrounds:
            sg: SplitGround
            sg.update(dt)
            sg.update_collision(player)

    def update_cat_jump(self, player: Player, dt):
        if self.cat_jumping:
            self.c_jumping_duration.reduce(dt)

            if self.c_jumping_duration.check():
                self.cat_jumping = False
                player.movable = True
                return

            if self.cat_jumping_y_dir == "up":
                self.y -= 200 * dt
            elif self.cat_jumping_y_dir == "down":
                self.y += 200 * dt

            dx = self.c_jump_player_pos[0] - self.x

            if abs(self.c_jump_dx / 2) > abs(dx):
                self.cat_jumping_y_dir = "down"
            
            self.x += 850 * dt if dx > 0 else -850 * dt

            self.image_rect = self.uimage.get_rect(topleft=(self.x, self.y))
            self.rect = self.uimage.get_rect(topleft=(self.x, self.y))

            if player.image_rect.colliderect(self.image_rect):
                player.movable = False
                player.hp -= int(30 * dt)

    def update_scr_lazers(self, player: Player, dt):
        for scr_l_b in self.scr_lazers:
            scr_l_b.update(player, dt)
    
    def update_sneezes(self, player: Player, dt):
        for sneeze in self.sneeze:
            sneeze.update(dt, player)
        # Bellek sızıntısını önleyen satır:
        self.sneeze = [s for s in self.sneeze if not s.deleted]
    
    def draw_arrows(self, surface: pygame.Surface):
        for arrow in self.arrows:
            arrow.draw(surface)
    
    def draw_bombs(self, surface: pygame.Surface):
        for bomb in self.bombs:
            bomb: Bomb
            bomb.draw(surface)
    
    def draw_sgrounds(self, surface: pygame.Surface):
        for sg in self.sgrounds:
            sg: SplitGround
            sg.draw(surface)

    def draw_scr_lazers(self, surface: pygame.Surface):
        for scr_l_b in self.scr_lazers:
            scr_l_b.draw(surface)

    def draw_sneezes(self, surface):
        for sneeze in self.sneeze:
            sneeze.draw(surface)
    
    def use_arrow(self, dt):
            if EnemyAbilities.ABILITY_ARROWS not in self.abilities or not self.living:
                return

            cd = self.arrow_cooldown if self.arrow_cooldown is not None else self.cooldown

            # Eğer başka bir yeteneğin ünlemi yanıyorsa bekle
            if self.charging_ability is not None and self.charging_ability != "arrow":
                return

            # Ünlem şarjı devrede mi?
            if self.charging_ability == "arrow":
                if self.telegraph.update(dt):
                    # Ünlem doldu -> Oku fırlat, Cooldown yenile ve ünlemi kapat!
                    self.arrows.append(Arrow(self.x, self.y, self.arrow_image_name))
                    cd.refresh()
                    self.charging_ability = None
                return

            # Normal Cooldown sayacı
            cd.reduce(dt)
            if cd.check():
                # Cooldown bitti! Hemen oku atmak yerine kafasında KIRMIZI ÜNLEM yak
                self.charging_ability = "arrow"
                self.telegraph.start_charge("arrow", self.THEMES)

    def use_bombing(self, dt, player: Player):
        if EnemyAbilities.ABILITY_BOMBING not in self.abilities or not self.living:
            return

        if self.charging_ability is not None and self.charging_ability != "bombing":
            return

        if self.charging_ability == "bombing":
            if self.telegraph.update(dt):
                self.bombs.append(Bomb(24, player.x, player.y))
                self.bombing_cooldown.refresh()
                self.charging_ability = None
            return

        self.bombing_cooldown.reduce(dt)
        if self.bombing_cooldown.check():
            self.charging_ability = "bombing"
            self.telegraph.start_charge("bombing", self.THEMES)

    def use_split_ground(self, dt, player: Player):
        if EnemyAbilities.ABILITY_SPLIT_GROUND not in self.abilities or not self.living:
            return

        if self.charging_ability is not None and self.charging_ability != "split_ground":
            return

        if self.charging_ability == "split_ground":
            if self.telegraph.update(dt):
                dx, dy = self.x - player.x, self.y - player.y
                self.sgrounds.append(
                    SplitGround(
                        46, self.x, self.y,
                        os.path.join(BASE_DIR, r"images/splitground_noback.png"),
                        math.degrees(math.atan2(-dy, dx)),
                        player.x, player.y
                    )
                )
                self.split_ground_cd.refresh()
                self.charging_ability = None
            return

        self.split_ground_cd.reduce(dt)
        if self.split_ground_cd.check():
            self.charging_ability = "split_ground"
            self.telegraph.start_charge("split_ground", self.THEMES)

    # -------------------------------------------------------------
    # 4. KEDİ ZIPLAMASI (YEŞİL LAZER)
    # -------------------------------------------------------------
    def use_cat_jump(self, dt, player: Player):
        if EnemyAbilities.ABILITY_CAT_JUMP not in self.abilities or not self.living:
            return

        # Kedi zaten havada zıplıyorsa yeni bir ünlem açma
        if getattr(self, "cat_jumping", False):
            return

        if self.charging_ability is not None and self.charging_ability != "cat_jump":
            return

        if self.charging_ability == "cat_jump":
            if self.telegraph.update(dt):
                self.c_jump_player_pos = (player.x, player.y)
                self.cat_jumping = True
                self.c_jump_dx = self.c_jump_player_pos[0] - self.x
                self.c_jumping_duration.refresh()
                self.cat_jump_cd.refresh()
                self.charging_ability = None
            return

        self.cat_jump_cd.reduce(dt)
        if self.cat_jump_cd.check():
            self.charging_ability = "cat_jump"
            self.telegraph.start_charge("cat_jump", self.THEMES)

    # -------------------------------------------------------------
    # 5. SCR LAZER YAĞMURU (CYAN LAZER)
    # -------------------------------------------------------------
    def use_scr_lazer_beam(self, dt, player: Player = None):
        if EnemyAbilities.ABILITY_SCR_LAZER_BEAM not in self.abilities or not self.living:
            return

        # Başka bir yeteneğin ünlemi devredeyse bekle
        if self.charging_ability is not None and self.charging_ability != "scr_lazer_beam":
            return

        # AŞAMA 1: TELEGRAPH / ÜNLEM ŞARJI
        if self.charging_ability == "scr_lazer_beam":
            if self.telegraph.update(dt):
                # Ünlem bitti -> Ateşleme modunu aç, ünlem durumunu kapat!
                self.charging_ability = None
                self.scr_lazer_beam_firing = True
            return

        # AŞAMA 2: ATEŞLEME MODU (10 Tane Lazer Tek Tek Çıkıyor)
        if getattr(self, "scr_lazer_beam_firing", False):
            self.lazer_beam_inside_cd.reduce(dt)

            if self.lazer_beam_inside_cd.check():
                self.scr_lazers.append(
                    SCRLazerBeam(
                        5,
                        colours.lighter(colours.BLUE, 75),
                        (0, random.randint(0, info.current_h)),
                        (info.current_w, random.randint(0, info.current_h))
                    )
                )
                self.lazer_beam_inside_cd.refresh()
                self.scr_lazer_beam_counter += 1

            if self.scr_lazer_beam_counter >= 7:
                self.scr_lazer_beam_cd.refresh()
                self.lazer_beam_inside_cd.refresh()
                self.scr_lazer_beam_counter = 0
                self.scr_lazer_beam_firing = False  # Ateşleme bitti, cooldown başladı
            return

        # AŞAMA 3: NORMAL COOLDOWN SAYACI
        self.scr_lazer_beam_cd.reduce(dt)
        if self.scr_lazer_beam_cd.check():
            # Cooldown bitti -> Ateşlemeye geçmeden önce kafada Mavi Ünlem yak!
            self.charging_ability = "scr_lazer_beam"
            self.telegraph.start_charge("scr_lazer_beam", self.THEMES)

    def use_sneeze(self):
        if EnemyAbilities.ABILITY_SNEEZE not in self.abilities or not self.living: return

        if random.randint(0, 150) == 150:
            for i in range(10):
                self.sneeze.append(
                    Sneeze()
                )

    def copy(self):
        new_copy = copy.deepcopy(self)
        new_copy.id = str(uuid.uuid4())  # Her klona benzersiz yeni bir ID verilir
        return new_copy

    def summon(self, dt, level: dict, world, pending_enemies: list):
        pass


    @staticmethod
    def draw(surface: pygame.Surface, font: userFont, level: list, bossFont: userFont = None):
        for enemy in level:
            enemy: Enemy
            if enemy.living:

                if type(enemy) == Boss: continue

                head_x = enemy.x + (enemy.uimage.get_width() / 2)
                head_y = enemy.y
                enemy.telegraph.draw(surface, (head_x, head_y))

                font.draw_text(str(max(0, enemy.hp)), (enemy.x+enemy.uimage.get_width()/2, enemy.y-10), surface, colours.BLACK, hiza="center")
                surface.blit(enemy.uimage, (enemy.x, enemy.y))
    
    @classmethod
    def default(cls):
        return cls(100, 10, [])
    
    @classmethod
    def miguel(cls):
        return cls(
            500,
            35,
            [EnemyAbilities.ABILITY_BOMBING],
            r_image_name=os.path.join(BASE_DIR,r"images/miguelr.png"),
            l_image_name=os.path.join(BASE_DIR,r"images/miguell.png"),
            speed=270,
            damagables=[Enemy.DAMAGE_SWORD_DASH, Enemy.DAMAGE_SILVER_BULLET],
            drops=[Item("Miguel'in Kanı", colours.RED, [Effect("hp", 15, -1)], Item.YUVARLAK_IKSIR, Item.APPENDER)],
            size=105
        )

    @classmethod
    def luffy(cls):
        return cls(
            300,
            25,
            r_image_name=os.path.join(BASE_DIR,r"images/luffyr.png"),
            l_image_name=os.path.join(BASE_DIR,r"images/luffyl.png"),
            speed=420,
            damagables=[Enemy.DAMAGE_SWORD_DASH],
            size=95
        )
    
    @classmethod
    def dinosaur(cls):
        return cls(
            1000,
            60,
            r_image_name=os.path.join(BASE_DIR,r"images/urasr.png"),
            l_image_name=os.path.join(BASE_DIR,r"images/urasl.png"),
            speed=210,
            size=230,
            abilities=[EnemyAbilities.ABILITY_SPLIT_GROUND],
            collisions=False,
            cooldown=Cooldown(4)
        )

    @classmethod
    def skzoo(cls, player=None, special=False):
        player: Player
        return cls(
            700,
            50,
            r_image_name=os.path.join(BASE_DIR,r"images/denizinseyir.png"),
            l_image_name=os.path.join(BASE_DIR,r"images/denizinseyil.png"),
            speed=350,
            size=110,
            abilities=[],
            damagables=[Enemy.DAMAGE_SWORD_DASH, Enemy.DAMAGE_BRONZE_GUN, Enemy.DAMAGE_SILVER_GUN, Enemy.DAMAGE_SILVER_BULLET],
            drops=[Effect("hp", 0, -1, player.available_guns, [Charm("Deniz'in şeyi", os.path.join(BASE_DIR,r"images/denizinseyir.png"), 0.09, [Effect("heal_cooldown_orig", 0.75, -1, flags=(Item.EQUALER,))], [Effect("hp", 15, -1, flags=(Item.APPENDER,))], 0.45)], (Item.APPENDER))] if special else []
        )

    @classmethod
    def floppa(cls):
        return cls(
            250,
            14,
            r_image_name=os.path.join(BASE_DIR, r"images/floppa.png"),
            l_image_name=os.path.join(BASE_DIR, r"images/floppa.png"),
            speed = 450,
            abilities=[EnemyAbilities.ABILITY_CAT_JUMP],
            damagables = [Enemy.DAMAGE_SWORD_DASH, Enemy.DAMAGE_BRONZE_GUN, Enemy.DAMAGE_BRONZE_BULLET],
            size = 150
        )

    @classmethod
    def morty(cls):
        return cls(
            400,
            56,
            [EnemyAbilities.ABILITY_SCR_LAZER_BEAM],
            os.path.join(BASE_DIR, r"images/evil-mortyr.png"),
            os.path.join(BASE_DIR, r"images/evil-mortyl.png")
        )

    def update(self, player: Player, world: World, dt, level: list, cheated=False):
        if self.flash_timer > 0:
            self.flash_timer -= dt

        if not self.cat_jumping:

            self.mx, self.my = player.x, player.y
            if self.recoil > 0:

                if self.recoil_dir == "right":
                    new_x = self.x + (self.speed + scale(500)) * dt

                elif self.recoil_dir == "left":
                    new_x = self.x - (self.speed + scale(500)) * dt

                self.image_rect = self.uimage.get_rect(topleft=(new_x, self.y))
                if not self.image_rect.collidelist(world.rocks_rects) != -1 or not self.collisions:
                    self.x = new_x

                self.recoil -= 1 * dt

            try:
                self.dx = self.mx - self.x
                self.dy = self.my - self.y
            except TypeError:
                self.set_pos(world, info)
                self.dx = self.mx - self.x
                self.dy = self.my - self.y

            self.distance = math.hypot(self.dx, self.dy)

            if self.distance > 0:

                new_x = self.x + (self.dx / self.distance) * self.speed * dt
                new_y = self.y + (self.dy / self.distance) * self.speed * dt
                self.image_rect = self.uimage.get_rect(topleft=(new_x, new_y))
                self.rect = self.uimage.get_rect(topleft=(new_x, new_y))
        
                if self.rotated_rect is None:
                    if not self.image_rect.collidelist(world.rocks_rects) != -1 or not self.collisions:
                        self.x += (self.dx / self.distance) * self.speed * dt
                        self.y += (self.dy / self.distance) * self.speed * dt
                
                else:
                    self.rotated_rect.topleft = (new_x, new_y)
                    if not self.rotated_rect.collidelist(world.rocks_rects) != -1 or not self.collisions:
                        self.x += (self.dx / self.distance) * self.speed * dt
                        self.y += (self.dy / self.distance) * self.speed * dt

            else:
                self.touching = True
        self.angle = math.degrees(math.atan2(-self.dy, self.dx))

        if -45 < self.angle < 45:
            self.uimage = self.image_r

        elif self.angle < -135 or self.angle > 135:
            self.uimage = self.image_l


        self.update_sgrounds(player, dt)
        self.sgrounds = [sg for sg in self.sgrounds if not sg.destroyed]
        self.scr_lazers = [scr_lazer for scr_lazer in self.scr_lazers if not scr_lazer.destroyed]
        self.sneeze = [sneeze for sneeze in self.sneeze if not sneeze.deleted]

        if self.hp <= 0:
            self.telegraph.cancel()

            if not self.claimed_death and Enemy.VAL_MNGR is not None and not cheated:
                Enemy.VAL_MNGR("kill", 1, "change")
                self.claimed_death = True

            self.living = False
            self.summoned = False
            self.drops: list
            for drop in self.drops:
                if type(drop) == Sword or type(drop) == Gun:
                    player.available_guns.append(drop)
                elif type(drop) == Item:
                    drop.set_pos(world)
                    world.items.append(drop)
                elif type(drop) == Effect:
                    drop.use(player, ())
                elif type(drop) == Enemy:
                    level.append(drop)
            self.drops.clear()
            return
    
    @classmethod
    def prepared_police(cls):
        return cls(
        450,
        34,
        r_image_name=os.path.join(BASE_DIR,r"images/enemy_policer.png"),
        l_image_name=os.path.join(BASE_DIR,r"images/enemy_policel.png"),
        speed=280,
        damage_cooldown=Cooldown(1.7),
        damagables=[
            Enemy.DAMAGE_BRONZE_GUN,
            Enemy.DAMAGE_SILVER_GUN,
            Enemy.DAMAGE_SWORD_DASH,
            Enemy.DAMAGE_SILVER_BULLET
        ]
    )

    @classmethod
    def prepared_old(cls, random_speed=False, hp=40):
        if random_speed:
            speed = random.randint(350, 380)

        return cls(
            hp,
            2,
            r_image_name=os.path.join(BASE_DIR,r"images/enemy_oldr.png"),
            l_image_name=os.path.join(BASE_DIR, r"images/enemy_oldl.png"),
            size=70,
            speed=speed if random_speed else 360,
            damage_cooldown=Cooldown(2.1),
            damagables=[
                Enemy.DAMAGE_BULLET,
                Enemy.DAMAGE_BRONZE_GUN,
                Enemy.DAMAGE_SILVER_GUN,
                Enemy.DAMAGE_SWORD_DASH,
                Enemy.DAMAGE_SWORD
            ]
        )

    def damage(self, player: Player, dt):
        self.damage_cooldown.reduce(dt)

        if self.damage_cooldown.check():
            self.damaged = False

        if not self.damaged and self.living:
            if not player.drawing and not player.sword_attacking:
                if self.image_rect.colliderect(player.image_rect):
                    player.hp -= self.attack
                    self.damaged = True
                    self.damage_cooldown.refresh()
                    player.combo_meter.break_combo()

    def reset(self, world: World):
        self.telegraph.cancel()
        self.set_pos(world, info)
        self.living = True
        self.hp = self.origin_hp
        self.recoil = 0
        self.recoil_dir = None
        self.charging_ability = None
        self.scr_lazer_beam_firing = False
        self.scr_lazer_beam_counter = 0
        if getattr(self, "telegraph", None):
            self.telegraph.cancel()

    def _load_images(self):
        fallback_r = os.path.join(BASE_DIR, r"images/fallback_enemyr.png")
        fallback_l = os.path.join(BASE_DIR, r"images/fallback_enemyr.png")

        try:
            self.image_r = pygame.image.load(self.rimage_name)

        except FileNotFoundError:

            try:
                logging.warning(f"{self.rimage_name} not found. Falling back to fallback image: {fallback_r}")
                self.image_r = pygame.image.load(fallback_r)

            except FileNotFoundError:
                logging.error(f"Fallback image not found for enemy {self}: {fallback_r}")
                self.image_r = pygame.Surface((100, 100))
                self.image_r.fill('purple')

        try:
            self.image_l = pygame.image.load(self.limage_name)

        except FileNotFoundError:

            try:
                logging.warning(f"{self.limage_name} not found. Falling back to fallback image: {fallback_l}")
                self.image_l = pygame.image.load(fallback_l)

            except FileNotFoundError:
                logging.error(f"Fallback image not found for enemy {self}: {fallback_l}")
                self.image_l = pygame.Surface((100, 100))
                self.image_l.fill('purple')

    def __getstate__(self):
        state = self.__dict__.copy()
        if state.get("image_r"):
            del state["image_r"]
            del state["image_l"]
            del state["uimage"]
            del state["arrow_image"]
        
        return state
    
    def __setstate__(self, state):
        self.__dict__.update(state)
        self._load_images()

        # Ekranın yüzde kaçını kaplayacak
        screen_fill_percentage = 0.06

        base_target_h = int(1080 * screen_fill_percentage * (self.image_size / 100.0))  # 1080p için ideal boy
        target_h = max(30, int(base_target_h * SCALE))

        # En-boy oranını bozmadan ölçekle:
        ratio_r = target_h / self.image_r.get_height()
        target_w_r = int(self.image_r.get_width() * ratio_r)
        self.image_r = pygame.transform.smoothscale(self.image_r, (target_w_r, target_h))

        ratio_l = target_h / self.image_l.get_height()
        target_w_l = int(self.image_l.get_width() * ratio_l)
        self.image_l = pygame.transform.smoothscale(self.image_l, (target_w_l, target_h))

        self.uimage = self.image_r

        self.arrow_image = pygame.image.load(self.arrow_image_name)
        self.arrow_image = pygame.transform.scale_by(self.arrow_image, SCALE)


class Boss(Enemy):
    DAMAGE_SWORD_DASH = "4"
    DAMAGE_BULLET = "5"
    DAMAGE_BRONZE_BULLET = "6"
    DAMAGE_SILVER_BULLET = "7"
    DAMAGE_BRONZE_GUN = "8"
    DAMAGE_SILVER_GUN = "9"
    DAMAGE_SWORD = "10"

    def __init__(
            self,
            hp,
            attack,
            abilities = None,
            r_image_name = os.path.join(BASE_DIR, "images/enemyr.png"),
            l_image_name = os.path.join(BASE_DIR, r"images/enemyl.png"),
            size=100,
            speed=300,
            damage_cooldown = Cooldown(2),
            cooldown = Cooldown(10),
            collisions=True,
            damagables=[DAMAGE_BULLET, DAMAGE_BRONZE_GUN, DAMAGE_SILVER_GUN, DAMAGE_SWORD_DASH, DAMAGE_SWORD],
            cooldown_arrow = None,
            arrow_image=os.path.join(BASE_DIR, r"images/arrow.png"),
            drops: list = None,
            *,
            bagimsiz_summons_cooldown: Cooldown = Cooldown(3),

            after_max_hp=None,
            name=None,
            bagimsiz_summons=None,
            cooldown_bagimsiz_summons: Cooldown=Cooldown(10),
            summons: list = None,
            cooldown_summons = Cooldown(3),
            scene_dialogues=None,
            typing_sound=None
        ):

        super().__init__(
            hp,
            attack,
            abilities,
            r_image_name,
            l_image_name,
            size,
            speed,
            damage_cooldown,
            cooldown,
            collisions,
            damagables,
            cooldown_arrow,
            arrow_image,
            drops=drops
        )

        self.after_max_hp = after_max_hp
        self.name = name or ""
        self.bagimsiz_summons = bagimsiz_summons or []
        self.bsummons_cooldown = bagimsiz_summons_cooldown
        self.cooldown_bagimsiz_summons = cooldown_bagimsiz_summons
        self.drops = drops or []
        self.summons = summons or []
        self.summon_cooldown = cooldown_summons

        try:
            self.full_image = pygame.image.load(r_image_name)

        except FileNotFoundError:
            self.full_image = pygame.image.load(
                os.path.join(BASE_DIR, r"images/fallback_enemyr.png")
            )

        self.typing_sound_filename = typing_sound or os.path.join(BASE_DIR, r"sounds/heavy_speak.wav")
        self.typing_sound = pygame.mixer.Sound(self.typing_sound_filename)

        self.scene_dialogues = scene_dialogues or []


    def update(self, player: Player, world: World, dt, level: list, cheated=False):
        if self.flash_timer > 0:
            self.flash_timer -= dt

        if not self.cat_jumping:


            self.mx, self.my = player.x, player.y
            if self.recoil > 0:

                if self.recoil_dir == "right":
                    new_x = self.x + (self.speed + scale(500)) * dt
                elif self.recoil_dir == "left":
                    new_x = self.x - (self.speed + scale(500)) * dt

                self.image_rect = self.uimage.get_rect(topleft=(new_x, self.y))
                if not self.image_rect.collidelist(world.rocks_rects) != -1 or not self.collisions:
                    self.x = new_x
                self.recoil -= 1 * dt

            try:
                self.dx = self.mx - self.x
                self.dy = self.my - self.y
            except TypeError:
                self.set_pos(world, info)
                self.dx = self.mx - self.x
                self.dy = self.my - self.y

            self.distance = math.hypot(self.dx, self.dy)

            if self.distance > 0:

                new_x = self.x + (self.dx / self.distance) * self.speed * dt
                new_y = self.y + (self.dy / self.distance) * self.speed * dt
                self.image_rect = self.uimage.get_rect(topleft=(new_x, new_y))
                self.rect = self.uimage.get_rect(topleft=(new_x, new_y))
        
                if self.rotated_rect is None:
                    if not self.image_rect.collidelist(world.rocks_rects) != -1 or not self.collisions:
                        self.x += (self.dx / self.distance) * self.speed * dt
                        self.y += (self.dy / self.distance) * self.speed * dt
                
                else:
                    self.rotated_rect.topleft = (new_x, new_y)
                    if not self.rotated_rect.collidelist(world.rocks_rects) != -1 or not self.collisions:
                        self.x += (self.dx / self.distance) * self.speed * dt
                        self.y += (self.dy / self.distance) * self.speed * dt

            else:
                self.touching = True
        self.angle = math.degrees(math.atan2(-self.dy, self.dx))

        if -45 < self.angle < 45:
            self.uimage = self.image_r

        elif self.angle < -135 or self.angle > 135:
            self.uimage = self.image_l

        self.update_sgrounds(player, dt)
        self.sgrounds = [sg for sg in self.sgrounds if not sg.destroyed]
        self.scr_lazers = [scr_lazer for scr_lazer in self.scr_lazers if not scr_lazer.destroyed]
        if self.hp <= 0:
            self.telegraph.cancel()
            self.living = False
            self.summoned = False
            self.drops: list

            if Enemy.VAL_MNGR is not None and not cheated:
                Enemy.VAL_MNGR("kill", 1, "change")

            for drop in self.drops:
                if type(drop) == Sword or type(drop) == Gun:
                    player.available_guns.append(drop)
                elif type(drop) == Item:
                    drop.set_pos(world, player)
                    world.items.append(drop)
                elif type(drop) == Effect:
                    drop.use(player, ())
                elif type(drop) == Enemy:
                    level.append(drop)
            self.drops.clear()
            if self.after_max_hp is not None:
                player.max_hp = self.after_max_hp
            self.after_max_hp = None
            return

    @staticmethod
    def draw(surface: pygame.Surface, font: userFont, level: list, bossFont: DynamicFont = None):
        bosses = []
        padding = 160
        for enemy in level:
            if enemy.living:
                if type(enemy) == Boss:
                    bosses.append(enemy)

                head_x = enemy.x + (enemy.uimage.get_width() / 2)
                head_y = enemy.y
                enemy.telegraph.draw(surface, (head_x, head_y))
                surface.blit(enemy.uimage, (enemy.x, enemy.y))

        for i, enemy in enumerate(bosses):
            if i > 1:
                continue

            bossFont = bossFont or font
            bar_height = info.current_w // 38  # float bölme ve print(bar_height) kaldırıldı

            font.draw_text(enemy.name, (info.current_w / 2, 50 + i * padding), surface, colours.BLACK, hiza="center")

            bar_w = info.current_w - info.current_w // 6
            unfill_rect = pygame.Rect(0, 0, bar_w, bar_height)
            unfill_rect.center = (info.current_w // 2, bar_height + 50 + i * padding)

            pygame.draw.rect(surface, colours.GRAY, unfill_rect, border_radius=20)

            percent = max(0.0, min(1.0, max(0, enemy.hp) / enemy.origin_hp))
            fill_rect = pygame.Rect(unfill_rect.left, unfill_rect.top, int(bar_w * percent), bar_height)
            pygame.draw.rect(surface, colours.RED, fill_rect, border_radius=20)

            rendered, _ = bossFont.render(f"{enemy.origin_hp}/{max(0, enemy.hp)}", colours.BLACK, surface, gap=10)
            surface.blit(
                rendered,
                (
                    unfill_rect.centerx - rendered.get_width() // 2,
                    unfill_rect.centery - rendered.get_height() // 2
                )
            )
    
    @classmethod
    def demirbt(cls):
        return cls(
            10_000,
            200,
            r_image_name=os.path.join(BASE_DIR, r"images/demirboklutf.png"),
            l_image_name=os.path.join(BASE_DIR, r"images/demirboklutf.png"),
            size=150,
            abilities=[EnemyAbilities.ABILITY_BOMBING, EnemyAbilities.ABILITY_SCR_LAZER_BEAM],
            name="Demirin Boklu Telefonu",
            damage_cooldown = Cooldown(3.4),
            cooldown=Cooldown(7),
            summons=[Enemy.miguel(), Enemy.miguel(), Enemy.morty()],
            after_max_hp = 2000,
            collisions=False,
            scene_dialogues=[
                ("Boss", "Lityum pilli kırmızı saçlı bi ablamız var işte sonra bi anda bi canavar geliyo bunlar dövüşüyo falan sonra bizimki lityum ablayı şarj ediyo"),
                ("Player", "Alayına Cubuloggo"),
                ("Boss", "At kafasi"),
                ("Boss", "At"),
                ("Player", "Yat Kafası"),
                ("Boss", "Ter gafaso"),
                ("Player", "balorant")
            ]
        )

    def summon(self, dt, level: dict, world, pending_enemies: list):
        self.bsummons_cooldown.reduce(dt)

        if self.summons and self.living:

            # Kendisi hariç mevcut düşmanlar
            without_self = (
                enemy
                for enemy in level.values()
                if enemy is not self
            )

            # Henüz summon edilmemiş düşmanlar
            all_not_summoned = all(
                not enemy.summoned
                for enemy in without_self
            )

            if all_not_summoned:
                should_summon = True

            else:
                self.summon_cooldown.reduce(dt)

                # Kendisi hariç bütün düşmanlar summon edilmiş mi?
                should_summon = (
                    self.summon_cooldown.check()
                    and all(
                        enemy.summoned
                        for enemy in level.values()
                        if enemy is not self
                    )
                )

            if should_summon:
                for summoning in self.summons:
                    new_enemy = summoning.copy()

                    new_enemy.summoned = True
                    new_enemy.set_pos(world, info)

                    pending_enemies.append(new_enemy)

                self.summon_cooldown.refresh()

        # Bağımsız summonlar
        if self.living and self.bsummons_cooldown.check():

            for summoning in self.bagimsiz_summons:
                new_enemy = summoning.copy()
                new_enemy.set_pos(world, info)

                pending_enemies.append(new_enemy)

            self.bsummons_cooldown.refresh()

    def __getstate__(self):
        state = self.__dict__.copy()
        if state.get("image_r"):
            del state["image_r"]
            del state["image_l"]
            del state["uimage"]
            del state["arrow_image"]

            del state["full_image"]
            del state["typing_sound"]
        
        return state
    
    def __setstate__(self, state):
        self.__dict__.update(state)

        fallback_r = os.path.join(BASE_DIR, r"images/fallback_enemyr.png")
        fallback_l = os.path.join(BASE_DIR, r"images/fallback_enemyr.png")

        try:
            self.image_r = pygame.image.load(self.rimage_name)

        except FileNotFoundError:
            self.image_r = pygame.image.load(fallback_r)

        try:
            self.image_l = pygame.image.load(self.limage_name)

        except FileNotFoundError:
            self.image_l = pygame.image.load(fallback_l)

        # Ekranın yüzde kaçını kaplayacak
        screen_fill_percentage = 0.06

        base_target_h = int(1080 * screen_fill_percentage * (self.image_size / 100.0))  # 1080p için ideal boy
        target_h = max(30, int(base_target_h * SCALE))

        # En-boy oranını bozmadan ölçekle:
        ratio_r = target_h / self.image_r.get_height()
        target_w_r = int(self.image_r.get_width() * ratio_r)
        self.image_r = pygame.transform.smoothscale(self.image_r, (target_w_r, target_h))

        ratio_l = target_h / self.image_l.get_height()
        target_w_l = int(self.image_l.get_width() * ratio_l)
        self.image_l = pygame.transform.smoothscale(self.image_l, (target_w_l, target_h))

        self.uimage = self.image_r

        self.arrow_image = pygame.image.load(self.arrow_image_name)
        self.arrow_image = pygame.transform.scale_by(self.arrow_image, SCALE)

        try:
            self.full_image = pygame.image.load(self.rimage_name)

        except FileNotFoundError:
            self.full_image = pygame.image.load(
                os.path.join(BASE_DIR, r"images/fallback_enemyr.png")
            )
        self.typing_sound = pygame.mixer.Sound(self.typing_sound_filename)
    

logging.info("Created classes.")
item1 = Item("Zıkkımın Kökü", colours.GREEN, 20, "hp", 20, Item.REDUCER, Item.TUP_IKSIR)
item_map = {
    "item1": Item("Can İksiri", colours.RED, [Effect("hp", 20, -1)], Item.APPENDER, Item.TUP_IKSIR),
    "item2": Item("Ölüm İksiri", colours.BLUE, [Effect("hp", 20, -1)], Item.YUVARLAK_IKSIR, Item.REDUCER, pickable=True)
}

level1 = [
    Enemy(100, 5)
]


def create_player():
    return Player(
        200,
        Sword(
            "Tahta Kılıç",
            15,
            colours.BROWN,
            700,
            MaterialFlags.WOODEN,
        ),
        os.path.join(BASE_DIR,r"images/stickmanr.png"),
        anim_dir=os.path.join(BASE_DIR, r"images/stickman_sprites"),
        val_manager=None
    )


defaults = {
    "Player": create_player(),
    "World": World(colours.darker(colours.GREEN, 75), colours.YELLOW, colours.darker(colours.YELLOW, 40), list(item_map[item] for item in item_map.keys()), os.path.join(BASE_DIR,"images/green_pattern.png"), os.path.join(BASE_DIR,"images/dirt_pattern.png")),
    "Level": "level1",
    "Win": False,
    "EnemyData": {}
}

logging.info("Created reference defaults.")

for enemy in level1:
    defaults["EnemyData"][enemy.id] = enemy

defaults["Player"].set_pos(defaults["World"])
for item in defaults["World"].items:
    item.set_pos(defaults["World"])

for enemy in globals()[defaults["Level"]]:
    enemy.set_pos(defaults["World"], info)

# hileli silah
defaults["Player"].available_guns.append(Gun("At Kafası", colours.lighter(colours.BLACK, 30), 40, 10, os.path.join(BASE_DIR,r"images/silver_silahr.png"), os.path.join(BASE_DIR,r"images/silver_silah_mermi.png"), 0.03, "__deflected__"))

constant_defaults: Final = defaults

def reset(screen_x: int, screen_y: int, game: dict):
    logging.info("Called reset.")
    global defaults
    del game["World"]
    game["World"] = World(colours.darker(colours.GREEN, 75), colours.YELLOW, colours.darker(colours.YELLOW, 40), [], terrain_image=os.path.join(BASE_DIR,"images/green_pattern.png"), dirt_image=os.path.join(BASE_DIR,"images/dirt_pattern.png"))
    game["Level"] = "level1"
    for enemy in globals()[game["Level"]]:
        enemy: Enemy
        enemy.reset(game["World"])
    game["World"].create_rocks(screen_x, screen_y)
    for item in item_map.values():
        new_item = item.copy()

        new_item.used = False
        new_item.picked = False
        new_item.touching = False
        new_item.drag_to_player = True
        new_item.mouse_getted = False
        new_item.effect_rect = None

        game["World"].items.append(new_item)
    for item in game["World"].items:
        item.used = False
        item.picked = False
        item.touching = False
        item.drag_to_player = True
        item.mouse_getted = False
        item.effect_rect = None
        item.set_pos(game["World"], game["Player"])

    game["Player"].reset(
        game["World"],
        Sword("Tahta Kılıç", 15, colours.BROWN, 700, MaterialFlags.WOODEN)
    )
    logging.info("Reseted variables successfully.")
    logger.debug(str(game))

    print("PLAYER")
    print(id(game["Player"]))
    print("WORLD")
    print(id(game["World"]))
    print("USING GUN")
    print(id(game["Player"].using_gun))
    print(type(game["Player"].using_gun))
    print("AVAILABLE GUNS")
    print(len(game["Player"].available_guns))

    for gun in game["Player"].available_guns:
        print(gun.name, id(gun), type(gun))
        
    for key, value in game["Player"].__dict__.items():
        print(key, type(value))

    game["Player"] = create_player()

    game["Player"].set_pos(game["World"])


    return game
