import pygame
from screens.screen import Screen
from screens.types import ScreenType
from calcs import SCALE
from basedir import BASE_DIR
import os

LICENSE_TEXT = ""
LICENSE_FILENAME = os.path.join(BASE_DIR, "LICENSE.txt")

# JENERİK İÇERİĞİ (İleride yeni rol veya metin eklemek için burayı düzenle)
# Tipler: "title", "subtitle", "role", "divider", "text", "space"

CREDITS_DATA = [
    {"type": "space", "amount": 60},
    {"type": "title", "text": "SAVAŞ OYUNU"},
    {"type": "subtitle", "text": "— YAPIM EKİBİ & KATKIDA BULUNANLAR —"},
    {"type": "space", "amount": 50},

    {
        "type": "role",
        "title": "OYUN TASARIMI & PROGRAMLAMA",
        "members": ["Mehmet Serdar EREN"]
    },
    {"type": "space", "amount": 35},

    {
        "type": "role",
        "title": "GÖRSEL DİL & KULLANICI ARAYÜZÜ (UI)",
        "members": ["Mehmet Serdar EREN"]
    },
    {"type": "space", "amount": 35},

    {
        "type": "role",
        "title": "MÜZİK & SES TASARIMI",
        "members": ["Overclock", "Weight of the Blade", "Excluded Corruption", "Eba Phonk", "Bouncing Seals", "Miguel Phonk", "Verity Obesity"]
    },
    {"type": "space", "amount": 45},

    {"type": "divider"},
    {"type": "space", "amount": 45},

    {
        "type": "role",
        "title": "KULLANILAN TEKNOLOJİLER",
        "members": [
            "Python 3",
            "Pygame Community Edition",
            "PyInstaller",
            "Cloudflare & Render"
        ]
    },
    {"type": "space", "amount": 40},

    {
        "type": "role",
        "title": "ÖZEL TEŞEKKÜRLER",
        "members": [
            "Uras Köroğlu",
            "Deniz Yalçın",
            "7/C Sınıfı",
            "Tüm Test Eden ve Oynayan Oyuncular"
        ]
    },
    {"type": "space", "amount": 50},

    {
        "type": "text",
        "id": "license_section",
        "lines": [
            "Bu proje açık kaynaklı geliştirme ruhuyla üretilmiştir.",
            "",
            "__license__"
        ]
    },
    {"type": "space", "amount": 80},
    {"type": "title", "text": "OYNADIĞINIZ İÇİN TEŞEKKÜRLER!"},
    {"type": "space", "amount": 200}
]


