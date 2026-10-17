import os
import math
import random
import pygame
import colours

from basedir import BASE_DIR
from dfont import DynamicFont
from screens.types import ScreenType
from .screen import Screen
import classes


class ConfettiParticle:
    """Havada süzülen ve 3D takla atarak dökülen konfeti parçacığı."""
    def __init__(self, x: float, y: float, angle_deg: float, power: float):
        self.x = x
        self.y = y
        
        rad = math.radians(angle_deg)
        self.vx = math.cos(rad) * power
        self.vy = math.sin(rad) * power

        self.color = random.choice([
            (255, 60, 60),    # Kırmızı
            (255, 210, 40),   # Altın Sarısı
            (60, 180, 255),   # Gök Mavisi
            (80, 230, 110),   # Neon Yeşil
            (255, 120, 220),  # Pembe
            (255, 140, 30),   # Turuncu
            (180, 80, 255)    # Mor
        ])

        self.w = random.randint(8, 16)
        self.h = random.randint(14, 26)
        self.rot_angle = random.uniform(0, 360)
        self.rot_speed = random.uniform(-180, 180)

        self.flutter_time = random.uniform(0, 10)
        self.flutter_speed = random.uniform(4.0, 9.0)
        self.gravity = 520.0
        self.active = True

    def update(self, dt: float, screen_h: int):
        self.vy += self.gravity * dt
        self.vx *= (1.0 - 0.7 * dt)  # Hava sürtünmesi

        self.x += self.vx * dt
        self.y += self.vy * dt

        self.rot_angle += self.rot_speed * dt
        self.flutter_time += dt

        if self.y > screen_h + 50:
            self.active = False

    def draw(self, surface: pygame.Surface):
        # 3D kağıt salınımı simülasyonu (Genişlik sinüs dalgasıyla büzülür)
        current_w = max(2, int(abs(math.cos(self.flutter_time * self.flutter_speed)) * self.w))
        part_surf = pygame.Surface((current_w, self.h), pygame.SRCALPHA)
        part_surf.fill(self.color)

        rotated = pygame.transform.rotate(part_surf, self.rot_angle)
        rect = rotated.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(rotated, rect)


