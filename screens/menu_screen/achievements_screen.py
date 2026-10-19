import pygame
from .menu_screen import MenuScreen
import colours
import math
import os
from basedir import BASE_DIR
from ui import Bar, BarElement
from lang_support import Lang
from screens.types import ScreenType
import threading
from fonts import get_font


class AchievementsScreen(MenuScreen):
    def __init__(self, game):
        super().__init__(game)

        self.verifying = False
        self.offline = False
        self.illegal = False
        self.loading_time = 0
        self.achievements = []

        self.langs = {
            "achievement_counter": Lang(türkçe="Başarı", english="Achievement", sanskrit="सफलता", arabic="نجاح"),
            "datas_could_not_verified": Lang(türkçe="Achievement verileri doğrulanamadı.", english="Achievement datas could not be verified.", arabic="تعذّر التحقق من بيانات الإنجاز.", sanskrit="उपलब्धिदत्तांशस्य सत्यापनं कर्तुं न शक्यते स्म ।"),
            "verifying_achievements": Lang(türkçe="Başarımlar Doğrulanıyor", english="Verifying Achievements", sanskrit="उपलब्धीनां सत्यापनम्", arabic="يتم التحقق من الإنجازات."),
            "no_internet_connection": Lang(türkçe="İnternet bağlantısı gerekli.", english="No Internet Connection", arabic="يلزم الاتصال بالإنترنت", sanskrit="अन्तर्जालसम्पर्कः आवश्यकः")
        }

        self.achievement_images = {}
        self.achievement_card_cache = {}

        # Yazı Tipleri (DynamicFont)
        self.font3 = get_font(self.game.fonts, Lang.USING_LANG, 3, "DynamicFont")
        self.font4 = get_font(self.game.fonts, Lang.USING_LANG, 4, "DynamicFont")
        self.font5 = get_font(self.game.fonts, Lang.USING_LANG, 5, "DynamicFont")
        self.font7 = get_font(self.game.fonts, Lang.USING_LANG, 7, "DynamicFont")

        self.orig_quit_icon = pygame.image.load(os.path.join(BASE_DIR, r"images/quit.png")).convert_alpha()
        self.quit_icon = pygame.transform.scale(self.orig_quit_icon, (self.game.info.current_w // 20, self.game.info.current_w // 20))
        self.old_screen_size = (self.game.width, self.game.height)

        bar_height = self.game.info.current_h // 10

        self.bar = Bar(
            0,
            self.game.screen.get_height() - bar_height,
            self.game.screen.get_width(),
            bar_height,
            colours.GRAY,
            BarElement(self.quit_icon, on_click=self.quit_button_on_click),
            BarElement(pygame.Surface((1, 1)), update=self.create_achievement_surface, manual_update=True),
            separator=True
        )

        self.offline_bar = Bar(
            0,
            self.game.screen.get_height() - bar_height,
            self.game.screen.get_width(),
            bar_height,
            colours.GRAY,
            BarElement(self.quit_icon, on_click=self.quit_button_on_click),
            separator=True
        )

        # -------------------------------------------------------------
        # KAYDIRMA (SCROLL) VE SCROLLBAR DEĞİŞKENLERİ
        # -------------------------------------------------------------
        self.scroll_y = 0.0
        self.target_scroll_y = 0.0
        self.total_content_height = 0
        self.max_scroll_y = 0.0

        self.scrollbar_w = 12
        self.is_dragging_scrollbar = False
        self.drag_offset_y = 0.0

        self.bar.update()

    def quit_button_on_click(self):
        self.game.screen_manager.set_screen(ScreenType.MENU)

    # =================================================================
    # SCROLLBAR VE ALAN DİKDÖRTGENLERİ
    # =================================================================
    def get_view_rect(self) -> pygame.Rect:
        bar_height = self.game.screen.get_height() // 10
        return pygame.Rect(0, 0, self.game.screen.get_width(), self.game.screen.get_height() - bar_height)

    def get_scrollbar_rects(self) -> tuple[pygame.Rect, pygame.Rect]:
        view_rect = self.get_view_rect()
        track_x = self.game.screen.get_width() - self.scrollbar_w - 18
        track_y = 30
        track_h = max(20, view_rect.height - 60)
        track_rect = pygame.Rect(track_x, track_y, self.scrollbar_w, track_h)

        if self.max_scroll_y <= 0:
            return track_rect, pygame.Rect(track_x, track_y, self.scrollbar_w, track_h)

        visible_ratio = min(1.0, view_rect.height / max(1, self.total_content_height))
        thumb_h = max(35, int(track_h * visible_ratio))
        scroll_range = track_h - thumb_h
        thumb_y = track_y + int(scroll_range * (self.scroll_y / self.max_scroll_y))
        thumb_rect = pygame.Rect(track_x, thumb_y, self.scrollbar_w, thumb_h)

        return track_rect, thumb_rect

    # =================================================================
    # KART ÜRETİMİ VE ÖNBELLEK
    # =================================================================
    def create_achievement_card(self, achievement_id: str, width: int, height: int, is_unlocked: bool):
        metadata = self.game.achievements.achievements_metadata[achievement_id]
        card = pygame.Surface((width, height), pygame.SRCALPHA)
        card_rect = card.get_rect()

        # 1. Kart Gövdesi ve Çerçevesi
        if is_unlocked:
            pygame.draw.rect(card, (18, 24, 34), card_rect, border_radius=12)
            pygame.draw.rect(card, (0, 240, 255), card_rect, width=2, border_radius=12)
        else:
            pygame.draw.rect(card, (12, 14, 18), card_rect, border_radius=12)
            pygame.draw.rect(card, (45, 52, 65), card_rect, width=2, border_radius=12)

        # 2. Görsel ve Kilit Filtresi
        image_size = min(width // 2, height // 3)
        raw_image = pygame.transform.smoothscale(metadata["image"], (image_size, image_size))

        if not is_unlocked:
            dark_filter = pygame.Surface((image_size, image_size), pygame.SRCALPHA)
            dark_filter.fill((60, 65, 75, 200))
            raw_image.blit(dark_filter, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        image_rect = raw_image.get_rect(midtop=(width // 2, 22))
        card.blit(raw_image, image_rect)

        # Kilitli ise Kilit İkonu Çiz
        if not is_unlocked:
            lock_cx = image_rect.centerx
            lock_cy = image_rect.centery

            arc_rect = pygame.Rect(lock_cx - 11, lock_cy - 18, 22, 22)
            pygame.draw.arc(card, (170, 180, 195), arc_rect, 0, math.pi, 3)

            body_rect = pygame.Rect(0, 0, 32, 24)
            body_rect.center = (lock_cx, lock_cy + 2)
            pygame.draw.rect(card, (28, 34, 44), body_rect, border_radius=5)
            pygame.draw.rect(card, (100, 115, 135), body_rect, width=2, border_radius=5)

            pygame.draw.circle(card, (10, 14, 20), (lock_cx, lock_cy), 3)
            pygame.draw.line(card, (10, 14, 20), (lock_cx, lock_cy), (lock_cx, lock_cy + 6), 2)

        # 3. Başlık
        title = metadata["title"](self.game.settings.get("language"))
        title_area = pygame.Surface((width - 20, 60))
        title_color = (240, 248, 255) if is_unlocked else (100, 115, 130)

        title_render, _ = self.font3.render(title, title_color, title_area, gap=0, breaklines=False)
        title_rect = title_render.get_rect(centerx=width // 2, top=image_rect.bottom + 16)
        card.blit(title_render, title_rect)

        # 4. Açıklama
        description = metadata["description"](self.game.settings.get("language"))
        description_area = pygame.Surface((width - 30, height - title_rect.bottom - 30))
        desc_color = (180, 190, 205) if is_unlocked else (70, 80, 95)

        description_renders, line_height = self.font4.render(description, desc_color, description_area, gap=0, breaklines=True)
        y = title_rect.bottom + 10
        for rendered in description_renders:
            if y + rendered.get_height() > height - 10:
                break
            rendered_rect = rendered.get_rect(centerx=width // 2, top=y)
            card.blit(rendered, rendered_rect)
            y += line_height

        return card

    def get_achievement_card(self, achievement_id: str, width: int, height: int, is_unlocked: bool):
        language = self.game.settings.get("language")
        key = (achievement_id, width, height, language, is_unlocked)
        if key not in self.achievement_card_cache:
            self.achievement_card_cache[key] = self.create_achievement_card(achievement_id, width, height, is_unlocked)
        return self.achievement_card_cache[key]

    def draw_achievement(self, surface: pygame.Surface, achievement_id: str, rect: pygame.Rect):
        ach_data = self.game.achievements.achievements.get(achievement_id, {})
        is_unlocked = bool(ach_data.get("unlocked", False))
        card = self.get_achievement_card(achievement_id, rect.width, rect.height, is_unlocked)
        surface.blit(card, rect)

    # =================================================================
    # ÇİZİM VE GRID YERLEŞİMİ (WRAP & SCROLL)
    # =================================================================
    def draw(self, surface: pygame.Surface):
        surface.fill(colours.BLACK)

        if self.verifying or self.initing_online:
            self.draw_loading(surface)
            self.offline_bar.draw(surface)
            return

        if self.offline:
            message = self.langs["no_internet_connection"]()
            message_area = pygame.Surface((surface.get_width() - 100, surface.get_height() - 100))
            renders, line_height = self.font7.render(message, "white", message_area, gap=0, breaklines=True)
            y = (surface.get_height() - len(renders) * line_height) // 2
            for rendered in renders:
                rect = rendered.get_rect(centerx=surface.get_width() // 2, top=y)
                surface.blit(rendered, rect)
                y += line_height
            self.offline_bar.draw(surface)
            return

        if self.illegal:
            message_area = pygame.Surface((surface.get_width() - 100, surface.get_height() - 100))
            renders, line_height = self.font7.render(self.langs["datas_could_not_verified"](), "white", message_area, gap=0, breaklines=True)
            y = (surface.get_height() - len(renders) * line_height) // 2
            for rendered in renders:
                rect = rendered.get_rect(centerx=surface.get_width() // 2, top=y)
                surface.blit(rendered, rect)
                y += line_height
            self.offline_bar.draw(surface)
            return

        # -------------------------------------------------------------
        # BAŞARIM KARTLARININ ÇİZİMİ (GRID WRAP & CLIP)
        # -------------------------------------------------------------
        view_rect = self.get_view_rect()
        surface.set_clip(view_rect)

        card_width = 300
        card_height = 400
        gap_x = 28
        gap_y = 30
        start_x = 60
        start_y = 40

        # Satırın sığacağı maksimum sağ sınır (Scrollbar'a çarpmayacak pay)
        max_right = surface.get_width() - self.scrollbar_w - 45

        cur_x = start_x
        cur_y = start_y

        mouse_pos = pygame.mouse.get_pos()
        hovered_card_info = None

        for achievement_id in self.achievements:
            # Satırda yer bittiyse bir alt satıra geç
            if cur_x + card_width > max_right and cur_x > start_x:
                cur_x = start_x
                cur_y += card_height + gap_y

            # Scroll çıkarılmış ekrandaki gerçek çizim dikdörtgeni
            screen_rect = pygame.Rect(cur_x, cur_y - int(self.scroll_y), card_width, card_height)

            # Sadece ekranda görünen kartları çiz (Performans)
            if screen_rect.bottom >= view_rect.top and screen_rect.top <= view_rect.bottom:
                self.draw_achievement(surface, achievement_id, screen_rect)

                # Fareyle üzerine gelindi mi?
                if view_rect.collidepoint(mouse_pos) and screen_rect.collidepoint(mouse_pos):
                    ach_data = self.game.achievements.achievements.get(achievement_id, {})
                    meta_data = self.game.achievements.achievements_metadata.get(achievement_id, {})
                    is_unlocked = bool(ach_data.get("unlocked", False))
                    unlock_tutorial = meta_data.get("unlock_tutorial", "No Tutorial")
                    hovered_card_info = (achievement_id, screen_rect, is_unlocked, unlock_tutorial)

            cur_x += card_width + gap_x

        # Toplam dikey boyutu ve maksimum kaydırma payını güncelle
        self.total_content_height = cur_y + card_height + gap_y + 30
        self.max_scroll_y = max(0.0, float(self.total_content_height - view_rect.height))

        surface.set_clip(None)

        # -------------------------------------------------------------
        # HOVER AÇIKLAMA BALONU (CLIP OLMADAN EN ÜSTE ÇİZİLİR)
        # -------------------------------------------------------------
        if hovered_card_info:
            _, hov_rect, hov_unlocked, hov_tutorial = hovered_card_info
            if not hov_unlocked:
                tutorial_rect = pygame.Rect(0, 0, 240, 110)
                tutorial_rect.center = hov_rect.center
                # Ekrandan taşmaması için sınırla
                tutorial_rect.clamp_ip(view_rect)

                pygame.draw.rect(surface, (20, 26, 36), tutorial_rect, border_radius=8)
                pygame.draw.rect(surface, (0, 240, 255), tutorial_rect, width=2, border_radius=8)

                tut_str = hov_tutorial(self.game.settings.get("language")) if callable(hov_tutorial) else str(hov_tutorial)
                tut_area = pygame.Surface((tutorial_rect.width - 20, tutorial_rect.height - 20))
                tut_renders, tut_lh = self.font5.render(tut_str, (240, 245, 255), tut_area, breaklines=True)

                total_text_h = len(tut_renders) * tut_lh
                y_text = tutorial_rect.top + (tutorial_rect.height - total_text_h) // 2
                for r in tut_renders:
                    r_rect = r.get_rect(centerx=tutorial_rect.centerx, top=y_text)
                    surface.blit(r, r_rect)
                    y_text += tut_lh

        # -------------------------------------------------------------
        # NEON DİKEY SCROLLBAR
        # -------------------------------------------------------------
        if self.max_scroll_y > 0:
            v_track, v_thumb = self.get_scrollbar_rects()
            pygame.draw.rect(surface, (14, 18, 26), v_track, border_radius=6)
            pygame.draw.rect(surface, (30, 40, 55), v_track, width=1, border_radius=6)

            thumb_color = (130, 250, 255) if self.is_dragging_scrollbar else (0, 240, 255)
            pygame.draw.rect(surface, thumb_color, v_thumb, border_radius=6)
            pygame.draw.rect(surface, (220, 255, 255), v_thumb.inflate(-4, -4), border_radius=4)

        # Alt Çıkış Barı
        self.bar.draw(surface)

    # =================================================================
    # GÜNCELLEME VE LERP SCROLL
    # =================================================================
    def update(self, dt):
        self.initing_online = self.game.initing_online_data
        self.bar.update()
        self.offline_bar.update()

        if self.verifying or self.initing_online:
            self.loading_time += dt

        # Yumuşak kaydırma sönümlemesi (Lerp)
        if not self.is_dragging_scrollbar:
            self.target_scroll_y = max(0.0, min(self.max_scroll_y, self.target_scroll_y))
            self.scroll_y += (self.target_scroll_y - self.scroll_y) * min(1.0, 14.0 * dt)
            self.scroll_y = max(0.0, min(self.max_scroll_y, self.scroll_y))

        bar_height = self.game.screen.get_height() // 10
        self.bar.rect.y = self.game.screen.get_height() - bar_height
        self.bar.rect.height = bar_height
        self.bar.rect.width = self.game.screen.get_width()

        self.offline_bar.rect.y = self.game.screen.get_height() - bar_height
        self.offline_bar.rect.height = bar_height
        self.offline_bar.rect.width = self.game.screen.get_width()

        if (self.game.width, self.game.height) != self.old_screen_size:
            self.quit_icon = pygame.transform.scale(
                self.orig_quit_icon,
                (self.game.width // 12, self.game.width // 12)
            )
            self.bar.elements[0].surface = self.quit_icon
            self.offline_bar.elements[0].surface = self.quit_icon

        self.old_screen_size = (self.game.width, self.game.height)

    # =================================================================
    # OLAY YÖNETİMİ (TEKERLEK & FAREYLE SÜRÜKLEME)
    # =================================================================
    def handle_event(self, event: pygame.event.Event):
        if self.verifying or self.illegal or self.offline or self.initing_online:
            self.offline_bar.handle_event(event)
            return

        # 1. Fare Tekerleği ile Kaydırma
        if event.type == pygame.MOUSEWHEEL:
            self.target_scroll_y -= event.y * 75
            self.target_scroll_y = max(0.0, min(self.max_scroll_y, self.target_scroll_y))
            return

        v_track, v_thumb = self.get_scrollbar_rects()

        # 2. Fare Tıklaması (Scrollbar Yakalama veya Kanala Zıplama)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.max_scroll_y > 0 and v_thumb.collidepoint(event.pos):
                self.is_dragging_scrollbar = True
                self.drag_offset_y = event.pos[1] - v_thumb.y
                return
            elif self.max_scroll_y > 0 and v_track.collidepoint(event.pos):
                scroll_range = v_track.height - v_thumb.height
                if scroll_range > 0:
                    clicked_pos = event.pos[1] - v_track.top - (v_thumb.height / 2)
                    ratio = max(0.0, min(1.0, clicked_pos / scroll_range))
                    self.target_scroll_y = ratio * self.max_scroll_y
                    self.scroll_y = self.target_scroll_y
                return

        # 3. Fare Bırakıldığında Sürüklemeyi Bitir
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.is_dragging_scrollbar = False

        # 4. Sürükleme Hareketi
        elif event.type == pygame.MOUSEMOTION:
            if self.is_dragging_scrollbar and self.max_scroll_y > 0:
                scroll_range = v_track.height - v_thumb.height
                if scroll_range > 0:
                    rel_pos = event.pos[1] - v_track.top - self.drag_offset_y
                    ratio = max(0.0, min(1.0, rel_pos / scroll_range))
                    self.target_scroll_y = ratio * self.max_scroll_y
                    self.scroll_y = self.target_scroll_y
                return

        # Alt Bar Olayları
        self.bar.handle_event(event)

    def start_verify(self):
        if self.verifying:
            return
        self.verifying = True
        self.offline = False
        self.illegal = False
        self.loading_time = 0
        threading.Thread(target=self.verify_achievements, daemon=True).start()

    def update_achievements(self):
        if self.offline or self.illegal:
            return
        self.achievements = []
        for achievement_id in self.game.achievements.achievements_metadata.keys():
            if achievement_id in self.game.achievements.achievements:
                self.achievements.append(achievement_id)

    def draw_loading(self, surface):
        dots = "." * (int(self.loading_time * 2) % 4)
        message = f"{self.langs['verifying_achievements']()}{dots}"
        area = pygame.Surface((surface.get_width() - 100, surface.get_height() - 100))
        renders, line_height = self.font7.render(message, "white", area, gap=0, breaklines=True)
        y = (surface.get_height() - len(renders) * line_height) // 2
        for rendered in renders:
            rect = rendered.get_rect(centerx=surface.get_width() // 2, top=y)
            surface.blit(rendered, rect)
            y += line_height

    def create_achievement_surface(self):
        if self.game.achievements is None:
            return
        unlocked = len(list(filter(lambda x: x["unlocked"], self.game.achievements.achievements.values())))
        total = len(self.game.achievements.achievements.keys())
        return self.font5.render(
            f"{self.langs['achievement_counter'](self.game.settings.get('language'))} {unlocked}/{total}",
            colours.BLACK,
            pygame.Surface((self.bar._per_width_for_element(), self.bar.rect.h))
        )[0]

    def verify_achievements(self):
        for achievement_id, achievement in self.game.achievements.achievements.items():
            if not achievement.get("unlocked"):
                continue
            result = self.game.achievements.verify(achievement_id)
            if result is None:
                self.offline = True
                self.verifying = False
                return
            if result is False:
                self.illegal = True
                self.verifying = False
                return
        self.verifying = False

    def on_enter(self, transfer_datas):
        self.font3 = get_font(self.game.fonts, Lang.USING_LANG, 3, "DynamicFont")
        self.font4 = get_font(self.game.fonts, Lang.USING_LANG, 4, "DynamicFont")
        self.font5 = get_font(self.game.fonts, Lang.USING_LANG, 5, "DynamicFont")
        self.font7 = get_font(self.game.fonts, Lang.USING_LANG, 7, "DynamicFont")

        self.illegal = self.game.illegal
        self.offline = self.game.offline
        self.initing_online = self.game.initing_online_data

        if self.initing_online or self.illegal or self.offline:
            return

        self.achievement_counter = self.create_achievement_surface()

        if self.game.dump("last_music") != os.path.join(BASE_DIR, r"musics/menu_theme.ogg"):
            self.game.mixer.music.load(os.path.join(BASE_DIR, r"musics/menu_theme.ogg"))
            self.game.mixer.music.play(-1)
            self.game.dump("last_music", os.path.join(BASE_DIR, r"musics/menu_theme.ogg"))

        self.start_verify()
        self.update_achievements()
        self.bar.update(manual=True)
        self.offline_bar.update(manual=True)