import pygame
import random


class ComboPopup:
    """Sağ alttan fırlatılan, dönerek ekran boyutuna orantılı şekilde uzağa süzülen kombo metni."""
    def __init__(self, text: str, color: tuple[int, int, int], font: pygame.font.Font, swidth: int, sheight: int):
        self.text = text
        self.color = color
        self.font = font

        # 1. Başlangıç konumu (Ekranın sağ alt kenarına orantılı)
        self.x = swidth - (swidth * random.uniform(0.06, 0.12))
        self.y = sheight - (sheight * random.uniform(0.10, 0.16))

        # 2. Yatay Fırlama Hızı (Ekran genişliğinin %40 ile %65'i kadar sola uzanır)
        self.vx = -swidth * random.uniform(0.30, 0.50)

        # 3. Dikey Fırlama Hızı (Ekranın üst-orta kısımlarına kadar tırmanır)
        self.vy = -sheight * random.uniform(1.20, 1.50)

        # 4. Dinamik Yerçekimi (Ekran yüksekliğine göre dengeli bir parabol çizer)
        self.gravity = sheight * 1.80

        # Dönme (Rotasyon) fiziği
        self.angle = random.uniform(-15.0, 15.0)
        self.rot_speed = random.uniform(120.0, 240.0) * (-1 if self.vx < 0 else 1)

        # Uçuş süresi (Geniş kavis boyunca havada kalabilmesi için 1.6 saniyeye çıkarıldı)
        self.lifetime = 1.65
        self.max_lifetime = 1.65
        self.dead = False

        self.base_surf = self._render_text_with_outline()

    def _render_text_with_outline(self) -> pygame.Surface:
        # Metin okunurluğu için siyah dış hat + renkli dolgu
        txt = self.font.render(self.text, True, self.color)
        outline = self.font.render(self.text, True, (15, 15, 20))
        
        w, h = txt.get_width() + 8, txt.get_height() + 8
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        
        # 4 köşeye siyah gölge basarak kalın kontur yap
        for ox, oy in [(-3, 0), (3, 0), (0, -3), (0, 3), (-2, -2), (2, 2)]:
            surf.blit(outline, (ox + 4, oy + 4))
        surf.blit(txt, (4, 4))
        return surf

    def update(self, dt: float):
        # 1. Hız ve yerçekimi entegrasyonu
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += self.gravity * dt

        # 2. Havada dönme
        self.angle += self.rot_speed * dt

        # 3. Süre ve yok olma
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.dead = True

    def draw(self, surface: pygame.Surface):
        if self.dead:
            return

        # Kalan süreye göre saydamlık (alpha fade-out)
        alpha = int(255 * max(0.0, min(1.0, self.lifetime / 0.5)))
        
        # Yüzeyi döndür
        rotated_surf = pygame.transform.rotate(self.base_surf, self.angle)
        
        # Saydamlığı uygula
        if alpha < 255:
            rotated_surf.set_alpha(alpha)

        # Merkeze göre çizdir
        rect = rotated_surf.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(rotated_surf, rect)