class DeskCard:
    """Masanın üzerine yukarıdan şaklatılarak yapıştırılan istatistik kartı."""
    def __init__(
            self,
            title: str,
            value: str,
            rel_x: float,
            rel_y: float,
            rel_w: float,
            rel_h: float,
            slam_delay: float,
            text_color: pygame.Color = (35, 30, 25)
        ):
        self.title = title
        self.value = value
        self.rel_x = rel_x  # Ekran oranları (0.0 - 1.0)
        self.rel_y = rel_y
        self.rel_w = rel_w
        self.rel_h = rel_h
        self.slam_delay = slam_delay

        # Masaya rastgele ve doğal durması için hafif eğik yapışma açısı (-3° ile +3°)
        self.tilt_angle = random.uniform(-2.8, 2.8)

        self.slammed = False
        self.anim_t = 0.0  # 0.0: Havada -> 1.0: Masaya yapıştı
        self.slam_duration = 0.22

        self.text_color = text_color

    def update(self, current_time: float, dt: float, sfx_slam=None):
        if current_time >= self.slam_delay and self.anim_t < 1.0:
            self.anim_t = min(1.0, self.anim_t + dt / self.slam_duration)
            if self.anim_t >= 1.0 and not self.slammed:
                self.slammed = True
                if sfx_slam:
                    sfx_slam.play()

    def draw(self, surface: pygame.Surface, screen_w: int, screen_h: int, font_title: DynamicFont, font_val: DynamicFont, current_time: float):
        if current_time < self.slam_delay:
            return  # Sırası gelmediyse çizilmez

        # İniş yumuşatma eğrisi (Yukarıdan masaya hızla çarpma)
        progress = self.anim_t
        ease_scale = 1.0 + (1.0 - progress) * 1.2  # 2.2x büyüklükten masaya 1.0x ile çarpar

        target_w = int(screen_w * self.rel_w)
        target_h = int(screen_h * self.rel_h)
        target_cx = int(screen_w * self.rel_x)
        target_cy = int(screen_h * self.rel_y)

        draw_w = max(10, int(target_w * ease_scale))
        draw_h = max(10, int(target_h * ease_scale))

        # Kart Yüzeyi (Fildişi / Not kağıdı rengi)
        card_surf = pygame.Surface((draw_w, draw_h), pygame.SRCALPHA)
        pygame.draw.rect(card_surf, (246, 243, 232), (0, 0, draw_w, draw_h), border_radius=12)
        pygame.draw.rect(card_surf, (200, 195, 180), (0, 0, draw_w, draw_h), width=4, border_radius=12)

        # Kartın üst kısmına yapışkanlı bant efekti
        tape_w = int(draw_w * 0.35)
        tape_h = max(6, int(draw_h * 0.12))
        tape_rect = pygame.Rect((draw_w - tape_w) // 2, 0, tape_w, tape_h)
        pygame.draw.rect(card_surf, (255, 215, 0, 200), tape_rect, border_radius=3)

        # Yazıları yerleştir (Sadece masaya oturduğunda net çizilir)
        if progress >= 0.7:
            # Başlık
            t_surf, _ = font_title.render(self.title, (110, 105, 95), card_surf)
            card_surf.blit(t_surf, t_surf.get_rect(center=(draw_w // 2, int(draw_h * 0.35))))
            # Değer
            v_surf, _ = font_val.render(self.value, self.text_color, card_surf)
            card_surf.blit(v_surf, v_surf.get_rect(center=(draw_w // 2, int(draw_h * 0.72))))

        # Masaya yaklaşırken gölgenin büzülmesi ve koyulaşması (3D Yapışma Yanılsaması)
        shadow_offset = int((1.0 - progress) * 45) + 6
        shadow_alpha = int(progress * 90) + 40
        shadow_surf = pygame.Surface((draw_w, draw_h), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (15, 10, 5, shadow_alpha), (0, 0, draw_w, draw_h), border_radius=12)

        # Eğik duruş açısı
        rotated_shadow = pygame.transform.rotate(shadow_surf, self.tilt_angle)
        rotated_card = pygame.transform.rotate(card_surf, self.tilt_angle)

        # Önce masaya düşen gölgeyi bas
        surface.blit(rotated_shadow, rotated_shadow.get_rect(center=(target_cx + shadow_offset, target_cy + shadow_offset)))
        # Ardından kartın kendisini bas
        surface.blit(rotated_card, rotated_card.get_rect(center=(target_cx, target_cy)))


class WinScreen(Screen):
    def __init__(self, game):
        super().__init__(game)

        self.last_screen_size = (0, 0)
        self.timer = 0.0
        self.confetti_popped = False

        self.particles: list[ConfettiParticle] = []
        self.cards: list[DeskCard] = []

        # Fontlar
        font_path = os.path.join(BASE_DIR, "fonts/Clarity-city.ttf")
        if not os.path.exists(font_path):
            font_path = pygame.font.get_default_font()
        self.font_path = font_path

        self.font_banner = None
        self.font_card_title = None
        self.font_card_val = None
        self.font_prompt = None

        # Sesler
        sounds_dir = os.path.join(BASE_DIR, "sounds")
        pop_path = os.path.join(sounds_dir, "pop.wav")
        if not os.path.exists(pop_path):
            pop_path = os.path.join(sounds_dir, "click.wav")
        self.sfx_pop = pygame.mixer.Sound(pop_path) if os.path.exists(pop_path) else None

        thud_path = os.path.join(sounds_dir, "slam.wav")
        self.sfx_slam = pygame.mixer.Sound(thud_path) if os.path.exists(thud_path) else None

        self.musics_dir = os.path.join(BASE_DIR, "musics")
        self.win_music = os.path.join(self.musics_dir, r"Weight_of_the_Blade.ogg")
        self.played_music = False

    def _get_all_time_kills(self) -> int:
        try:
            if hasattr(self.game, "val_manager") and callable(self.game.val_manager):
                return int(self.game.val_manager("kill"))
        except Exception:
            pass
        return 0

    def _get_max_combo(self) -> int:
        try:
            player: classes.Player = getattr(self.game.game_data, "player", None)
            if player and hasattr(player, "combo_meter"):
                return player.combo_meter.max_combo
        
        except:
            pass

        return 0

    def _get_max_rank(self) -> tuple[str, tuple[int, int, int]]:
        try:
            player: classes.Player = getattr(self.game.game_data, "player", None)
            if player and hasattr(player, "combo_meter"):
                return player.combo_meter.top_rank

        except:
            pass

        return ("---", (128, 128, 128))

    def _update_layout(self, screen_w: int, screen_h: int):
        if self.last_screen_size == (screen_w, screen_h):
            return

        self.last_screen_size = (screen_w, screen_h)

        # Orantılı Font Boyutları
        self.font_banner = DynamicFont(self.font_path, max(28, int(screen_h * 0.070)), 100)
        self.font_card_title = DynamicFont(self.font_path, max(16, int(screen_h * 0.024)), 100)
        self.font_card_val = DynamicFont(self.font_path, max(26, int(screen_h * 0.055)), 100)
        self.font_prompt = DynamicFont(self.font_path, max(14, int(screen_h * 0.022)), 100)

    def on_enter(self, transfer_datas=None):
        self.timer = 0.0
        self.confetti_popped = False
        self.particles.clear()
        self.cards.clear()
        self.last_screen_size = (0, 0)

        info = pygame.display.Info()
        self._update_layout(info.current_w, info.current_h)

        # İstatistikleri Çek
        kills = self._get_all_time_kills()
        max_combo = self._get_max_combo()
        max_rank, max_rank_color = self._get_max_rank()

        # Masaya yapışacak kartlar sıralaması ve zamanlaması:
        # 1. Büyük Zafer Belgesi (1.2 saniyede masaya yapışır)
        self.cards.append(
            DeskCard("BÖLÜM RAPORU", "ZAFER!", 0.50, 0.36, 0.54, 0.18, slam_delay=1.2)
        )
        # 2. Tüm Zamanların Öldürme Kartı (1.8 saniyede yapışır)
        self.cards.append(
            DeskCard("TOPLAM LEŞ", str(kills), 0.34, 0.62, 0.24, 0.22, slam_delay=1.8)
        )
        # 3. Maksimum Kombo Kartı (2.4 saniyede yapışır)
        self.cards.append(
            DeskCard("MAKSİMUM KOMBO", f"{max_rank} {max_combo}x", 0.66, 0.62, 0.24, 0.22, slam_delay=2.4, text_color=max_rank_color)
        )

    def _fire_confetti(self, screen_w: int, screen_h: int):
        """Ekranın sağ ve sol alt köşesindeki konfeti borularından saçılma."""
        if self.sfx_pop:
            self.sfx_pop.play()

        # Sol Boru (Yukarı ve sağa doğru fırlar: -35° ile -75°)
        left_x = screen_w * 0.08
        left_y = screen_h * 0.88
        for _ in range(90):
            ang = random.uniform(-78, -32)
            power = random.uniform(500, 1050)
            self.particles.append(ConfettiParticle(left_x, left_y, ang, power))

        # Sağ Boru (Yukarı ve sola doğru fırlar: -105° ile -145°)
        right_x = screen_w * 0.92
        right_y = screen_h * 0.88
        for _ in range(90):
            ang = random.uniform(-148, -102)
            power = random.uniform(500, 1050)
            self.particles.append(ConfettiParticle(right_x, right_y, ang, power))

    def handle_event(self, event: pygame.event.Event):
        is_action = (
            (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1) or
            (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE)
        )

        if not is_action:
            return

        # Animasyonlar henüz bitmediyse: Tek tuşla hepsini masaya anında şaklat
        all_slammed = all(c.slammed for c in self.cards)
        if not all_slammed:
            for card in self.cards:
                card.slam_delay = 0.0
                card.anim_t = 1.0
                card.slammed = True
            self.timer = max(self.timer, 3.0)
            return

        # Tüm kartlar masaya oturmuşsa menüye dön
        self._return_to_next()

    def update(self, dt: float):
        self.timer += dt
        screen_w, screen_h = self.last_screen_size

        # 0.65. Saniyede Konfetiler Patlar
        if self.timer >= 0.65 and not self.confetti_popped:
            self.confetti_popped = True
            if screen_w > 0 and screen_h > 0:
                self._fire_confetti(screen_w, screen_h)

        # Konfetileri güncelle
        for p in self.particles:
            p.update(dt, screen_h)
        self.particles = [p for p in self.particles if p.active]

        # Kartların iniş animasyonlarını güncelle
        for card in self.cards:
            card.update(self.timer, dt, self.sfx_slam)

        if not self.played_music:
            if all(card.slammed for card in self.cards):
                self.played_music = True
                self.game.mixer.music.load(self.win_music)
                self.game.mixer.music.play(-1)

    def _draw_table_background(self, surface: pygame.Surface, screen_w: int, screen_h: int):
        """Ahşap çalışma masası dokusu ve masa matı."""
        # Sıcak koyu ahşap zemin
        surface.fill((48, 33, 24))

        # Masa tahtası çizgileri
        plank_h = max(40, screen_h // 12)
        for y in range(0, screen_h, plank_h):
            pygame.draw.line(surface, (38, 25, 18), (0, y), (screen_w, y), 2)

        # Masanın ortasındaki deri çalışma matı
        pad_w = int(screen_w * 0.88)
        pad_h = int(screen_h * 0.84)
        pad_rect = pygame.Rect((screen_w - pad_w) // 2, (screen_h - pad_h) // 2, pad_w, pad_h)
        pygame.draw.rect(surface, (30, 24, 28), pad_rect, border_radius=20)
        pygame.draw.rect(surface, (65, 52, 45), pad_rect, width=4, border_radius=20)

    def _draw_confetti_cannons(self, surface: pygame.Surface, screen_w: int, screen_h: int):
        """Köşelerde duran retro parti konfeti tüpleri."""
        # Sol Boru
        lx, ly = int(screen_w * 0.08), int(screen_h * 0.88)
        pygame.draw.line(surface, (230, 50, 50), (lx - 15, ly + 25), (lx + 20, ly - 25), 18)
        pygame.draw.circle(surface, (255, 215, 0), (lx + 20, ly - 25), 11)

        # Sağ Boru
        rx, ry = int(screen_w * 0.92), int(screen_h * 0.88)
        pygame.draw.line(surface, (50, 130, 240), (rx + 15, ry + 25), (rx - 20, ry - 25), 18)
        pygame.draw.circle(surface, (255, 215, 0), (rx - 20, ry - 25), 11)

    def draw(self, surface: pygame.Surface):
        screen_w, screen_h = surface.get_size()
        self._update_layout(screen_w, screen_h)

        # 1. Masa Zemini
        self._draw_table_background(surface, screen_w, screen_h)

        # 2. Konfeti Boruları
        self._draw_confetti_cannons(surface, screen_w, screen_h)

        # 3. Masanın Üstüne Yapıştırılan Kartlar
        for card in self.cards:
            card.draw(surface, screen_w, screen_h, self.font_card_title, self.font_card_val, self.timer)

        # 4. Havada Uçuşan Konfetiler (Kartların üstüne dökülür)
        for p in self.particles:
            p.draw(surface)

        # 5. Devam Et Yazısı (Tüm kartlar yapışınca altta parıldayarak belirir)
        all_slammed = all(c.slammed for c in self.cards)
        if all_slammed:
            pulse = abs(math.sin(self.timer * 4.0)) * 140 + 115
            txt, _ = self.font_prompt.render("Devam etmek için [BOŞLUK] veya [SOL TIK]", (int(pulse), int(pulse), int(pulse)), surface)
            surface.blit(txt, txt.get_rect(center=(screen_w // 2, int(screen_h * 0.86))))

    def _return_to_next(self):
        if hasattr(self.game, "reset"):
            self.game.reset()

        self.game.screen_manager.set_screen(ScreenType.MENU)