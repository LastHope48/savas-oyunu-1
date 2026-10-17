def calculate_size(initialized_size: int, initialized_screen_s: int, size: int):
    '''
    Ekran boyutuna göre boyut hesaplar. Dinamik boyut gerektiren objeler için.
    '''
    calculated = int(initialized_size * (size / initialized_screen_s))
    return calculated

# calcs.py
import pygame

pygame.init()
_info = pygame.display.Info()

# 4K bazlı referans çarpanı (Örn: 1080p'de 0.5 döner)
SCALE = _info.current_h / 1080.0

def scale(val: float | int) -> int:
    """Tekil piksel, hız veya yarıçap değerlerini ölçekler."""
    return int(val * SCALE)

def scale_size(w: int, h: int) -> tuple[int, int]:
    """Görsel boyutlarını (w, h) ölçekler."""
    return (int(w * SCALE), int(h * SCALE))
