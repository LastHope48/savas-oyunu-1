import pygame
import pygame.gfxdraw
import copy


def draw_aa_line(surface, color, start, end, width=10):
    x1, y1 = start
    x2, y2 = end

    pygame.draw.line(
        surface,
        color,
        start,
        end,
        width
    )

    radius = width / 2

    pygame.gfxdraw.filled_circle(
        surface,
        round(x1),
        round(y1),
        round(radius),
        color
    )

    pygame.gfxdraw.filled_circle(
        surface,
        round(x2),
        round(y2),
        round(radius),
        color
    )

    pygame.gfxdraw.aacircle(
        surface,
        round(x1),
        round(y1),
        round(radius),
        color
    )

    pygame.gfxdraw.aacircle(
        surface,
        round(x2),
        round(y2),
        round(radius),
        color
    )

def invert_dict(d: dict):
    return {v: k for k, v in d.items()}

def draw_sword_at_pivot(surface, sword_image, hand_pos, angle, pivot_offset=(6, None)):
    """
    Kılıcı kabza noktasından döndürerek el pozisyonuna çizer.
    - hand_pos: Elin ekrandaki (x, y) piksel koordinatı
    - angle: Kılıcın dönüş açısı (derece)
    - pivot_offset: Kabzanın kılıç görseli içindeki konumu (x: kabza X, y: kabza Y).
      (Varsayılan olarak kılıcın sol-orta veya alt-orta kabzası baz alınır)
    """
    w, h = sword_image.get_size()
    # Eğer pivot Y verilmediyse dikeyde ortala
    px = pivot_offset[0]
    py = h // 2 if pivot_offset[1] is None else pivot_offset[1]

    # Kabza noktasından kılıcın merkezine olan vektör
    pivot_to_center = pygame.math.Vector2(w / 2 - px, h / 2 - py)
    
    # Vektörü açıyla döndür (Pygame'de Y aşağı doğru olduğu için eksi açı)
    rotated_offset = pivot_to_center.rotate(-angle)

    # Kılıç görselini döndür
    rotated_image = pygame.transform.rotate(sword_image, angle)
    
    # Yeni döndürülmüş görselin merkezini elin konumuna göre hesapla
    rect = rotated_image.get_rect()
    rect.center = (hand_pos[0] + rotated_offset.x, hand_pos[1] + rotated_offset.y)

    surface.blit(rotated_image, rect)

