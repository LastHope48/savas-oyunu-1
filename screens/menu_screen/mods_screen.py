import os
import subprocess
import platform
import pygame

from .menu_screen import MenuScreen
from basedir import BASE_DIR
from ui import Bar, BarElement
from fonts import get_font
from lang_support import Lang
from screens.types import ScreenType
from calcs import scale
import colours


class ModsScreen(MenuScreen):
    def __init__(self, game):
        super().__init__(game)
        self.selected_mod_id = None
        self.scroll_y = 0.0
        self.target_scroll_y = 0.0

        # Yazı Tipleri
        self.font_title = get_font(self.game.fonts, Lang.USING_LANG, 1, "DynamicFont")
        self.font_body = get_font(self.game.fonts, Lang.USING_LANG, 3, "DynamicFont")
        self.font_desc = get_font(self.game.fonts, Lang.USING_LANG, 4, "DynamicFont")

        # Alt Geri Dönüş Barı
        bar_height = self.game.info.current_h // 10
        self.orig_quit_icon = pygame.image.load(os.path.join(BASE_DIR, "images/quit.png")).convert_alpha()
        self.quit_icon = pygame.transform.scale(self.orig_quit_icon, (self.game.info.current_w // 20, self.game.info.current_w // 20))

        self.bar = Bar(
            0,
            self.game.screen.get_height() - bar_height,
            self.game.screen.get_width(),
            bar_height,
            colours.GRAY,
            BarElement(self.quit_icon, on_click=self.on_back_click),
            separator=True
        )

        # "Klasörü Aç" Butonu
        self.btn_open_folder = pygame.Rect(0, 0, scale(220), scale(46))
        # "Aktif / Pasif" Butonu
        self.btn_toggle_mod = pygame.Rect(0, 0, scale(180), scale(46))

    def on_back_click(self):
        self.game.screen_manager.set_screen(ScreenType.SETTINGS)

    def open_mods_folder(self):
        """İşletim sistemine göre mod klasörünü dosya gezgininde açar."""
        folder = os.path.abspath(self.game.mod_manager.MODS_DIR)
        if platform.system() == "Windows":
            os.startfile(folder)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", folder])
        else:
            subprocess.Popen(["xdg-open", folder])

    def handle_event(self, event: pygame.event.Event):
        self.bar.handle_event(event)

        if event.type == pygame.MOUSEWHEEL:
            self.target_scroll_y -= event.y * 50
            self.target_scroll_y = max(0.0, self.target_scroll_y)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # 1. Klasörü Aç Butonu Tıklaması
            if self.btn_open_folder.collidepoint(event.pos):
                self.open_mods_folder()
                return

            # 2. Mod Aç/Kapa (Toggle) Butonu Tıklaması
            if self.selected_mod_id and self.btn_toggle_mod.collidepoint(event.pos):
                self.game.mod_manager.toggle_mod(self.selected_mod_id)
                return

            # 3. Sol Liste Kart Tıklamaları
            mods_list = list(self.game.mod_manager.mods.values())
            card_w = int(self.game.width * 0.38)
            card_h = scale(76)
            start_x = scale(40)
            start_y = scale(90) - self.scroll_y

            for i, mod in enumerate(mods_list):
                c_rect = pygame.Rect(start_x, start_y + i * (card_h + scale(12)), card_w, card_h)
                if c_rect.collidepoint(event.pos):
                    self.selected_mod_id = mod.id
                    break

    def update(self, dt: float):
        self.bar.update()
        self.scroll_y += (self.target_scroll_y - self.scroll_y) * min(1.0, 14.0 * dt)

        # İlk girişte mod seçilmemişse ilk modu seç
        if self.selected_mod_id is None and self.game.mod_manager.mods:
            self.selected_mod_id = list(self.game.mod_manager.mods.keys())[0]

    def draw(self, surface: pygame.Surface):
        surface.fill((12, 16, 24))
        sw, sh = self.game.width, self.game.height

        # ÜST BAŞLIK
        title_surf, _ = self.font_title.render("// YÜKLÜ MODLAR VE EKLENTİLER //", (0, 240, 255), surface.get_rect())
        surface.blit(title_surf, (scale(40), scale(26)))

        # -------------------------------------------------------------
        # SOL TARAF: SCROLLABLE MOD LİSTESİ (MINECRAFT STYLE)
        # -------------------------------------------------------------
        list_w = int(sw * 0.40)
        list_area = pygame.Rect(scale(30), scale(80), list_w, sh - scale(180))
        surface.set_clip(list_area)

        card_w = list_w - scale(20)
        card_h = scale(76)
        start_x = scale(40)
        start_y = scale(90) - self.scroll_y

        for i, mod in enumerate(self.game.mod_manager.mods.values()):
            c_rect = pygame.Rect(start_x, start_y + i * (card_h + scale(12)), card_w, card_h)

            # Seçili kart vurgusu
            is_selected = (self.selected_mod_id == mod.id)
            bg_col = (24, 34, 48) if is_selected else (16, 22, 32)
            border_col = (0, 240, 255) if is_selected else (45, 55, 70)

            pygame.draw.rect(surface, bg_col, c_rect, border_radius=8)
            pygame.draw.rect(surface, border_col, c_rect, width=2, border_radius=8)

            # Mod İkonu
            if mod.icon_surf:
                icon_scaled = pygame.transform.smoothscale(mod.icon_surf, (card_h - 16, card_h - 16))
                surface.blit(icon_scaled, (c_rect.left + 8, c_rect.top + 8))
            else:
                # Yedek ikon kutusu
                box_rect = pygame.Rect(c_rect.left + 8, c_rect.top + 8, card_h - 16, card_h - 16)
                pygame.draw.rect(surface, (30, 42, 58), box_rect, border_radius=6)
                pygame.draw.rect(surface, (0, 180, 210), box_rect, width=1, border_radius=6)

            # İsim & Sürüm
            text_x = c_rect.left + card_h + 6
            name_surf, _ = self.font_body.render(mod.name, (240, 250, 255), c_rect)
            surface.blit(name_surf, (text_x, c_rect.top + 10))

            # Durum rozeti (Aktif: Yeşil, Devre Dışı: Kırmızı)
            status_text = "AKTİF" if mod.enabled else "DEVRE DIŞI"
            status_col = (80, 240, 120) if mod.enabled else (240, 70, 70)
            st_surf, _ = self.font_desc.render(f"v{mod.version} | {status_text}", status_col, c_rect)
            surface.blit(st_surf, (text_x, c_rect.top + 40))

        surface.set_clip(None)

        # -------------------------------------------------------------
        # SAĞ TARAF: SEÇİLİ MOD DETAYLARI
        # -------------------------------------------------------------
        detail_x = list_w + scale(60)
        detail_w = sw - detail_x - scale(40)
        detail_rect = pygame.Rect(detail_x, scale(80), detail_w, sh - scale(180))

        pygame.draw.rect(surface, (16, 22, 32), detail_rect, border_radius=12)
        pygame.draw.rect(surface, (35, 48, 65), detail_rect, width=2, border_radius=12)

        sel_mod = self.game.mod_manager.mods.get(self.selected_mod_id)
        if sel_mod:
            # Büyük İkon
            if sel_mod.icon_surf:
                big_icon = pygame.transform.smoothscale(sel_mod.icon_surf, (scale(96), scale(96)))
                surface.blit(big_icon, (detail_x + scale(24), scale(104)))
            
            # Başlık, Yazar ve Sürüm
            title_pos_x = detail_x + (scale(136) if sel_mod.icon_surf else scale(24))
            m_name, _ = self.font_title.render(sel_mod.name, (255, 255, 255), detail_rect)
            surface.blit(m_name, (title_pos_x, scale(104)))

            m_author, _ = self.font_body.render(f"Geliştirici: {sel_mod.author}  |  Sürüm: {sel_mod.version}", (0, 210, 240), detail_rect)
            surface.blit(m_author, (title_pos_x, scale(144)))

            # Açıklama Metni Alanı
            desc_area = pygame.Rect(detail_x + scale(24), scale(215), detail_w - scale(48), scale(220))
            pygame.draw.line(surface, (30, 42, 60), (detail_x + scale(20), scale(200)), (detail_x + detail_w - scale(20), scale(200)), 2)

            renders, lh = self.font_desc.render(sel_mod.description, (180, 195, 215), desc_area, breaklines=True)
            dy = desc_area.top
            for r in renders:
                surface.blit(r, (desc_area.left, dy))
                dy += lh

            # Aktif/Pasif Yap Butonu
            self.btn_toggle_mod.bottomright = (detail_x + detail_w - scale(24), detail_rect.bottom - scale(24))
            btn_bg = (200, 50, 50) if sel_mod.enabled else (40, 180, 90)
            btn_txt = "DEVRE DIŞI BIRAK" if sel_mod.enabled else "AKTİF ET"

            pygame.draw.rect(surface, btn_bg, self.btn_toggle_mod, border_radius=8)
            t_surf, _ = self.font_body.render(btn_txt, (255, 255, 255), self.btn_toggle_mod)
            surface.blit(t_surf, t_surf.get_rect(center=self.btn_toggle_mod.center))

        # "Modlar Klasörünü Aç" Butonu (Sol altta)
        self.btn_open_folder.bottomleft = (scale(40), sh - scale(115))
        pygame.draw.rect(surface, (24, 34, 48), self.btn_open_folder, border_radius=8)
        pygame.draw.rect(surface, (0, 240, 255), self.btn_open_folder, width=2, border_radius=8)
        f_surf, _ = self.font_body.render("Klasörü Aç", (0, 240, 255), self.btn_open_folder)
        surface.blit(f_surf, f_surf.get_rect(center=self.btn_open_folder.center))

        self.bar.draw(surface)

    def on_enter(self, transfer_datas):
        self.game.mod_manager.scan_mods()
        self.bar.update(manual=True)