class CreditsScreen(Screen):
    def __init__(self, game):
        super().__init__(game)

        self.scroll = 0.0
        self.normal_speed = 55.0 * SCALE
        self.fast_speed = 260.0 * SCALE
        self.current_speed = self.normal_speed

        # Font boyutları
        self.title_font = pygame.font.Font(None, int(46 * SCALE))
        self.subtitle_font = pygame.font.Font(None, int(28 * SCALE))
        self.role_title_font = pygame.font.Font(None, int(22 * SCALE))
        self.name_font = pygame.font.Font(None, int(32 * SCALE))
        self.body_font = pygame.font.Font(None, int(22 * SCALE))
        self.hint_font = pygame.font.Font(None, int(18 * SCALE))

        # Üst ve alt kenar sinematik karartma perdeleri
        self.top_fade = None
        self.bottom_fade = None
        self._init_fade_masks()

        # İçerik koordinatlarını önceden hesapla (her karede hesaplamayı engeller)
        self.layout_items = []
        self.total_content_height = 0
        self._build_layout()
        self._read_license()

    def _read_license(self):
        license_lines = []

        try:
            if os.path.exists(LICENSE_FILENAME):
                with open(LICENSE_FILENAME, "r", encoding="utf-8") as f:
                    raw_text = f.read().strip()
                    # Pygame \n karakterlerini çizemediği için satırlara bölüyoruz:
                    license_lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
            else:
                license_lines = ["Lisans dosyası bulunamadı."]

        except Exception as e:
            if hasattr(self.game, "logger"):
                self.game.logger.error(f"Reading license at {LICENSE_FILENAME} failed.")
                self.game.logger.exception(e)
            else:
                print(f"Lisans okuma hatası: {e}")
            license_lines = ["Lisans verisi okunamadı."]

        license_block = None
        for item in CREDITS_DATA:
            if item.get("id") == "license_section":
                license_block = item
                break

        if license_block:
            # İlk açıklama satırını koruyup altına lisans metnini ekliyoruz:
            header_line = license_block["lines"][0] if license_block.get("lines") else ""
            license_block["lines"] = [header_line] + [""] +license_lines
            
            # Değişen metin boyutuyla koordinatları yeniden hesapla:
            self._build_layout()
        else:
            self.game.logger.warning("'license_section' ID block in CREDITS_DATA not found.")

    def _init_fade_masks(self):
        """Yazıların ekranın üstünden ve altından yumuşakça sönümlenerek geçmesi için degrade maskeler."""
        w, h = self.game.screen.get_size()
        fade_h = int(120 * SCALE)

        self.top_fade = pygame.Surface((w, fade_h), pygame.SRCALPHA)
        self.bottom_fade = pygame.Surface((w, fade_h), pygame.SRCALPHA)

        for y in range(fade_h):
            # 0'da tam siyah, fade_h'de tam şeffaf
            ratio = y / fade_h
            alpha_top = int(255 * (1.0 - ratio))
            alpha_bottom = int(255 * ratio)

            pygame.draw.line(self.top_fade, (0, 0, 0, alpha_top), (0, y), (w, y))
            pygame.draw.line(self.bottom_fade, (0, 0, 0, alpha_bottom), (0, y), (w, y))

    def _build_layout(self):
        """CREDITS_DATA listesini tarayıp her elemana bağıl bir dikey (rel_y) koordinat atar."""
        self.layout_items = []
        current_y = 0

        for item in CREDITS_DATA:
            itype = item.get("type")

            if itype == "space":
                current_y += int(item.get("amount", 20) * SCALE)

            elif itype == "title":
                surf = self.title_font.render(item["text"], True, (0, 240, 255))
                # Gölgeyi de burada bir kez renderlayıp önbelleğe alıyoruz:
                shadow_surf = self.title_font.render(item["text"], True, (4, 6, 10))
                self.layout_items.append({
                    "surf": surf,
                    "shadow_surf": shadow_surf,
                    "rel_y": current_y,
                    "type": "title"
                })
                current_y += surf.get_height() + int(10 * SCALE)

            elif itype == "subtitle":
                surf = self.subtitle_font.render(item["text"], True, (130, 165, 200))
                self.layout_items.append({"surf": surf, "rel_y": current_y, "type": "subtitle"})
                current_y += surf.get_height() + int(10 * SCALE)

            elif itype == "role":
                role_surf = self.role_title_font.render(item["title"], True, (0, 190, 220))
                self.layout_items.append({"surf": role_surf, "rel_y": current_y, "type": "role_title"})
                current_y += role_surf.get_height() + int(8 * SCALE)

                for name in item.get("members", []):
                    name_surf = self.name_font.render(name, True, (245, 250, 255))
                    shadow_surf = self.name_font.render(name, True, (4, 6, 10))
                    self.layout_items.append({
                        "surf": name_surf,
                        "shadow_surf": shadow_surf,
                        "rel_y": current_y,
                        "type": "name"
                    })
                    current_y += name_surf.get_height() + int(6 * SCALE)

            elif itype == "divider":
                self.layout_items.append({"rel_y": current_y, "type": "divider"})
                current_y += int(20 * SCALE)

            elif itype == "text":
                for line in item.get("lines", []):
                    line_surf = self.body_font.render(line, True, (160, 175, 195))
                    self.layout_items.append({"surf": line_surf, "rel_y": current_y, "type": "text"})
                    current_y += line_surf.get_height() + int(6 * SCALE)

        self.total_content_height = current_y

    def draw(self, surface: pygame.Surface):
        # 1. Koyu Siber Zemin
        surface.fill((10, 14, 20))

        sw, sh = surface.get_size()
        center_x = sw // 2

        # 2. Yazıların Çizimi (Off-screen Culling)
        for item in self.layout_items:
            screen_y = sh - self.scroll + item["rel_y"]

            # Ekran dışındaysa hiç çizme (FPS koruması)
            if screen_y < -60 or screen_y > sh + 60:
                continue

            itype = item["type"]

            if itype == "divider":
                line_w = int(240 * SCALE)
                lx1 = center_x - line_w // 2
                lx2 = center_x + line_w // 2
                pygame.draw.line(surface, (0, 200, 235), (lx1, screen_y), (lx2, screen_y), 2)
                pygame.draw.circle(surface, (255, 255, 255), (center_x, int(screen_y)), 3)

            else:
                surf = item["surf"]
                rect = surf.get_rect(centerx=center_x, top=screen_y)

                # Eğer önceden üretilmiş gölgesi varsa 2 piksel çaprazına çiz
                if "shadow_surf" in item:
                    surface.blit(item["shadow_surf"], rect.move(2, 2))

                # Asıl metni çiz
                surface.blit(surf, rect)

        # 3. Üst ve Alt Sinematik Sönümleme Perdeleri
        if self.top_fade:
            surface.blit(self.top_fade, (0, 0))
        if self.bottom_fade:
            surface.blit(self.bottom_fade, (0, sh - self.bottom_fade.get_height()))

        # 4. Alt Köşe Kontrol İpucu
        hint_surf = self.hint_font.render("[Sol Tık: Hızlandır | Fare Tekerleği: Kaydır | ESC: Çıkış]", True, (75, 95, 120))
        surface.blit(hint_surf, (20, sh - 30))

    def update(self, dt: float):
        self.scroll += self.current_speed * dt

        # Jenerik tamamen bitip ekranın üstünden kaybolduğunda menüye dön
        screen_h = self.game.screen.get_height()
        if self.scroll > self.total_content_height + screen_h:
            self._exit_credits()

    def handle_event(self, event: pygame.event.Event):
        # 1. Hızlandırma (Sol Tık Basılıyken)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 or event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            self.current_speed = self.fast_speed

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 or event.type == pygame.KEYUP:
            self.current_speed = self.normal_speed

        # 2. Fare Tekerleği ile Manuel İleri / Geri Kaydırma
        elif event.type == pygame.MOUSEWHEEL:
            self.scroll -= event.y * (40 * SCALE)
            self.scroll = max(0.0, self.scroll)

        # 3. İptal / Menüye Dönüş
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                self._exit_credits()

    def _exit_credits(self):
        if hasattr(self.game, "screen_manager"):
            self.game.screen_manager.set_screen(ScreenType.MENU)

    def on_enter(self, transfer_datas: dict = None):
        self.scroll = 0.0
        self.current_speed = self.normal_speed

        self.game.mixer.music.load(
            os.path.join(BASE_DIR, r"musics/credits_music.ogg")
        )
        self.game.mixer.music.play(-1)
        self.game.dump("last_music", os.path.join(BASE_DIR, r"musics/credits_music.ogg"))

        self._init_fade_masks()