def create_player_dialogue_portrait(
    width: int = 340,
    height: int = 430,
    facing_left: bool = False,
    include_sword: bool = True
) -> pygame.Surface:
    """
    Orijinal 'idle_0.png' çöp adam karakterini baz alarak yüksek çözünürlüklü
    ve pürüzsüz bir diyalog portresi oluşturur.
    
    Özellikler:
    - Ön gövde ve uzuvlar: Canlı Cyan Mavi (56, 182, 255)
    - Arka uzuvlar: Derinlik katan Koyu Mavi (24, 88, 145)
    - Kafa: Yuvarlak kask/kafa üzerinde beyaz kapsül vizör
    - Sırt: İsteğe bağlı açılı kılıç (include_sword=True)
    - 2x Supersampling: Kenarlarda piksel kırılması olmadan net çizim
    """
    # 1. 2 Kat Büyük Tuval (Anti-aliasing / pürüzsüzleştirme için)
    scale = 2
    sw, sh = width * scale, height * scale
    canvas = pygame.Surface((sw, sh), pygame.SRCALPHA)

    # Renk Paleti (idle_0.png'den birebir alınmıştır)
    COLOR_FRONT = (56, 182, 255)   # Ön uzuvlar, gövde ve kafa (#38B6FF)
    COLOR_BACK = (24, 88, 145)     # Arka kol ve arka bacak gölgesi (#185891)
    COLOR_VISOR = (255, 255, 255)  # Beyaz vizör çizgisi

    # İskelet ve Oran Hesaplamaları
    cx = sw * 0.48
    head_r = int(sh * 0.095)
    head_pos = (int(cx + sh * 0.08), int(sh * 0.19))

    neck = (int(head_pos[0] - sh * 0.015), int(head_pos[1] + head_r * 0.95))
    pelvis = (int(cx - sh * 0.02), int(sh * 0.58))
    limb_w = int(head_r * 0.62)

    def draw_bone(p1, p2, color, w=limb_w):
        """Yuvarlak eklemli pürüzsüz kemik/uzuv çizer."""
        pygame.draw.line(canvas, color, p1, p2, w)
        pygame.draw.circle(canvas, color, p1, w // 2)
        pygame.draw.circle(canvas, color, p2, w // 2)

    # ========================================================
    # 1. ARKA UZUVLAR (Koyu Mavi - Derinlik Hissi)
    # ========================================================
    # Arka Kol (Gövdenin gerisine bükülmüş duruş)
    back_shoulder = (int(neck[0] - sh * 0.015), int(neck[1] + sh * 0.02))
    back_elbow = (int(cx - sh * 0.14), int(sh * 0.46))
    back_hand = (int(cx - sh * 0.02), int(sh * 0.53))
    draw_bone(back_shoulder, back_elbow, COLOR_BACK)
    draw_bone(back_elbow, back_hand, COLOR_BACK)

    # Arka Bacak (Geriye doğru açılmış adım)
    back_hip = (int(pelvis[0] - sh * 0.015), int(pelvis[1]))
    back_knee = (int(cx - sh * 0.16), int(sh * 0.75))
    back_foot = (int(cx - sh * 0.18), int(sh * 0.95))
    draw_bone(back_hip, back_knee, COLOR_BACK)
    draw_bone(back_knee, back_foot, COLOR_BACK)

    # ========================================================
    # 2. SIRTTAKİ KILIÇ (İsteğe Bağlı)
    # ========================================================
    if include_sword:
        s_start = (int(cx - sh * 0.18), int(sh * 0.72))
        s_end = (int(cx + sh * 0.22), int(sh * 0.06))
        # Kın ve namlu
        pygame.draw.line(canvas, (35, 42, 52), s_start, s_end, int(limb_w * 0.75))
        pygame.draw.line(canvas, (220, 230, 245), s_start, s_end, int(limb_w * 0.40))
        # Muhafaza (Guard) & Kabza
        g_pos = (int(cx + sh * 0.13), int(sh * 0.20))
        pygame.draw.circle(canvas, (218, 165, 32), g_pos, int(limb_w * 0.6))
        draw_bone(g_pos, s_end, (45, 50, 60), int(limb_w * 0.5))

    # ========================================================
    # 3. ÖN GÖVDE VE ÖN UZUVLAR (Açık Cyan Mavi)
    # ========================================================
    # Gövde omurgası
    draw_bone(neck, pelvis, COLOR_FRONT, w=int(limb_w * 1.05))

    # Ön Bacak (Öne basan dik adım)
    front_hip = (int(pelvis[0] + sh * 0.015), int(pelvis[1]))
    front_knee = (int(cx + sh * 0.09), int(sh * 0.76))
    front_foot = (int(cx + sh * 0.12), int(sh * 0.95))
    draw_bone(front_hip, front_knee, COLOR_FRONT)
    draw_bone(front_knee, front_foot, COLOR_FRONT)

    # Ön Kol (Hafif öne-aşağı uzanan duruş)
    front_shoulder = (int(neck[0] + sh * 0.015), int(neck[1] + sh * 0.02))
    front_elbow = (int(cx + sh * 0.08), int(sh * 0.45))
    front_hand = (int(cx + sh * 0.22), int(sh * 0.53))
    draw_bone(front_shoulder, front_elbow, COLOR_FRONT)
    draw_bone(front_elbow, front_hand, COLOR_FRONT)

    # ========================================================
    # 4. KAFA VE VİZÖR
    # ========================================================
    # Kafa çemberi
    pygame.draw.circle(canvas, COLOR_FRONT, head_pos, head_r)

    # Beyaz Vizör (Kafanın sağ üst kenarına oturan yatay kapsül)
    vw = int(head_r * 0.82)
    vh = int(head_r * 0.25)
    vx = int(head_pos[0] + head_r * 0.12)
    vy = int(head_pos[1] - head_r * 0.22)
    visor_rect = pygame.Rect(vx, vy, vw, vh)
    pygame.draw.rect(canvas, COLOR_VISOR, visor_rect, border_radius=max(1, vh // 2))

    # ========================================================
    # 5. KÜÇÜLTME & YÖN AYARI
    # ========================================================
    final_surf = pygame.transform.smoothscale(canvas, (width, height))
    if facing_left:
        final_surf = pygame.transform.flip(final_surf, True, False)

    return final_surf