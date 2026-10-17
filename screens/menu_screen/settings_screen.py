import os
import threading
import pygame
from basedir import BASE_DIR
from fonts import get_font
from console import Console
from classes import Button
import classes
from lang_support import Lang
import colours
from screens.types import ScreenType
from .menu_screen import MenuScreen
from update_manager import check_for_update, prepare_update
from userfont import userFont


class UpdateWindow:
    """Untitled Tag Game / Retro OS tarzı sürüklenebilir pencere."""
    def __init__(self, x: int, y: int, w: int = 560, h: int = 250):
        self.w = w
        self.h = h
        self.x = x
        self.y = y
        self.header_h = 36

        self.is_open = False
        self.is_dragging = False
        self.drag_offset_x = 0
        self.drag_offset_y = 0

        # Durum değişkenleri
        self.status_text = ""
        self.progress = 0.0
        self.is_loading = False
        self.is_finished = False
        self.has_error = False

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(self.x, self.y, self.w, self.h)

    @property
    def header_rect(self) -> pygame.Rect:
        return pygame.Rect(self.x, self.y, self.w, self.header_h)

    @property
    def close_btn_rect(self) -> pygame.Rect:
        return pygame.Rect(self.x + self.w - 32, self.y + 5, 26, 26)

    def open(self, start_status="Başlatılıyor..."):
        self.is_open = True
        self.status_text = start_status
        self.progress = 0.0
        self.is_loading = True
        self.is_finished = False
        self.has_error = False

    def close(self):
        self.is_open = False
        self.is_dragging = False

    def handle_event(self, event: pygame.event.Event, sfx_manager=None, sfx_vol=1.0) -> bool:
        """Pencere açıksa olayları tüketir (Modal davranış)."""
        if not self.is_open:
            return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # 1. Kapat Butonu Tıklandı mı?
            if self.close_btn_rect.collidepoint(event.pos):
                if sfx_manager:
                    sfx_manager.play("click", sfx_vol)
                self.close()
                return True

            # 2. Başlık Çubuğuna Basıldı mı? (Sürüklemeyi Başlat)
            if self.header_rect.collidepoint(event.pos):
                self.is_dragging = True
                self.drag_offset_x = event.pos[0] - self.x
                self.drag_offset_y = event.pos[1] - self.y
                return True

            # Pencerenin içine tıklandıysa arka planı engelle
            if self.rect.collidepoint(event.pos):
                return True

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.is_dragging = False

        elif event.type == pygame.MOUSEMOTION:
            if self.is_dragging:
                # Pencereyi sürükle
                self.x = event.pos[0] - self.drag_offset_x
                self.y = event.pos[1] - self.drag_offset_y
                return True

        # Pencere açıkken alt katmandaki butonların tetiklenmesini engelle
        return self.rect.collidepoint(pygame.mouse.get_pos())

    def update(self, screen_w: int, screen_h: int):
        if not self.is_open:
            return

        # Ekran sınırlarının dışına kaçmasını engelle
        self.x = max(10, min(screen_w - self.w - 10, self.x))
        self.y = max(10, min(screen_h - self.h - 10, self.y))

    def draw(self, surface: pygame.Surface, font_header: userFont, font_body: userFont):
        if not self.is_open:
            return

        # -------------------------------------------------------------
        # 1. ARKA PLAN KARARTMASI (MODAL VURGUSU)
        # -------------------------------------------------------------
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 110))
        surface.blit(overlay, (0, 0))

        # -------------------------------------------------------------
        # 2. PENCERE GÖVDESİ & SİBER GÖLGE
        # -------------------------------------------------------------
        # Dış gölge
        shadow_rect = self.rect.move(6, 8)
        pygame.draw.rect(surface, (8, 10, 15, 180), shadow_rect, border_radius=10)

        # Ana Gövde (Koyu Grafit OS Paneli)
        pygame.draw.rect(surface, (18, 22, 32), self.rect, border_radius=10)
        # Siber Neon Kenarlık
        pygame.draw.rect(surface, (0, 240, 255), self.rect, width=2, border_radius=10)

        # -------------------------------------------------------------
        # 3. BAŞLIK ÇUBUĞU (TITLEBAR)
        # -------------------------------------------------------------
        pygame.draw.rect(
            surface,
            (26, 34, 48),
            self.header_rect,
            border_top_left_radius=10,
            border_top_right_radius=10
        )
        pygame.draw.line(surface, (0, 240, 255), self.header_rect.bottomleft, self.header_rect.bottomright, 1)

        # Başlık İkonu & Yazısı
        title_surf = font_header.return_text("[SYS_UPDATE_DAEMON.EXE]", (0, 240, 255))
        surface.blit(title_surf, (self.x + 14, self.y + 8))

        # Kapatma ("X") Butonu
        mx, my = pygame.mouse.get_pos()
        close_hover = self.close_btn_rect.collidepoint(mx, my)
        close_bg = (220, 50, 50) if close_hover else (35, 45, 60)
        pygame.draw.rect(surface, close_bg, self.close_btn_rect, border_radius=4)
        
        # 'X' Çizgileri
        cb = self.close_btn_rect
        pygame.draw.line(surface, (255, 255, 255), (cb.left + 7, cb.top + 7), (cb.right - 7, cb.bottom - 7), 2)
        pygame.draw.line(surface, (255, 255, 255), (cb.right - 7, cb.top + 7), (cb.left + 7, cb.bottom - 7), 2)

        # -------------------------------------------------------------
        # 4. İÇERİK: LOG / DURUM ALANI (TERMINAL METNİ)
        # -------------------------------------------------------------
        body_box = pygame.Rect(self.x + 20, self.y + 50, self.w - 40, 72)
        pygame.draw.rect(surface, (12, 16, 24), body_box, border_radius=6)
        pygame.draw.rect(surface, (40, 52, 70), body_box, width=1, border_radius=6)

        # Durum Rengi (Hata: Kırmızı, Bitti: Yeşil, Yükleniyor: Camgöbeği)
        status_color = (255, 80, 80) if self.has_error else ((0, 255, 170) if self.is_finished else (180, 220, 255))
        prompt_surf = font_body.return_text("> " + self.status_text, status_color)
        surface.blit(prompt_surf, (body_box.left + 12, body_box.top + 14))

        # -------------------------------------------------------------
        # 5. NEON İLERLEME ÇUBUĞU (PROGRESS BAR)
        # -------------------------------------------------------------
        bar_w = self.w - 40
        bar_h = 24
        bar_x = self.x + 20
        bar_y = self.y + 138

        # Çubuk Haznesi (Track)
        track_rect = pygame.Rect(bar_x, bar_y, bar_w, bar_h)
        pygame.draw.rect(surface, (12, 16, 24), track_rect, border_radius=6)
        pygame.draw.rect(surface, (45, 60, 80), track_rect, width=1, border_radius=6)

        # İlerleme Dolgusu
        fill_ratio = max(0.0, min(1.0, self.progress / 100.0))
        fill_w = int(bar_w * fill_ratio)

        if fill_w > 0:
            fill_rect = pygame.Rect(bar_x, bar_y, fill_w, bar_h)
            pygame.draw.rect(surface, (0, 230, 255), fill_rect, border_radius=6)
            # Üst Cam Parlaması
            pygame.draw.line(surface, (200, 255, 255), (fill_rect.left, bar_y + 2), (fill_rect.right, bar_y + 2), 2)

        # Yüzde Göstergesi
        pct_text = f"{self.progress:.1f}%"
        pct_surf = font_body.return_text(pct_text, (255, 255, 255))
        surface.blit(pct_surf, pct_surf.get_rect(center=track_rect.center))

        # -------------------------------------------------------------
        # 6. ALT BİLGİ İPUCU (FOOTER)
        # -------------------------------------------------------------
        hint_str = "" # Şuanlık boş
        hint_surf = font_body.return_text(hint_str, (100, 120, 145))
        surface.blit(hint_surf, hint_surf.get_rect(center=(self.x + self.w // 2, self.y + 195)))


class SettingsScreen(MenuScreen):
    def __init__(self, game):
        super().__init__(game)

        self.langs = {
            "update_button_text": Lang(türkçe="Güncellemeleri Kontrol Et", english="Check Updates", arabic="التحقق من وجود تحديثات", sanskrit="Updates इति पश्यन्तु"),
            "checking_updates": Lang(türkçe="Güncellemeler kontrol ediliyor...", english="Checking updates...", arabic="جارٍ التحقق من وجود تحديثات...", sanskrit="अपडेट् कृते जाँचः क्रियते..."),
            "update_up_on_date": Lang(türkçe="Oyun zaten güncel.", english="The game is up-to-date.", arabic="اللعبة محدثة بالفعل.", sanskrit="क्रीडा पूर्वमेव अद्यतनम् अस्ति।"),
            "new_ver_found": Lang(türkçe="Yeni sürüm bulundu: ", english="New Version Found: ", arabic="تم العثور على إصدار جديد: ", sanskrit="नवीनं संस्करणं प्राप्तम् : "),
            "update_is_ready": Lang(
                türkçe="Güncelleme hazır. Oyun kapatıldığında uygulanacak.",
                english="Update is ready. Will be applied when you exit.",
                arabic="التحديث جاهز. سيتم تطبيقه عند إغلاق اللعبة.",
                sanskrit="अद्यतनं सज्जम् अस्ति। यदा क्रीडा निरुद्धा भविष्यति तदा प्रयोक्ष्यते।"
            ),
            "update_error": Lang(türkçe="Güncelleme hatası: Beklenmeyen bir hata oluştu.", english="Update Error: An unexpected error occurred.", arabic="خطأ في التحديث: حدث خطأ غير متوقع.", sanskrit="अद्यतनदोषः : अप्रत्याशितदोषः अभवत् ।")
        }

        self.update_fonts()

        self.console = Console(self.game.command_parser, self.font3, self.font3)

        self.quit_icon = pygame.image.load(os.path.join(BASE_DIR, r"images/quit_icon.png")).convert_alpha()
        self.quit_icon = pygame.transform.scale(
            self.quit_icon,
            (self.game.info.current_w // 30, self.game.info.current_w // 30)
        )
        self.quit_icon_rect = self.quit_icon.get_rect()
        self.old_fullscreen = self.game.settings.get("fullscreen")

        self.update_thread = None
        self.update_running = False

        # -------------------------------------------------------------
        # SÜRÜKLENEBİLİR OS GÜNCELLEME PENCERESİ
        # -------------------------------------------------------------
        init_win_x = (self.game.width - 560) // 2
        init_win_y = (self.game.height - 250) // 2
        self.update_window = UpdateWindow(init_win_x, init_win_y, w=560, h=230)

        # Güncelleme Butonunu Settings Menüsünün İçine Buton Olarak Entegre Ediyoruz
        self._inject_update_button_to_settings()

    def _inject_update_button_to_settings(self):
        """Settings sınıfı içindeki seçeneklere pencereyi açacak butonu ekler."""
        self.game.settings.options["check_updates"] = {
            "type": "button",
            "text": self.langs["update_button_text"],
            "callback": self.check_update,
            "accent_color": (0, 240, 255)
        }
        self.game.settings.names["check_updates"] = Lang(türkçe="Güncelleme", english="Update", arabic="تحديث", sanskrit="अद्यतनम्")
        self.game.settings.values["check_updates"] = ""
        self.game.settings.types["check_updates"] = str
        self.game.settings.create_elements()

    def draw(self, surface: pygame.Surface):
        surface.fill('black')

        # 1. Ayarlar Menüsü
        self.game.settings.draw(surface, self.font2, self.game.width, self.game.height)

        # 2. Çıkış Butonu
        surface.blit(self.quit_icon, (0, 0))

        # 3. Konsol
        self.console.draw(surface, self.game.height)

        # 4. SÜRÜKLENEBİLİR OS PENCERESİ (EN ÜST KATMAN)
        if self.update_window.is_open:
            self.update_window.draw(surface, self.font4, self.font3)

    def update(self, dt):
        self.game.settings.update(dt, self.game.width, self.game.height)
        if self.old_fullscreen != self.game.settings.get("fullscreen"):
            self.game.screen = pygame.display.set_mode(
                (self.game.width, self.game.height),
                pygame.FULLSCREEN if self.game.settings.get("fullscreen") else pygame.RESIZABLE
            )

        self.old_fullscreen = self.game.settings.get("fullscreen")

        if self.game.settings.get("music"):
            other_music = self.game.settings.get_element("other_music")
            if other_music:
                if os.path.exists(self.game.settings.get("other_music")):
                    other_music.showing_icons = [other_music.icons.get("path_found")]
                else:
                    other_music.showing_icons = [other_music.icons.get("path_not_found")]
            self.game.mixer.music.set_volume(self.game.settings.get("music_volume"))
        else:
            self.game.mixer.music.set_volume(0.0)
            other_music = self.game.settings.get_element("other_music")
            if other_music:
                other_music.showing_icons = []

        old_lang = Lang.USING_LANG
        Lang.USING_LANG = self.game.settings.get("language")
        new_lang = Lang.USING_LANG

        if old_lang != new_lang:
            self.update_fonts()
            classes.Slot.delete_slots()
            classes.Slot.create_slots(self.game.save_manager, self.font2)

        # Pencere sınırlarını güncelle
        self.update_window.update(self.game.width, self.game.height)

    def handle_event(self, event: pygame.event.Event):
        # 1. Eğer OS Penceresi Açıksa Önce Olayı O Tüketsin (Modal Davranış)
        if self.update_window.is_open:
            handled = self.update_window.handle_event(
                event,
                self.game.sfx_manager,
                self.game.settings.get("sfx_volume")
            )
            if handled:
                return

        # 2. Ayarlar Menüsü Olayları
        self.game.settings.handle_event(event)

        # 3. Sol Üst Çıkış İkonu
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.quit_icon_rect.collidepoint(event.pos):
                if self.game.settings.get("sfx"):
                    self.game.sfx_manager.play("click", self.game.settings.get("sfx_volume"))
                self.game.screen_manager.set_screen(self.game.screen_manager.get_last_screen())

        self.console.handle_event(event)

    def check_update(self):
        """Butona tıklandığında OS penceresini açıp arka plan iş parçacığını (thread) başlatır."""
        if self.update_running:
            self.update_window.is_open = True
            return

        self.update_running = True
        self.update_window.open(start_status=self.langs["checking_updates"]())

        self.update_thread = threading.Thread(target=self.update_worker, daemon=True)
        self.update_thread.start()

    def update_worker(self):
        try:
            update = check_for_update()

            if update is None:
                self.update_window.status_text = self.langs["update_up_on_date"]()
                self.update_window.is_loading = False
                self.update_window.is_finished = True
                self.update_window.progress = 100.0
                return

            self.update_window.status_text = f"{self.langs['new_ver_found']()} v{update['version']}"

            success, error = prepare_update(
                update["url"],
                update["signature_url"],
                self.update_progress_callback
            )

            if not success:
                self.update_window.status_text = error
                self.update_window.has_error = True
                self.update_window.is_loading = False
                return

            self.update_window.progress = 100.0
            self.update_window.status_text = self.langs["update_is_ready"]()
            self.update_window.is_loading = False
            self.update_window.is_finished = True

        except Exception as e:
            self.update_window.status_text = self.langs["update_error"]()
            self.update_window.has_error = True
            self.update_window.is_loading = False
            print("GÜNCELLEME HATASI:", repr(e))

        finally:
            self.update_running = False

    def update_progress_callback(self, progress):
        self.update_window.progress = progress

    def update_fonts(self):
        self.font2 = get_font(self.game.fonts, Lang.USING_LANG, 2, "userFont")
        self.dfont2 = get_font(self.game.fonts, Lang.USING_LANG, 2, "DynamicFont")
        self.font3 = get_font(self.game.fonts, Lang.USING_LANG, 3, "userFont")
        self.font4 = get_font(self.game.fonts, Lang.USING_LANG, 4, "userFont")

    def on_enter(self, transfer_datas: dict):
        self.update_fonts()

        self.game.mixer.music.load(os.path.join(BASE_DIR, r"musics/settings_music.ogg"))
        self.game.mixer.music.play(-1)

    def on_exit(self):
        self.game.mixer.music.stop()
        self.game.dump("last_music", os.path.join(BASE_DIR, r"musics/settings_music.ogg"))
        self.game.settings.save()