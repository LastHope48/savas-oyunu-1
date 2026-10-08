import os
import random
import pygame
from .menu_screen import MenuScreen
from basedir import BASE_DIR
from classes import Button
from fonts import all_font1
import colours
from screens.types import ScreenType


class CassetteWorld:
    """Tek bir dünyanın kaset çalarını ve durumunu yöneten veri sınıfı."""
    def __init__(self, world_id: int, title: str, preview_path: str, unlocked: bool = True):
        self.world_id = world_id
        self.title = title
        self.preview_path = preview_path
        self.unlocked = unlocked

        # Önizleme görselini yükle
        self.preview_surf = None
        if os.path.exists(preview_path):
            self.preview_surf = pygame.image.load(preview_path).convert()


class WorldSelectScreen(MenuScreen):
    # -------------------------------------------------------------
    # GÖRSEL ÜZERİNDEKİ BAĞIL KOORDİNATLAR (Deck Görseline Göre Oranlar)
    # -------------------------------------------------------------
    # Monitör camının deck görseli içindeki konumu (x_oran, y_oran, w_oran, h_oran)
    MONITOR_REL = (0.22, 0.12, 0.56, 0.32)
    # Kaset yuvasının iç haznesi
    SLOT_REL = (0.24, 0.58, 0.52, 0.28)

    # Durumlar
    STATE_IDLE = "idle"           # Gezinme / Scroll
    STATE_HOVER = "hover"         # Kaset hizalanıyor
    STATE_INSERTING = "inserting" # Kaset içeri giriyor
    STATE_LOCKED = "locked"       # Kaset oturdu, ekran açıldı
    STATE_ZOOMING = "zooming"     # CRT ekrana zoom yapılıyor

    def __init__(self, game):
        super().__init__(game)

        self.worlds_data: list[dict] = None

        self.screen_w = self.game.info.current_w
        self.screen_h = self.game.info.current_h

        # 1. Görselleri Yükle
        self.base_dir = BASE_DIR
        assets_dir = os.path.join(self.base_dir, "images")

        # Kaset Çalar (Deck)
        raw_deck = pygame.image.load(os.path.join(assets_dir, "deck_terminal.png")).convert_alpha()
        deck_target_h = int(self.screen_h * 0.78)
        scale_ratio = deck_target_h / raw_deck.get_height()
        deck_target_w = int(raw_deck.get_width() * scale_ratio)
        self.deck_img = pygame.transform.smoothscale(raw_deck, (deck_target_w, deck_target_h))
        self.deck_w, self.deck_h = self.deck_img.get_size()

        # Kaset
        raw_cassette = pygame.image.load(os.path.join(assets_dir, "cassette.png")).convert_alpha()
        # Kasetin yuvaya tam sığması için yuva genişliğine oranla boyutlandırıyoruz
        slot_pixel_w = self.deck_w * self.SLOT_REL[2]
        c_ratio = (slot_pixel_w * 0.94) / raw_cassette.get_width()
        self.cassette_img = pygame.transform.smoothscale(
            raw_cassette,
            (int(raw_cassette.get_width() * c_ratio), int(raw_cassette.get_height() * c_ratio))
        )
        self.cassette_w, self.cassette_h = self.cassette_img.get_size()

        # Uzun Dikey Arka Plan (Kaydırmalı)
        bg_path = os.path.join(assets_dir, "green_pattern.png")
        if os.path.exists(bg_path):
            self.bg_img = pygame.image.load(bg_path).convert()

            self.bg_img = pygame.transform.scale_by(self.bg_img, 2 * self.game.info.current_h / self.bg_img.get_height())
        else:
            # Yedek boş degrade zemin
            self.bg_img = pygame.Surface((self.screen_w, self.screen_h * 3))
            self.bg_img.fill((16, 20, 26))

        

        # 2. Dünyaları Tanımla
        self.worlds = [
            CassetteWorld(1, "Sektör 01: Çatı Katı", os.path.join(assets_dir, "world1_preview.png"), unlocked=True),
            # CassetteWorld(2, "Sektör 02: Siber Fabrika", os.path.join(assets_dir, "world2_preview.png"), unlocked=True),
            # CassetteWorld(3, "Sektör 03: Cehennem Hattı", os.path.join(assets_dir, "world3_preview.png"), unlocked=False),
        ]

        # 3. Kaydırma (Scroll) Değişkenleri
        self.scroll_y = 0.0
        self.target_scroll_y = 0.0
        self.world_spacing = self.screen_h * 0.92  # Her dünya arası dikey mesafe
        self.max_scroll = (len(self.worlds) - 1) * self.world_spacing

        # 4. Kaset Pozisyon & Fizik Değişkenleri
        self.selected_world_idx = 0
        self.hovered_world_idx = -1
        self.state = self.STATE_IDLE

        # Sağ alttaki bekleme konumu
        self.idle_pos = pygame.Vector2(self.screen_w - self.cassette_w * 0.85, self.screen_h - self.cassette_h * 0.85)
        self.idle_angle = 15.0  # 15 derece eğik duruş

        self.cassette_pos = pygame.Vector2(self.idle_pos)
        self.cassette_angle = self.idle_angle

        # Animasyon sayaçları
        self.insert_timer = 0.0
        self.insert_duration = 0.85
        self.locked_timer = 0.0
        self.zoom_factor = 1.0

        # CRT Statik Gürültü Yüzeyi (Önceden üretilmiş 4 kare döngü - FPS düşmesini engeller)
        self.noise_frames = self._generate_noise_cache()
        self.noise_idx = 0

        # Monitör sabit boyutları
        self.mon_w = int(self.deck_w * self.MONITOR_REL[2])
        self.mon_h = int(self.deck_h * self.MONITOR_REL[3])
        self.corner_radius = int(self.mon_h * 0.09)  # CRT camının köşe kavisi (~22px)

        # -------------------------------------------------------------
        # CRT YUVARLATILMIŞ KÖŞE MASKESİ (ALPHA MASK)
        # -------------------------------------------------------------
        self.crt_mask = pygame.Surface((self.mon_w, self.mon_h), pygame.SRCALPHA)
        self.crt_mask.fill((0, 0, 0, 0))  # Tamamen şeffaf taban
        # Sadece yuvarlatılmış dikdörtgenin içini beyaza boyuyoruz:
        pygame.draw.rect(
            self.crt_mask,
            (255, 255, 255, 255),
            (0, 0, self.mon_w, self.mon_h),
            border_radius=self.corner_radius
        )

        self.exit_button = Button(
            0, 0, 100, 100,
            "X",
            all_font1,
            colours.RED,
            colours.WHITE,
            [ScreenType.WORLD_SELECT],
            design="bevel",
            border_radius=0
        )

    def _generate_noise_cache(self) -> list[pygame.Surface]:
        frames = []
        mw = int(self.deck_w * self.MONITOR_REL[2])
        mh = int(self.deck_h * self.MONITOR_REL[3])
        for _ in range(4):
            surf = pygame.Surface((mw // 2, mh // 2))
            for y in range(mh // 2):
                val = random.randint(18, 45)
                surf.fill((val, val + random.randint(5, 15), val + 20), (0, y, mw // 2, 1))
            frames.append(pygame.transform.scale(surf, (mw, mh)))
        return frames

    # =============================================================
    # EVENT VE ETKİLEŞİM
    # =============================================================
    def handle_event(self, event: pygame.event.Event):
        """ScreenManager her karede tek tek event gönderir."""

        if self.exit_button.clicked(event, ScreenType.WORLD_SELECT):
            self.game.screen_manager.set_screen(ScreenType.MENU)
            return
        
        # Fare Tekerleği ile Dikey Scroll
        if event.type == pygame.MOUSEWHEEL and self.state in (self.STATE_IDLE, self.STATE_HOVER):
            self.target_scroll_y -= event.y * 140
            self.target_scroll_y = max(0.0, min(self.max_scroll, self.target_scroll_y))

        # Sol Tıklama: Kaseti Yuvaya İt
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

            if self.state == self.STATE_HOVER and self.hovered_world_idx != -1:
                world = self.worlds[self.hovered_world_idx]
                if world.unlocked:
                    self.selected_world_idx = self.hovered_world_idx
                    self.state = self.STATE_INSERTING
                    self.insert_timer = 0.0

                    # Tıklama anındaki mevcut konum ve açıyı başlangıç olarak sakla:
                    self.insert_start_x = self.cassette_pos.x
                    self.insert_start_y = self.cassette_pos.y
                    self.insert_start_angle = self.cassette_angle

    # =============================================================
    # GÜNCELLEME VE ANİMASYON DÖNGÜSÜ
    # =============================================================
    def update(self, dt: float):
        self.exit_button.on_mouse()

        self.exit_button.set_center(
            self.game.width // 60,
            self.game.width // 60
        )

        # 1. Pürüzsüz Scroll Yaylanması (Lerp)
        self.scroll_y += (self.target_scroll_y - self.scroll_y) * min(1.0, 10.0 * dt)
        self.noise_idx = (self.noise_idx + 1) % len(self.noise_frames)

        # Fare pozisyonu tespiti
        mx, my = pygame.mouse.get_pos()

        # Hangi dünyanın kaset çalarının üzerindeyiz?
        if self.state in (self.STATE_IDLE, self.STATE_HOVER):
            self.hovered_world_idx = -1
            for i, world in enumerate(self.worlds):
                deck_x = (self.screen_w - self.deck_w) // 2
                deck_y = int(self.screen_h * 0.12 + i * self.world_spacing - self.scroll_y)
                deck_rect = pygame.Rect(deck_x, deck_y, self.deck_w, self.deck_h)

                if deck_rect.collidepoint(mx, my):
                    self.hovered_world_idx = i
                    break

            if self.hovered_world_idx != -1 and self.worlds[self.hovered_world_idx].unlocked:
                self.state = self.STATE_HOVER
            else:
                self.state = self.STATE_IDLE

        # ---------------------------------------------------------
        # 2. KASETİN POZİSYON ANİMASYONU
        # ---------------------------------------------------------
        if self.state == self.STATE_IDLE:
            # Sağ altta 15 derece dinlenme pozisyonu
            self.cassette_pos += (self.idle_pos - self.cassette_pos) * min(1.0, 8.0 * dt)
            self.cassette_angle += (self.idle_angle - self.cassette_angle) * min(1.0, 8.0 * dt)

        elif self.state == self.STATE_HOVER:
            # Kaset çaların yuvasının tam önüne hizalan ve dikleş (0 derece)
            deck_x = (self.screen_w - self.deck_w) // 2
            deck_y = int(self.screen_h * 0.12 + self.hovered_world_idx * self.world_spacing - self.scroll_y)

            slot_x = deck_x + self.deck_w * self.SLOT_REL[0]
            slot_y = deck_y + self.deck_h * self.SLOT_REL[1]

            target_pos = pygame.Vector2(slot_x + (self.deck_w * self.SLOT_REL[2] - self.cassette_w) // 2, slot_y - self.cassette_h * 0.45)
            self.cassette_pos += (target_pos - self.cassette_pos) * min(1.0, 11.0 * dt)
            self.cassette_angle += (0.0 - self.cassette_angle) * min(1.0, 12.0 * dt)

        elif self.state == self.STATE_INSERTING:
            self.insert_timer += dt
            t = min(1.0, self.insert_timer / self.insert_duration)

            # Ease-in-out yumuşatma eğrisi
            t_curve = t * t * (3.0 - 2.0 * t)

            deck_x = (self.screen_w - self.deck_w) // 2
            deck_y = int(self.screen_h * 0.12 + self.selected_world_idx * self.world_spacing - self.scroll_y)

            slot_x = deck_x + self.deck_w * self.SLOT_REL[0]
            slot_y = deck_y + self.deck_h * self.SLOT_REL[1]
            slot_w = self.deck_w * self.SLOT_REL[2]

            # Yuvanın tam yatay orta noktası
            target_x = slot_x + (slot_w - self.cassette_w) // 2
            end_y = slot_y + 12  # Yuvanın tabanına oturduğu derinlik

            # -------------------------------------------------------------
            # KRİTİK DÜZELTME: X VE AÇI DA MERKEZE HİZALANIYOR
            # -------------------------------------------------------------
            # Hareketin ilk %30'luk diliminde kaset hızla yuvanın tam ortasına ve 0° dikliğe oturur
            align_t = min(1.0, t * 3.3)
            self.cassette_pos.x = self.insert_start_x + (target_x - self.insert_start_x) * align_t
            self.cassette_angle = self.insert_start_angle * (1.0 - align_t)

            # Y ekseninde yuvaya doğru iniş:
            start_y = slot_y - self.cassette_h * 0.45
            base_start_y = getattr(self, "insert_start_y", start_y)
            self.cassette_pos.y = base_start_y + (end_y - base_start_y) * t_curve

            if t >= 1.0:
                self.state = self.STATE_LOCKED
                self.locked_timer = 0.0
                self.cassette_pos.x = target_x
                self.cassette_pos.y = end_y
                self.cassette_angle = 0.0

        elif self.state == self.STATE_LOCKED:
            # Kaset oturdu: Ekran açılır, 0.6 saniye bekleyip zoom başlatır
            self.locked_timer += dt
            if self.locked_timer >= 0.6:
                self.state = self.STATE_ZOOMING

        elif self.state == self.STATE_ZOOMING:
            # Monitöre doğru büyüme (Zoom in transition)
            self.zoom_factor += (5.5 - self.zoom_factor) * min(1.0, 4.0 * dt)
            if self.zoom_factor >= 4.8:
                self._start_game(self.worlds[self.selected_world_idx].world_id)

    # =============================================================
    # ÇİZİM
    # =============================================================
    def draw(self, surface: pygame.Surface):
        surface.fill('black')

        # 1. Uzun Arka Plan
        bg_y = -int(self.scroll_y * 0.5)
        surface.blit(self.bg_img, (0, bg_y))

        # 2. Her Dünyanın Kaset Çalarını Çiz
        for i, world in enumerate(self.worlds):
            deck_x = (self.screen_w - self.deck_w) // 2
            deck_y = int(self.screen_h * 0.12 + i * self.world_spacing - self.scroll_y)
            deck_rect = pygame.Rect(deck_x, deck_y, self.deck_w, self.deck_h)

            if deck_rect.bottom < 0 or deck_rect.top > self.screen_h:
                continue

            # -------------------------------------------------------------
            # ADIM 1: ÖNCE KASET ÇALAR GÖVDESİNİ ÇİZ
            # -------------------------------------------------------------
            surface.blit(self.deck_img, (deck_x, deck_y))

            # -------------------------------------------------------------
            # ADIM 2: MONİTÖR CAMININ ÜSTÜNE YUVARLATILMIŞ EKRANI BAS
            # -------------------------------------------------------------
            mon_x = int(deck_x + self.deck_w * self.MONITOR_REL[0])
            mon_y = int(deck_y + self.deck_h * self.MONITOR_REL[1])
            monitor_rect = pygame.Rect(mon_x, mon_y, self.mon_w, self.mon_h)

            is_active = (self.state in (self.STATE_INSERTING, self.STATE_LOCKED, self.STATE_ZOOMING)) and (self.selected_world_idx == i)

            # Şeffaflık destekli (SRCALPHA) ekran yüzeyi
            screen_surf = pygame.Surface((self.mon_w, self.mon_h), pygame.SRCALPHA)

            if is_active and world.preview_surf:
                scaled_preview = pygame.transform.smoothscale(world.preview_surf, (self.mon_w, self.mon_h))
                screen_surf.blit(scaled_preview, (0, 0))

                # CRT Tarama Çizgileri (Scanlines)
                for line_y in range(0, self.mon_h, 4):
                    pygame.draw.line(screen_surf, (0, 0, 0, 65), (0, line_y), (self.mon_w, line_y))
            else:
                # Aktif değilken karıncalanma
                screen_surf.blit(self.noise_frames[self.noise_idx], (0, 0))

            # Kilitli dünya ise kırmızı filtre
            if not world.unlocked:
                screen_surf.fill((160, 20, 20), special_flags=pygame.BLEND_MULT)

            # Köşeleri maskeyle kesip yuvarlatıyoruz
            screen_surf.blit(self.crt_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

            # CRT Cam Çerçeve Vurgusu (İçbükey derinlik çizgisi)
            pygame.draw.rect(
                screen_surf,
                (12, 18, 24, 180),
                (0, 0, self.mon_w, self.mon_h),
                width=3,
                border_radius=self.corner_radius
            )

            # Ekrana bas (TEK SEFER!)
            surface.blit(screen_surf, monitor_rect)

        # -------------------------------------------------------------
        # 3. KASET ÇİZİMİ (Clipping ve Giriş Animasyonu)
        # -------------------------------------------------------------
        active_deck_y = int(self.screen_h * 0.12 + self.selected_world_idx * self.world_spacing - self.scroll_y)
        active_deck_x = (self.screen_w - self.deck_w) // 2

        if self.state in (self.STATE_INSERTING, self.STATE_LOCKED):
            # Kaset yuvasının dikey giriş boğazı:
            slot_clip_rect = pygame.Rect(
                active_deck_x + self.deck_w * self.SLOT_REL[0],
                active_deck_y + self.deck_h * (self.SLOT_REL[1] - 0.20),
                self.deck_w * self.SLOT_REL[2],
                self.deck_h * (self.SLOT_REL[3] + 0.30)
            )

            surface.set_clip(slot_clip_rect)

            # Eğer açı henüz 0'a inmediyse döndürülerek çizilir, aksi halde düz çizilir
            if abs(self.cassette_angle) > 0.5:
                rotated_c = pygame.transform.rotate(self.cassette_img, self.cassette_angle)
                c_rect = rotated_c.get_rect(center=(
                    int(self.cassette_pos.x + self.cassette_w // 2),
                    int(self.cassette_pos.y + self.cassette_h // 2)
                ))
                surface.blit(rotated_c, c_rect)
            else:
                surface.blit(self.cassette_img, (int(self.cassette_pos.x), int(self.cassette_pos.y)))

            surface.set_clip(None)
        else:
            # Beklerken veya hover sırasında serbest çizim
            rotated_c = pygame.transform.rotate(self.cassette_img, self.cassette_angle)
            c_rect = rotated_c.get_rect(center=(
                int(self.cassette_pos.x + self.cassette_w // 2),
                int(self.cassette_pos.y + self.cassette_h // 2)
            ))
            surface.blit(rotated_c, c_rect)

        self.exit_button.draw(surface)
        

        # -------------------------------------------------------------
        # 4. ZOOM GEÇİŞİ
        # -------------------------------------------------------------
        if self.state == self.STATE_ZOOMING:
            deck_x = (self.screen_w - self.deck_w) // 2
            deck_y = int(self.screen_h * 0.12 + self.selected_world_idx * self.world_spacing - self.scroll_y)
            center_x = deck_x + self.deck_w * (self.MONITOR_REL[0] + self.MONITOR_REL[2] / 2)
            center_y = deck_y + self.deck_h * (self.MONITOR_REL[1] + self.MONITOR_REL[3] / 2)

            w = int(self.screen_w * self.zoom_factor)
            h = int(self.screen_h * self.zoom_factor)
            zoomed = pygame.transform.scale(surface, (w, h))

            zx = int(center_x - (center_x * self.zoom_factor))
            zy = int(center_y - (center_y * self.zoom_factor))
            surface.blit(zoomed, (zx, zy))
    def _start_game(self, world_id: int):
        """Kaset tamamen yüklendiğinde ve zoom bittiğinde oyunu başlatan köprü."""
        # ScreenManager ekran geçişi (Senin projenin ScreenType enum yapısına göre):
        from screens.screen_manager import ScreenType
        
        if hasattr(self.game, "current_world_id"):
            self.game.current_world_id = world_id

        self.game.screen_manager.get_screen(ScreenType.GAME).start_new_game()

        self.game.screen_manager.set_screen(ScreenType.GAME)

    def on_enter(self, transfer_datas):
        if self.game.dump("last_music") != os.path.join(BASE_DIR, r"musics/mystery_music.ogg"):
            self.game.mixer.music.load(
                os.path.join(
                    BASE_DIR,
                    r"musics/mystery_music.ogg"
                )
            )

            self.game.mixer.music.play(-1)

    def on_exit(self):
        self.game.dump(
            "last_music",
            os.path.join(
                    BASE_DIR,
                    r"musics/mystery_music.ogg"
            )
        )
