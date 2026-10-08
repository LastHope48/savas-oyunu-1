import math
import pygame


class EnemyTelegraph:
    """
    Düşmanın saldırı öncesinde kafasının üstünde beliren 
    yaylanan ve titreyen hafif ünlem işareti (!) sistemi.
    """
    def __init__(self):
        self.timer = 0.0
        self.charge_duration = 0.5
        self.is_charging = False
        self.attack_type = "arrow"

        self.core_color = (255, 60, 60)
        self.glow_color = (255, 20, 40)

        # Önceden yüklenmiş kalın font
        if not pygame.font.get_init():
            pygame.font.init()
        self.font = pygame.font.SysFont("Impact", 28)

    def start_charge(self, attack_type: str, themes: dict):
        self.is_charging = True
        self.timer = 0.0
        self.attack_type = attack_type

        theme = themes.get(attack_type, {
            "core": (255, 60, 60),
            "glow": (255, 20, 40),
            "duration": 0.50
        })
        self.core_color = theme["core"]
        self.glow_color = theme["glow"]
        self.charge_duration = theme["duration"]

    def cancel(self):
        self.is_charging = False
        self.timer = 0.0

    def update(self, dt: float) -> bool:
        """Süre dolduğunda True döner (saldırı fırlatılmalıdır)."""
        if not self.is_charging:
            return False

        self.timer += dt
        if self.timer >= self.charge_duration:
            self.is_charging = False
            self.timer = 0.0
            return True

        return False

    def draw(self, surface: pygame.Surface, head_center_pos: tuple[float, float]):
        """Düşmanın kafasının hemen üstüne küçük ve hafif bir ünlem çizer."""
        if not self.is_charging:
            return

        progress = min(1.0, self.timer / self.charge_duration)

        # 1. Pop-in Yaylanma Animasyonu (İlk çıktığında büyüyüp oturur)
        scale = min(1.0, self.timer * 6.0)
        # Sonlara doğru yaklaşan saldırı uyarısı için hafif titreme
        shake_x = math.sin(self.timer * 40.0) * (2.0 * progress) if progress > 0.5 else 0.0

        # 2. Renk: Son %18'lik dilimde Parry için beyaza patlar
        if progress >= 0.82:
            render_color = (255, 255, 255)
            badge_color = (255, 255, 255)
        else:
            render_color = self.core_color
            badge_color = self.glow_color

        # 3. Küçük İkon Yüzeyi (Sadece 36x44 piksel - Sıfır kasma!)
        icon_w, icon_h = 36, 44
        icon_surf = pygame.Surface((icon_w, icon_h), pygame.SRCALPHA)

        # Arka plan parlama halkası / elips rozet
        badge_rect = pygame.Rect(4, 2, 28, 38)
        pygame.draw.ellipse(icon_surf, (*badge_color, 190), badge_rect)
        pygame.draw.ellipse(icon_surf, (20, 20, 25, 220), badge_rect.inflate(-4, -4))

        # Ünlem Metni ("!")
        text_surf = self.font.render("!", True, render_color)
        text_rect = text_surf.get_rect(center=(icon_w // 2, icon_h // 2 - 1))
        icon_surf.blit(text_surf, text_rect)

        # Ölçekleme (Pop efekti)
        if scale < 1.0:
            sw = max(1, int(icon_w * scale))
            sh = max(1, int(icon_h * scale))
            icon_surf = pygame.transform.smoothscale(icon_surf, (sw, sh))

        # Düşmanın kafasının ~26px üstüne oturt
        draw_x = head_center_pos[0] + shake_x - (icon_surf.get_width() // 2)
        draw_y = head_center_pos[1] - 28 - icon_surf.get_height()

        surface.blit(icon_surf, (draw_x, draw_y))

    def __getstate__(self):
        state = self.__dict__.copy()
        state.pop("font", None)
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.font = pygame.font.SysFont("Impact", 28)