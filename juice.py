import pygame
import random
import math

class Spark:
    """Mermi sektirme veya kılıç vuruşunda fırlayan neon çizgi kıvılcımı."""
    def __init__(self, x: float, y: float, angle: float, speed: float, color: tuple, length: float = 12.0):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = speed
        self.color = color
        self.length = length
        self.life = 1.0        # 1.0'dan 0'a doğru azalır
        self.decay = random.uniform(3.5, 6.0) # Saniyede sönme hızı

    def update(self, dt: float) -> bool:
        self.x += math.cos(self.angle) * self.speed * dt
        self.y += math.sin(self.angle) * self.speed * dt
        self.speed *= max(0.0, 1.0 - 5.0 * dt) # Sürtünmeyle yavaşlama
        self.life -= self.decay * dt
        return self.life > 0

    def draw(self, surface: pygame.Surface):
        if self.life <= 0:
            return
        cur_len = self.length * self.life
        end_x = self.x + math.cos(self.angle) * cur_len
        end_y = self.y + math.sin(self.angle) * cur_len
        # Parlak çekirdek ve renk
        pygame.draw.line(surface, (255, 255, 255), (self.x, self.y), (end_x, end_y), width=max(1, int(2 * self.life)))
        pygame.draw.line(surface, self.color, (self.x, self.y), (end_x, end_y), width=max(1, int(3 * self.life)))


class JuiceManager:
    """Tüm ekran sarsıntısı, hitstop ve kıvılcım efektlerini tek noktadan yönetir."""
    def __init__(self):
        self.freeze_timer = 0.0
        self.trauma = 0.0          # 0.0 - 1.0 arası sarsıntı gücü
        self.max_shake_offset = 14 # Maksimum piksel kayması
        self.sparks: list[Spark] = []

    def hitstop(self, duration: float = 0.05):
        """Kılıç vurduğunda veya ok sektiğinde dünyayı anlık dondurur (0.04-0.08 sn idealdir)."""
        self.freeze_timer = max(self.freeze_timer, duration)

    def add_trauma(self, amount: float):
        """Organik sarsıntı ekler (Hafif vuruş: 0.25, Sert darbe/Deflect: 0.5, Patlama: 0.8)."""
        self.trauma = min(1.0, self.trauma + amount)

    def emit_sparks(self, x: float, y: float, count: int = 10, base_angle: float = 0.0, spread: float = 60.0, color: tuple = (0, 240, 255)):
        """Darbe noktasından fırlayan neon kıvılcımlar saçar."""
        for _ in range(count):
            ang_deg = base_angle + random.uniform(-spread / 2, spread / 2)
            rad = math.radians(ang_deg)
            spd = random.uniform(250, 650)
            self.sparks.append(Spark(x, y, rad, spd, color, length=random.uniform(8, 16)))

    def update(self, dt: float) -> bool:
        """
        Geriye True dönerse oyun o an 'Hitstop' modundadır; 
        yani fizik ve hareket güncellemeleri atlanmalıdır.
        """
        # 1. Kıvılcımları güncelle
        self.sparks = [s for s in self.sparks if s.update(dt)]

        # 2. Sarsıntı sönümlenmesi (Decay)
        if self.trauma > 0:
            self.trauma = max(0.0, self.trauma - 1.8 * dt)

        # 3. Hitstop sayacı
        if self.freeze_timer > 0:
            self.freeze_timer -= dt
            return True # Donma aktif
        return False

    def get_shake_offset(self) -> tuple[int, int]:
        """Karesel (trauma²) sarsıntı ofseti döndürür. Titreme çok organik hissettirir."""
        if self.trauma <= 0.01:
            return 0, 0
        shake = self.trauma * self.trauma # Non-linear sönümleme
        angle = random.uniform(0, math.tau)
        dist = shake * self.max_shake_offset
        return int(math.cos(angle) * dist), int(math.sin(angle) * dist)

    def draw_sparks(self, surface: pygame.Surface):
        for s in self.sparks:
            s.draw(surface)