class ComboMeter:
    RANKS = [
        (0,  "---",  (120, 120, 120)),
        (1,  "D",    (100, 180, 255)),   # Cyan
        (5,  "C",    (100, 240, 140)),   # Yeşil
        (10, "B",    (255, 220, 60)),    # Sarı
        (16, "A",    (255, 140, 40)),    # Turuncu
        (24, "S",    (255, 40, 80)),     # Kırmızı
        (35, "SSS",  (255, 215, 0)),     # Altın / Supreme
    ]

    def __init__(self, x_offset: int = 40, y_offset: int = 40):
        self.combo_count = 0
        self.timer = 0.0
        self.max_time = 2.4
        self.scale = 1.0
        self.x_offset = x_offset
        self.y_offset = y_offset

        # Uçuşan yazılar listesi
        self.popups: list[ComboPopup] = []

        self._init_fonts()

    def _init_fonts(self):
        if not pygame.font.get_init():
            pygame.font.init()
        self.font_count = pygame.font.SysFont("Impact", 44)
        self.font_rank = pygame.font.SysFont("Impact", 56)
        self.font_label = pygame.font.SysFont("Arial", 14, bold=True)
        # Fırlayan yazı için kalın ve etkileyici font
        self.font_popup = pygame.font.SysFont("Impact", 38)

    # =========================================================
    # SERİLEŞTİRME
    # =========================================================

    def __getstate__(self):
        state = self.__dict__.copy()
        # Fontlar ve geçici uçuşan efekt parçacıkları diske kaydedilmez
        state.pop("font_count", None)
        state.pop("font_rank", None)
        state.pop("font_label", None)
        state.pop("font_popup", None)
        state.pop("popups", None)
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.popups = []
        self._init_fonts()

    # =========================================================
    # OYNANIŞ & FIRLATMA
    # =========================================================

    def get_current_rank(self) -> tuple[str, tuple[int, int, int]]:
        current_rank = self.RANKS[0]
        for threshold, name, color in self.RANKS:
            if self.combo_count >= threshold:
                current_rank = (name, color)
        return current_rank[0], current_rank[1]

    def add_hit(self, count: int = 1, swidth: int = 1280, sheight: int = 720):
        """Kılıç vurduğunda veya ok sektirildiğinde çağrılır."""
        self.combo_count += count
        self.timer = self.max_time
        self.scale = 1.45

        # Rütbeyi ve rengi belirle
        rank_name, rank_color = self.get_current_rank()

        # "A - x20" formatında yazıyı oluştur ve sağ alttan fırlat
        popup_text = f"{rank_name} - x{self.combo_count}"
        self.popups.append(
            ComboPopup(
                text=popup_text,
                color=rank_color,
                font=self.font_popup,
                swidth=swidth,
                sheight=sheight
            )
        )

    def break_combo(self):
        if self.combo_count > 0:
            self.combo_count = 0
            self.timer = 0.0
            self.scale = 1.0

    def update(self, dt: float):
        # 1. Kombo zaman aşımı
        if self.combo_count > 0:
            self.timer -= dt
            if self.timer <= 0:
                self.combo_count = 0
                self.timer = 0.0

        # 2. Köşedeki sabit UI yaylanması
        if self.scale > 1.0:
            self.scale += (1.0 - self.scale) * min(1.0, 14.0 * dt)

        # 3. Fırlayan yazıların fiziğini güncelle
        for popup in self.popups:
            popup.update(dt)
        self.popups = [p for p in self.popups if not p.dead]

    def draw(self, surface: pygame.Surface):
        # 1. Önce uçuşan ve dönen yazıları ekrana bas
        for popup in self.popups:
            popup.draw(surface)

        # 2. Sağ üstteki sabit kombo kutusu
        if self.combo_count <= 0:
            return

        swidth, _ = surface.get_size()
        base_y = self.y_offset
        rank_name, rank_color = self.get_current_rank()

        rank_surf = self.font_rank.render(rank_name, True, rank_color)
        count_surf = self.font_count.render(f"x{self.combo_count}", True, (255, 255, 255))
        label_surf = self.font_label.render("COMBO", True, (200, 200, 200))

        combo_box = pygame.Surface((200, 100), pygame.SRCALPHA)
        combo_box.blit(rank_surf, (10, 5))
        combo_box.blit(count_surf, (90, 12))
        combo_box.blit(label_surf, (95, 62))

        bar_w = int(170 * (self.timer / self.max_time))
        pygame.draw.rect(combo_box, (40, 45, 55), (10, 84, 170, 5), border_radius=3)
        pygame.draw.rect(combo_box, rank_color, (10, 84, bar_w, 5), border_radius=3)

        w = int(combo_box.get_width() * self.scale)
        h = int(combo_box.get_height() * self.scale)
        scaled_surf = pygame.transform.smoothscale(combo_box, (w, h))

        rect = scaled_surf.get_rect(topright=(swidth - self.x_offset, base_y))
        surface.blit(scaled_surf, rect)
