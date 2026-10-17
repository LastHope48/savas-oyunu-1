import os
import random
import pygame

from basedir import BASE_DIR
from dfont import DynamicFont, MsgBox
from fonts import font3_univ
from screens.types import ScreenType
from screens.screen import Screen


class LoseScreen(Screen):
    PHASE_FREEZE = "freeze"        # 1. Siyah ekranda donma
    PHASE_GRAVE_POP = "grave_pop"  # 2. Tık sesiyle mezarın gelmesi
    PHASE_TYPING = "typing"        # 3. Daktilo yazısı
    PHASE_WAIT = "wait"            # 4. Yazı bitti, oyuncu girdi verene kadar bekleme
    PHASE_FADE_WHITE = "fade_out"  # 5. Beyaza bürünme

    # Çoklu diyalog grupları (İstediğin kadar metin ekleyebilirsin)
    QUOTES = [
        [
            "Henüz pes edemezsin...",
            "Kaderin burada son bulamaz.",
            "Lütfen kararlılığını koru!"
        ],
        [
            "Derin bir nefes al...",
            "Ve tekrar ayağa kalk.",
            "Bu dünyanın sana hâlâ ihtiyacı var."
        ],
        [
            "Yapabilirsin...",
            "Sana inanıyorum."
        ],
        [
            "Pes etmezsen başarırsın.",
            "İmkansız değil ya!"
        ]
    ]

    def __init__(self, game):
        super().__init__(game)

        # 1. Temel Görselleri Ham (Raw) Yükle
        assets_dir = os.path.join(BASE_DIR, "images")   
        
        player_img_path = os.path.join(assets_dir, r"stickman_sprites/idle_0.png")
        if os.path.exists(player_img_path):
            self.raw_player_img = pygame.image.load(player_img_path).convert_alpha()
        else:
            self.raw_player_img = pygame.Surface((60, 100), pygame.SRCALPHA)
            pygame.draw.rect(self.raw_player_img, (240, 240, 240), (0, 0, 60, 100), border_radius=8)

        grave_img_path = os.path.join(assets_dir, "grave.png")
        if os.path.exists(grave_img_path):
            self.raw_grave_img = pygame.image.load(grave_img_path).convert_alpha()
        else:
            self.raw_grave_img = self._create_procedural_grave()

        # Ölçeklenmiş görsellerin önbelleği
        self.player_img = None
        self.grave_img = None
        self.last_screen_size = (0, 0)

        # 2. Sesler
        sounds_dir = os.path.join(BASE_DIR, "sounds")
        musics_dir = os.path.join(BASE_DIR, "musics")
        
        click_path = os.path.join(sounds_dir, "click.wav")
        self.click_sfx = pygame.mixer.Sound(click_path) if os.path.exists(click_path) else None

        type_path = os.path.join(sounds_dir, "low_pitch_speak.wav")
        self.type_sfx = pygame.mixer.Sound(type_path) if os.path.exists(type_path) else None

        self.lose_music_path = os.path.join(musics_dir, "lose_music.ogg")

        # 3. Yazı Tipi
        self.font_path = os.path.join(BASE_DIR, "fonts/unifont-18.0.01.otf")
        if not os.path.exists(self.font_path):
            self.font_path = pygame.font.get_default_font()
        
        self.font = None
        self.msgbox = None

        # 4. Diyalog Durum Değişkenleri
        self.current_quote_group: list[str] = []
        self.quote_index: int = 0

        # 5. Durum Değişkenleri ve Sayaçlar
        self.phase = self.PHASE_FREEZE
        self.timer = 0.0
        self.fade_alpha = 0.0
        self.fade_speed = 130.0
        self.fade_surface = None

    def _create_procedural_grave(self) -> pygame.Surface:
        surf = pygame.Surface((180, 240), pygame.SRCALPHA)
        pygame.draw.rect(surf, (150, 150, 160), (20, 60, 140, 180), border_top_left_radius=70, border_top_right_radius=70)
        pygame.draw.rect(surf, (200, 200, 210), (20, 60, 140, 180), width=6, border_top_left_radius=70, border_top_right_radius=70)

        # RIP yazısı
        rip_text = font3_univ.return_text("R.I.P.", (80, 80, 90))
        rip_text_rect = rip_text.get_rect(center=(surf.get_width() // 2, surf.get_height() // 2))

        surf.blit(
            rip_text,
            rip_text_rect
        )

        pygame.draw.ellipse(surf, (70, 70, 80), (0, 210, 180, 30))
        return surf

    def _update_layout(self, screen_w: int, screen_h: int):
        """Ekran boyutu her değiştiğinde öğeleri orantılar."""
        if self.last_screen_size == (screen_w, screen_h):
            return

        self.last_screen_size = (screen_w, screen_h)

        # 1. Dinamik Font
        font_size = max(20, int(screen_h * 0.038))
        self.font = DynamicFont(self.font_path, font_size, 100)

        # 2. Karakter ve Mezar Ölçekleme
        target_obj_h = max(60, int(screen_h * 0.18))
        p_ratio = target_obj_h / self.raw_player_img.get_height()
        target_p_w = int(self.raw_player_img.get_width() * p_ratio)
        self.player_img = pygame.transform.smoothscale(self.raw_player_img, (target_p_w, target_obj_h))

        g_ratio = target_obj_h / self.raw_grave_img.get_height()
        target_g_w = int(self.raw_grave_img.get_width() * g_ratio)
        self.grave_img = pygame.transform.smoothscale(self.raw_grave_img, (target_g_w, target_obj_h))

        # 3. Dinamik MsgBox Konumu ve Boyutu
        box_w = int(screen_w * 0.72)
        box_h = int(screen_h * 0.22)
        box_x = (screen_w - box_w) // 2
        box_y = int(screen_h * 0.10)
        border_w = max(3, int(screen_h * 0.005))
        padding = max(12, int(screen_h * 0.025))

        if self.msgbox is not None:
            self.msgbox.x = box_x
            self.msgbox.y = box_y
            self.msgbox.width = box_w
            self.msgbox.height = box_h
            self.msgbox.font = self.font
            self.msgbox.border = border_w
            self.msgbox.padding = padding
        else:
            current_text = self.current_quote_group[self.quote_index] if self.current_quote_group else ""
            self.msgbox = MsgBox(
                text=current_text,
                font=self.font,
                width=box_w,
                height=box_h,
                x=box_x,
                y=box_y,
                color=(0, 0, 0),
                border=border_w,
                padding=padding,
                text_color=(255, 255, 255),
                typing_speed=12.0
            )

        # 4. Beyaz Perde Yüzeyi
        self.fade_surface = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        

    def _setup_current_quote_msgbox(self):
        """O anki sıradaki metni MsgBox içerisine yerleştirip daktiloyu başlatır."""
        screen_w, screen_h = self.last_screen_size
        box_w = int(screen_w * 0.72)
        box_h = int(screen_h * 0.22)
        box_x = (screen_w - box_w) // 2
        box_y = int(screen_h * 0.10)
        border_w = max(3, int(screen_h * 0.005))
        padding = max(12, int(screen_h * 0.025))

        current_text = self.current_quote_group[self.quote_index]
        self.msgbox = MsgBox(
            text=current_text,
            font=self.font,
            width=box_w,
            height=box_h,
            x=box_x,
            y=box_y,
            color=(0, 0, 0),
            border=border_w,
            padding=padding,
            text_color=(255, 255, 255),
            typing_speed=12.0
        )
        self.msgbox.start_typing()

    def _advance_dialogue(self):
        """Bir sonraki metne geçer veya son metindeyse beyaza bürünmeyi başlatır."""
        self.quote_index += 1

        if self.quote_index < len(self.current_quote_group):
            # Sıradaki metne geç
            self._setup_current_quote_msgbox()
            self.phase = self.PHASE_TYPING
        else:
            # Grup bitti, ekran beyaza dönsün
            self.phase = self.PHASE_FADE_WHITE

    def on_enter(self, transfer_datas=None):
        self.phase = self.PHASE_FREEZE
        self.timer = 0.0
        self.fade_alpha = 0.0
        self.msgbox = None
        self.last_screen_size = (0, 0)

        # Rastgele bir diyalog grubu seç ve ilk metinden başla
        self.current_quote_group = random.choice(self.QUOTES)
        self.quote_index = 0

        # Eski müziği kes
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()

        info = pygame.display.Info()
        self._update_layout(info.current_w, info.current_h)

    def handle_event(self, event: pygame.event.Event):
        # Sol tık VEYA Boşluk (Space) tuşu kontrolü
        is_action = (
            (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1) or
            (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE)
        )

        if not is_action:
            return

        # 1. Yazı yazılıyorsa tek tuşla anında tamamla
        if self.phase == self.PHASE_TYPING and self.msgbox and not self.msgbox.finished:
            self.msgbox.skip_typing()
            self.phase = self.PHASE_WAIT
            return

        # 2. Yazı bittiyse (PHASE_WAIT) sonraki metne veya beyaza geç
        if self.phase == self.PHASE_WAIT:
            self._advance_dialogue()

    def update(self, dt: float):
        self.timer += dt

        # 1. AŞAMA: DONMA (1 saniye sessizlik)
        if self.phase == self.PHASE_FREEZE:
            if self.timer >= 1.0:
                self.phase = self.PHASE_GRAVE_POP
                self.timer = 0.0

                if self.click_sfx:
                    self.click_sfx.play()

                if os.path.exists(self.lose_music_path):
                    try:
                        pygame.mixer.music.load(self.lose_music_path)
                        pygame.mixer.music.play(-1)
                    except pygame.error:
                        pass

        # 2. AŞAMA: MEZAR BELİRDİ (0.5 sn bekleyip ilk metni başlat)
        elif self.phase == self.PHASE_GRAVE_POP:
            if self.timer >= 0.5:
                self.phase = self.PHASE_TYPING
                self.timer = 0.0
                if self.msgbox:
                    self.msgbox.start_typing()

        # 3. AŞAMA: DAKTİLO
        elif self.phase == self.PHASE_TYPING:
            if self.msgbox:
                self.msgbox.update(dt, sound=self.type_sfx, volume=0.8, play=True)
                if self.msgbox.finished:
                    # Yazı bitti -> Oyuncu basana kadar beklemek için PHASE_WAIT'e al
                    self.phase = self.PHASE_WAIT

        # 4. AŞAMA: BEKLEME (Otomatik geçiş kaldırıldı, kullanıcı girdisi beklenir)
        elif self.phase == self.PHASE_WAIT:
            pass

        # 5. AŞAMA: BEYAZA BÜRÜNME
        elif self.phase == self.PHASE_FADE_WHITE:
            self.fade_alpha += self.fade_speed * dt
            if self.fade_alpha >= 255.0:
                self.fade_alpha = 255.0
                self._return_to_main_menu()

    def draw(self, surface: pygame.Surface):
        screen_w, screen_h = surface.get_size()
        self._update_layout(screen_w, screen_h)

        surface.fill((0, 0, 0))

        center_x = screen_w // 2
        center_y = int(screen_h * 0.64)

        if self.phase == self.PHASE_FREEZE:
            if self.player_img:
                p_rect = self.player_img.get_rect(center=(center_x, center_y))
                surface.blit(self.player_img, p_rect)
        else:
            if self.grave_img:
                g_rect = self.grave_img.get_rect(center=(center_x, center_y))
                surface.blit(self.grave_img, g_rect)

        # Üstteki MsgBox
        if self.phase in (self.PHASE_TYPING, self.PHASE_WAIT, self.PHASE_FADE_WHITE):
            if self.msgbox:
                self.msgbox.draw(surface)

        # Beyaza kararma
        if self.phase == self.PHASE_FADE_WHITE and self.fade_alpha > 0 and self.fade_surface:
            self.fade_surface.fill((255, 255, 255, int(self.fade_alpha)))
            surface.blit(self.fade_surface, (0, 0))

    def _return_to_main_menu(self):
        pygame.mixer.music.stop()
        if hasattr(self.game, "reset"):
            self.game.reset()

        self.game.dump("last_music", self.lose_music_path)
        self.game.screen_manager.set_screen(ScreenType.MENU)