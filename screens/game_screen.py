import os
import random
import threading
import pygame

from .screen import Screen
from levels import level_sword_map, level_item_map, levels, bronze_gun
import typehint_game
import classes
from fonts import get_font
import colours
from classes import Button, defaults as game_data_defaults, MaterialFlags
from calcs import calculate_size, scale
from lang_support import Lang
from scene import Scene, SceneDialogue
from basedir import BASE_DIR
from helper_funcs import create_player_dialogue_portrait
from typing import Literal
from ready_music import Music
from copy import deepcopy
from flags import DefaultWorld, NoItem, NoSword

from gamedata import GameData
from .types import ScreenType
from cooldown import Cooldown


GAME_MODES = Literal["campaign", "freeplay"]


class GameScreen(Screen):
    def __init__(self, game):
        super().__init__(game)
        self.game: typehint_game.Game

        # Sarsıntı ve Oyun İçi Efekt Katmanı (Render Surface)
        self.render_surf = pygame.Surface((self.game.width, self.game.height))
        self._was_deflecting = False

        self.font1 = get_font(
            self.game.fonts,
            Lang.USING_LANG,
            1,
            "userFont"
        )
        self.font2 = get_font(
            self.game.fonts,
            Lang.USING_LANG,
            2,
            "userFont"
        )
        self.font3 = get_font(
            self.game.fonts,
            Lang.USING_LANG,
            3,
            "userFont"
        )
        self.dfont1 = get_font(
            self.game.fonts,
            Lang.USING_LANG,
            1,
            "DynamicFont"
        )

        self.langs = {
            "new_game_button": Lang(türkçe="Yeni Oyun", english="New Game", arabic="لعبة جديدة", sanskrit="नूतनः क्रीडा"),
            "continue_button": Lang(türkçe="Devam Et", english="Continue", arabic="يكمل", sanskrit="अनुवर्तते"),
            "load_button": Lang(türkçe="Yükle", english="Load", sanskrit="अपलोड् कुर्वन्तु", arabic="رفع"),
            "save_button": Lang(türkçe="Kaydet", english="Save", arabic="يحفظ", sanskrit="रक्ष्"),
            "settings_button": Lang(türkçe="Ayarlar", english="Settings", sanskrit="सेटिंग्स्", arabic="إعدادات"),
            "quit_button": Lang(türkçe="Menüye Dön", english="Return Menu", arabic="مخرج", sanskrit="निर्गम")
        }

        self.levels: list[list[classes.Enemy]] = levels

        self.dash_cooldown = Cooldown(0.13)
        self.cd_gun_choosing = Cooldown(0.4, 0.35)

        self.gun_choosing = False
        self.esc_screen = False

        self.quick_gun_swap_index = 0
        self.saved_last = False
        self.save_last_cd = Cooldown(20)
        self.typing_sound = self.game.mixer.Sound(os.path.join(BASE_DIR, r"sounds/heavy_speak.wav"))

        self.new_game_button = Button(
            0, 0, 300, 80,
            "Yeni Oyun",
            self.dfont1,
            colours.YELLOW,
            colours.WHITE,
            [ScreenType.MENU, ScreenType.GAME],
            colours.darker(colours.YELLOW, 20),
            colours.darker(colours.YELLOW, 50),
            design="bevel",
            border_radius=0
        )

        self.continue_button = Button(
            0, 0, 300, 80,
            "Devam Et",
            self.dfont1,
            colours.YELLOW,
            colours.WHITE,
            [ScreenType.MENU, ScreenType.GAME],
            colours.darker(colours.YELLOW, 20),
            colours.darker(colours.YELLOW, 50),
            design="bevel",
            border_radius=0
        )

        self.load_button = Button(
            0, 0, 300, 80,
            "Yükle",
            self.dfont1,
            colours.YELLOW,
            colours.WHITE,
            [ScreenType.MENU, ScreenType.GAME],
            colours.darker(colours.YELLOW, 20),
            colours.darker(colours.YELLOW, 50),
            design="bevel",
            border_radius=0
        )

        self.save_button = Button(
            0, 0, 300, 80,
            "Kaydet",
            self.dfont1,
            colours.YELLOW,
            colours.WHITE,
            [ScreenType.MENU, ScreenType.GAME],
            colours.darker(colours.YELLOW, 20),
            colours.darker(colours.YELLOW, 50),
            design="bevel",
            border_radius=0
        )

        self.settings_button = Button(
            0, 0, 300, 80,
            "Ayarlar",
            self.dfont1,
            colours.YELLOW,
            colours.WHITE,
            [ScreenType.MENU, ScreenType.GAME],
            colours.darker(colours.YELLOW, 20),
            colours.darker(colours.YELLOW, 50),
            design="bevel",
            border_radius=0
        )

        self.quit_button = Button(
            0, 0, 300, 80,
            "Menüye Dön",
            self.dfont1,
            colours.RED,
            colours.WHITE,
            [ScreenType.MENU, ScreenType.GAME],
            colours.darker(colours.RED, 20),
            colours.darker(colours.RED, 50),
            design="bevel",
            border_radius=0
        )

        self.scene = None
        self.achievement_unlock_cd = Cooldown(3)
        self.max_combo = 0

        # Oyun Modu ve Free Play Dalga Değişkenleri
        self.mode: GAME_MODES = "campaign"
        self.freeplay_wave = 1
        self.wave_intermission_cd = Cooldown(1.2)
        self._special_events_injected = False

    def spawn_freeplay_wave(self, wave: int):
        """Free Play modu için dinamik düşman dalgası üretir."""
        self.game.game_data.enemy_data = {}
        enemy_count = min(14, 3 + wave * 2)

        pool = [
            classes.Enemy.prepared_old,
            classes.Enemy.default
        ]

        item_pool = [
            classes.Item(
                "Can İksiri",
                (255, 0, 0),
                [classes.Effect("hp", 50, 0, flags=(classes.Item.APPENDER,))],
                classes.Item.TUP_IKSIR
            ),
            classes.Item(
                "Ölüm İksiri",
                (0, 0, 255),
                [classes.Effect("hp", 25, 0, flags=(classes.Item.REDUCER,))],
                classes.Item.YUVARLAK_IKSIR,
                pickable=True
            )
        ]

        if wave >= 2:
            pool.append(classes.Enemy.default)
        
        if wave >= 3:
            pool.append(classes.Enemy.prepared_old)
            pool.append(classes.Enemy.prepared_old)
            pool.append(classes.Enemy.prepared_old)
            pool.append(classes.Enemy.default)
            item_pool.append(
                classes.Item(
                    "Can İksiri",
                    (255, 0, 0),
                    [classes.Effect("hp", 50, 0, flags=(classes.Item.APPENDER))],
                    classes.Item.TUP_IKSIR
                )
            )
        
        if wave >= 4:
            pool.append(classes.Enemy.prepared_police)
            for _ in range(6):
                pool.append(classes.Enemy.prepared_old)

            item_pool.append(
                classes.Item(
                    "Ölüm İksiri",
                    (0, 0, 255),
                    [classes.Effect("hp", 25, 0, flags=(classes.Item.REDUCER))],
                    classes.Item.YUVARLAK_IKSIR,
                    pickable=True
                )
            )
        
        if wave >= 6:
            pool.append(classes.Enemy.morty)
            pool.append(classes.Enemy.miguel)
            pool.append(classes.Enemy.skzoo)

        if wave >= 10:
            pool.append(classes.Enemy.dinosaur)

        if wave % 5 == 0:
            self.game.game_data.player.max_hp *= 2

        if wave == 5:
            self.game.game_data.player.ability_healing = True

        for _ in range(enemy_count):
            factory = random.choice(pool)

            if callable(factory):
                enemy: classes.Enemy = factory()
                if not isinstance(enemy, classes.Enemy):
                    self.game.logger.warning(
                        f"{_ + 1}. factory is not a function returns Enemy object. Skipping..."
                    )
                    continue

            elif isinstance(factory, classes.Enemy):
                enemy: classes.Enemy = factory.copy()

            else:
                self.game.logger.warning(
                    f"{_ + 1}. factory is not a function or Enemy object. Skipping..."
                )
                continue
            
            enemy.reset(self.game.game_data.world)
            enemy.set_pos(self.game.game_data.world, self.game.info)
            self.game.game_data.enemy_data[enemy.id] = enemy

        for _ in range(len(item_pool) // 2):
            item_selected = deepcopy(random.choice(item_pool))
            item_selected.set_pos(self.game.game_data.world)
            self.game.game_data.world.items.append(item_selected)

        self.game.game_data.player.hp = min(
            self.game.game_data.player.max_hp,
            self.game.game_data.player.hp + 45
        )

    def check_freeplay_wave(self, dt):
        all_dead = all(not enemy.living for enemy in self.game.game_data.enemy_data.values())
        if all_dead:
            self.wave_intermission_cd.reduce(dt)
            if self.wave_intermission_cd.check():
                self.freeplay_wave += 1
                self.spawn_freeplay_wave(self.freeplay_wave)
                self.wave_intermission_cd.refresh()

    def draw(self, surface: pygame.Surface):
        # 1. Ekran boyutuna göre render_surf'ü kontrol et
        if not hasattr(self, "render_surf") or self.render_surf.get_size() != surface.get_size():
            self.render_surf = pygame.Surface(surface.get_size())

        target_surf = self.render_surf
        target_surf.fill((0, 0, 0))

        # -------------------------------------------------------------
        # 2. DÜNYA VE VARLIKLAR (SARSINTIYA DAHİL OLAN KATMAN)
        # -------------------------------------------------------------
        self.game.game_data.world.draw(target_surf)
        self.game.game_data.world.draw_items(target_surf, self.font3, self.game.game_data.player)

        if type(self.game.game_data.player.using_gun) == classes.Gun:
            self.game.game_data.player.using_gun.draw(
                target_surf,
                self.game.game_data.player.x + 30,
                self.game.game_data.player.y + 10
            )
        elif type(self.game.game_data.player.using_gun) == classes.Charm:
            self.game.game_data.player.using_gun.draw(
                target_surf,
                self.game.game_data.player.x + 30,
                self.game.game_data.player.y + 10
            )

        for enemy in self.game.game_data.enemy_data.values():
            enemy.draw_arrows(target_surf)
            enemy.draw_bombs(target_surf)
            enemy.draw_sgrounds(target_surf)

        classes.Enemy.draw(
            target_surf,
            self.font3,
            list(self.game.game_data.enemy_data.values()),
            self.font1
        )

        classes.Boss.draw(
            target_surf,
            self.font3,
            list(self.game.game_data.enemy_data.values()),
            self.dfont1
        )

        # Hit-Flash Efekti (Darbe anında düşmanı saf beyaz parlat)
        for enemy in self.game.game_data.enemy_data.values():
            if getattr(enemy, "flash_timer", 0) > 0 and hasattr(enemy, "rect"):
                flash_overlay = pygame.Surface(enemy.rect.size, pygame.SRCALPHA)
                flash_overlay.fill((255, 255, 255, 200))
                target_surf.blit(flash_overlay, enemy.rect, special_flags=pygame.BLEND_RGBA_ADD)

        self.game.game_data.player.draw(target_surf)
        self.game.game_data.player.draw_dash(target_surf)
        self.game.game_data.player.draw_teleport(target_surf)

        for enemy in self.game.game_data.enemy_data.values():
            enemy.draw_sneezes(target_surf)
            enemy.draw_scr_lazers(target_surf)

        # Neon kıvılcımları dünya yüzeyine çiz
        self.game.juice.draw_sparks(target_surf)

        # -------------------------------------------------------------
        # 3. ANA EKRANA BLIT (ORGANİK SARSINTI UYGULANIR)
        # -------------------------------------------------------------
        shake_x, shake_y = self.game.juice.get_shake_offset()
        surface.blit(target_surf, (shake_x, shake_y))

        # -------------------------------------------------------------
        # 4. HUD VE SABİT ARAYÜZ (SARSINTIDAN ETKİLENMEZ)
        # -------------------------------------------------------------
        self.game.game_data.player.draw_statistics(surface, self.font2, self.game.info, self.game.clock)

        if self.mode == "freeplay":
            alive_count = sum(1 for e in self.game.game_data.enemy_data.values() if e.living)
            wave_text = f"FREE PLAY  |  WAVE {self.freeplay_wave}  |  KALAN DUSMAN: {alive_count}"
            self.font1.draw_text(
                wave_text,
                (self.game.width // 2, 35),
                surface,
                (0, 0, 0),
                hiza="center"
            )

        if self.gun_choosing:
            self.game.game_data.player.draw_available_guns(surface)

        elif self.esc_screen:
            self.new_game_button.draw(surface)
            self.continue_button.draw(surface)
            self.load_button.draw(surface)
            self.save_button.draw(surface)
            self.settings_button.draw(surface)
            self.quit_button.draw(surface)

        if self.scene is not None and self.scene.active:
            self.scene.draw(surface)

    def update(self, dt):
        self.achievement_unlock_cd.reduce(dt)

        if self.scene is not None and self.scene.active:
            self.game.juice.trauma = 0.0
            self.scene.update(dt, self.game.settings.get("sfx_volume"), self.game.settings.get("sfx"))
            return

        # -------------------------------------------------------------
        # GAME JUICE & HITSTOP KONTROLÜ
        # -------------------------------------------------------------
        is_frozen = self.game.juice.update(dt)

        # Beyaz flaş sayaçlarını azalt
        for enemy in self.game.game_data.enemy_data.values():
            if getattr(enemy, "flash_timer", 0) > 0:
                enemy.flash_timer -= dt

        # Mikro donma aktifken fizik ve hareket güncellemelerini atla
        if is_frozen:
            return

        if not self.esc_screen and not self.gun_choosing:
            self.dash_cooldown.reduce(dt)
        self.cd_gun_choosing.reduce(dt)
        self.save_last_cd.reduce(dt)

        if self.save_last_cd.check():
            self.saved_last = False

        keys = pygame.key.get_pressed()

        if not self.gun_choosing and not self.esc_screen:
            # Durum takibi (Hasar ve darbe tespiti için)
            old_player_hp = self.game.game_data.player.hp
            enemy_hps = {enemy.id: enemy.hp for enemy in self.game.game_data.enemy_data.values()}
            old_deflect_count = len(getattr(self.game.game_data.player, "deflect_bullets", []))

            if keys[pygame.K_LSHIFT] and self.dash_cooldown.check() and not self.game.game_data.player.drawing and isinstance(self.game.game_data.player.using_gun, classes.Sword):
                self.game.game_data.player.dash()
                self.dash_cooldown.refresh()

            elif keys[pygame.K_LSHIFT] and type(self.game.game_data.player.using_gun) == classes.Gun:
                self.game.game_data.player.using_gun.dash_attack(self.game.game_data.player)

            varliklar = list(self.game.game_data.enemy_data.values())
            varliklar.append(self.game.game_data.player)

            for item in self.game.game_data.world.items:
                item: classes.Item
                item.update(varliklar)

            for enemy in self.game.game_data.enemy_data.values():
                enemy.damage(self.game.game_data.player, dt)

            self.game.game_data.world.update(self.game.game_data.enemy_data.values())

            if type(self.game.game_data.player.using_gun) == classes.Gun:
                if pygame.mouse.get_pressed()[0]:
                    self.game.game_data.player.using_gun.fire()

            if not self.gun_choosing:
                self.game.game_data.player.update(
                    pygame.mouse.get_pos(),
                    self.game.game_data.world,
                    dt,
                    self.game.width,
                    self.game.height,
                    self.game.game_data.enemy_data.values()
                )

                self.game.game_data.player.heal(dt)

                if type(self.game.game_data.player.using_gun) == classes.Gun:
                    self.game.game_data.player.using_gun.update(
                        self.game.game_data.world,
                        dt,
                        self.game.game_data.enemy_data.values(),
                        self.game.game_data.player,
                        self.game.dump("gun_combo")
                    )

                if type(self.game.game_data.player.using_gun) == classes.Charm:
                    self.game.game_data.player.using_gun.update(self.game.game_data.player.angle, dt)
                    self.game.game_data.player.using_gun.use_active(self.game.game_data.player, dt)

                if isinstance(self.game.game_data.player.using_gun, classes.Sword):
                    self.game.game_data.player.deflect(self.game.game_data.enemy_data.values(), dt)

                pending_enemies = []

                for enemy in self.game.game_data.enemy_data.values():
                    enemy: classes.Enemy
                    enemy.update(
                        self.game.game_data.player,
                        self.game.game_data.world,
                        dt,
                        self.game.game_data.enemy_data.values(),
                        self.game.cheated
                    )
                    enemy.update_arrows(self.game.game_data.player, dt)
                    enemy.summon(
                        dt,
                        self.game.game_data.enemy_data,
                        self.game.game_data.world,
                        pending_enemies
                    )
                    enemy.update_bombs(self.game.game_data.player, dt)
                    enemy.update_cat_jump(self.game.game_data.player, dt)
                    enemy.update_scr_lazers(self.game.game_data.player, dt)
                    enemy.update_sneezes(self.game.game_data.player, dt)

                for enemy in pending_enemies:
                    self.game.game_data.enemy_data[enemy.id] = enemy

                for item in self.game.game_data.world.items:
                    item.update_pos(dt)
                    if item.rect.colliderect(self.game.game_data.player.image_rect):
                        item.use(self.game.game_data.player)

                try:
                    for enemy in self.game.game_data.enemy_data.values():
                        enemy.use_arrow(dt)
                        enemy.use_bombing(dt, self.game.game_data.player)
                        enemy.use_split_ground(dt, self.game.game_data.player)
                        enemy.use_cat_jump(dt, self.game.game_data.player)
                        enemy.use_scr_lazer_beam(dt)
                        enemy.use_sneeze()
                except KeyError:
                    pass

            self.game.game_data.player.damage(
                self.game.game_data.enemy_data.values(),
                dt,
                self.gun_choosing
            )

            # ---------------------------------------------------------
            # DARBE & VURUŞ TETİKLEYİCİLERİ (GAME JUICE FEEDBACK)
            # ---------------------------------------------------------
            # 1. Deflect (Mermi/Ok Karşılama)
            new_deflect_count = len(getattr(self.game.game_data.player, "deflect_bullets", []))
            curr_deflect_anim = getattr(self.game.game_data.player, "is_deflecting_anim", False)
            if new_deflect_count > old_deflect_count or (curr_deflect_anim and not self._was_deflecting):
                self.game.juice.hitstop(0.06)
                self.game.juice.add_trauma(0.5)
                self.game.juice.emit_sparks(
                    self.game.game_data.player.x,
                    self.game.game_data.player.y,
                    count=14,
                    color=(0, 240, 255)
                )
            self._was_deflecting = curr_deflect_anim

            # 2. Oyuncunun Hasar Alması
            if self.game.game_data.player.hp < old_player_hp:
                self.game.juice.hitstop(0.04)
                self.game.juice.add_trauma(0.4)
                self.game.juice.emit_sparks(
                    self.game.game_data.player.x,
                    self.game.game_data.player.y,
                    count=8,
                    color=(255, 60, 60)
                )

            # 3. Düşmanların Hasar Alması ve Ölümü
            for enemy in self.game.game_data.enemy_data.values():
                prev_hp = enemy_hps.get(enemy.id, enemy.hp)
                if enemy.hp < prev_hp:
                    enemy.flash_timer = 0.08
                    ex = getattr(enemy, "x", enemy.rect.centerx if hasattr(enemy, "rect") else self.game.width // 2)
                    ey = getattr(enemy, "y", enemy.rect.centery if hasattr(enemy, "rect") else self.game.height // 2)

                    if not enemy.living or enemy.hp <= 0:
                        # Öldürücü vuruş
                        if type(self.game.game_data.player.using_gun) != classes.Gun:
                            self.game.juice.hitstop(0.07)
                        self.game.juice.add_trauma(0.45)
                        self.game.juice.emit_sparks(ex, ey, count=18, color=(255, 50, 50))
                    else:
                        # Normal darbe
                        if type(self.game.game_data.player.using_gun) != classes.Gun:
                            self.game.juice.hitstop(0.04)
                        self.game.juice.add_trauma(0.25)
                        spark_color = (0, 240, 255) if isinstance(self.game.game_data.player.using_gun, classes.Sword) else (255, 200, 50)
                        self.game.juice.emit_sparks(ex, ey, count=10, color=spark_color)

            # Maksimum Kombo Takibi
            if getattr(self.game.game_data.player, "combo_meter", None):
                current_combo = getattr(self.game.game_data.player.combo_meter, "combo", 0)
                if current_combo > self.max_combo:
                    self.max_combo = current_combo

            if self.game.achievements is not None:
                if self.achievement_unlock_cd.check():
                    if not self.game.achievements.achievements.get("1_000_000_kill").get("unlock"):
                        if self.game.val_manager("kill") >= 1_000_000:
                            threading.Thread(
                                target=self.game.achievements.unlock,
                                args=("1_000_000_kill",),
                                daemon=True
                            ).start()
                            self.achievement_unlock_cd.refresh()

                    if not self.game.achievements.achievements.get("10_000_kill").get("unlock"):
                        if self.game.val_manager("kill") >= 10_000:
                            threading.Thread(
                                target=self.game.achievements.unlock,
                                args=("10_000_kill",),
                                daemon=True
                            ).start()
                            self.achievement_unlock_cd.refresh()

                    if not self.game.achievements.achievements.get("500_kill").get("unlock"):
                        if self.game.val_manager("kill") >= 500:
                            threading.Thread(
                                target=self.game.achievements.unlock,
                                args=("500_kill",),
                                daemon=True
                            ).start()
                            self.achievement_unlock_cd.refresh()

            if self.game.game_data.player.hp <= 0:
                self.game.screen_manager.set_screen(ScreenType.LOSE)
                return

            if self.mode == "freeplay":
                self.check_freeplay_wave(dt)
            else:
                self.check_level()

        if self.gun_choosing:
            self.game.game_data.player.update_available_guns(dt)

        if self.esc_screen:
            width = self.game.width
            height = self.game.height

            self.new_game_button.set_center(width * 0.5, height * 0.27)
            self.new_game_button.width = calculate_size(300, 800, width)
            self.new_game_button.height = calculate_size(80, 800, height)
            self.new_game_button.text = self.langs['new_game_button'].get(self.game.settings.get('language'))

            self.continue_button.set_center(width * 0.5, height * 0.4)
            self.continue_button.width = calculate_size(300, 800, width)
            self.continue_button.height = calculate_size(80, 800, height)
            self.continue_button.text = self.langs['continue_button'].get(self.game.settings.get('language'))

            self.load_button.set_center(width * 0.5, height * 0.53)
            self.load_button.width = calculate_size(300, 800, width)
            self.load_button.height = calculate_size(80, 800, height)
            self.load_button.text = self.langs['load_button'].get(self.game.settings.get('language'))

            self.save_button.set_center(width * 0.5, height * 0.66)
            self.save_button.width = calculate_size(300, 800, width)
            self.save_button.height = calculate_size(80, 800, height)
            self.save_button.text = self.langs['save_button'].get(self.game.settings.get('language'))

            self.settings_button.set_center(width * 0.5, height * 0.79)
            self.settings_button.width = calculate_size(300, 800, width)
            self.settings_button.height = calculate_size(80, 800, height)
            self.settings_button.text = self.langs['settings_button'].get(self.game.settings.get('language'))

            self.quit_button.set_center(width * 0.5, height * 0.92)
            self.quit_button.width = calculate_size(300, 800, width)
            self.quit_button.height = calculate_size(80, 800, height)
            self.quit_button.text = self.langs['quit_button'].get(self.game.settings.get('language'))

        if self.mode == "campaign":
            self.check_win()

        if not self.saved_last and self.mode == "campaign":
            self.game.logger.info("Saving last.")
            self.save_last()

    def handle_event(self, event: pygame.event.Event):
        if self.scene is not None and self.scene.active:
            self.scene.handle_event(event)
            return

        for item in self.game.game_data.world.items:
            item: classes.Item
            item.handle_event(event)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_t and not self.esc_screen:
                self.game.game_data.player.teleport(self.game.game_data.world)

            if event.key == pygame.K_r and self.cd_gun_choosing.check() and not self.esc_screen:
                self.gun_choosing = not self.gun_choosing
                self.cd_gun_choosing.refresh(0)

            if event.key == pygame.K_TAB and not self.esc_screen:
                if self.cd_gun_choosing.check():
                    self.quick_gun_swap_index += 1
                    old_gun = self.game.game_data.player.using_gun
                    try:
                        self.game.game_data.player.available_guns[self.quick_gun_swap_index]
                    except IndexError:
                        self.quick_gun_swap_index = 0
                    finally:
                        selected_gun = self.game.game_data.player.available_guns[self.quick_gun_swap_index]
                        if type(selected_gun) == classes.Charm:
                            self.game.game_data.player.using_gun = selected_gun
                            selected_gun.used = False
                            selected_gun.equip(self.game.game_data.player)
                        else:
                            if old_gun is not None:
                                if type(old_gun) == classes.Charm:
                                    old_gun.unequip(self.game.game_data.player)
                                self.game.game_data.player.using_gun = selected_gun
                    self.cd_gun_choosing.refresh(1)
                    self.game.game_data.player.drawing = False

            if event.key == pygame.K_ESCAPE and not self.gun_choosing:
                self.esc_screen = not self.esc_screen
                if self.esc_screen:
                    self.game.mixer.music.pause()
                else:
                    self.game.mixer.music.unpause()

        if self.gun_choosing:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                secilen = self.game.game_data.player.weapon_wheel_get_mouse(self.gun_choosing)
                if secilen is not None:
                    secilen: int
                    old_gun = self.game.game_data.player.using_gun
                    selected_gun = self.game.game_data.player.available_guns[secilen]
                    if type(selected_gun) == classes.Charm:
                        self.game.game_data.player.using_gun = selected_gun
                        selected_gun.used = False
                        selected_gun.equip(self.game.game_data.player)
                    else:
                        if old_gun is not None:
                            if type(old_gun) == classes.Charm:
                                old_gun.unequip(self.game.game_data.player)
                        self.game.game_data.player.using_gun = selected_gun
                    self.quick_gun_swap_index = secilen
                    self.gun_choosing = False
                    self.game.game_data.player.drawing = False

        elif self.esc_screen:
            if self.new_game_button.clicked(event, ScreenType.GAME):
                if self.game.settings.get("sfx"):
                    self.game.sfx_manager.play("click", self.game.settings.get("sfx_volume"))
                self.game.game_data = GameData.to_gamedata(game_data_defaults)
                self.esc_screen = False
                self.start_new_game(mode=self.mode)
                return

            if self.continue_button.clicked(event, ScreenType.GAME):
                if self.game.settings.get("sfx"):
                    self.game.sfx_manager.play("click", self.game.settings.get("sfx_volume"))
                self.esc_screen = False
                return

            if self.save_button.clicked(event, ScreenType.GAME):
                if self.mode == "campaign":
                    if self.game.settings.get("sfx"):
                        self.game.sfx_manager.play("click", self.game.settings.get("sfx_volume"))
                    self.game.screen_manager.set_screen(ScreenType.SAVE, screen_type_before=ScreenType.GAME)

            if self.load_button.clicked(event, ScreenType.GAME):
                if self.game.settings.get("sfx"):
                    self.game.sfx_manager.play("click", self.game.settings.get("sfx_volume"))
                self.game.screen_manager.set_screen(ScreenType.LOAD, screen_type_before=ScreenType.GAME)

            if self.settings_button.clicked(event, ScreenType.GAME):
                if self.game.settings.get("sfx"):
                    self.game.sfx_manager.play("click", self.game.settings.get("sfx_volume"))
                self.game.screen_manager.set_screen(ScreenType.SETTINGS)

            if self.quit_button.clicked(event, ScreenType.GAME):
                if self.game.settings.get("sfx"):
                    self.game.sfx_manager.play("click", self.game.settings.get("sfx_volume"))
                self.game.screen_manager.set_screen(ScreenType.MENU)
                return

        else:
            self.game.game_data.player.handle_event(event)

    def check_win(self):
        if self.game.game_data.win:
            if not self.game.cheated:
                if self.game.achievements is not None:
                    self.game.achievements.unlock("win")
                if self.game.const_game_data is not None:
                    self.game.const_game_data["worlds_accessable"] = True
                if self.game.dump("new_game"):
                    self.game.val_manager("win", 1, "change")
            else:
                if self.game.last_boss == "urasin_sumuklu_pecetesi":
                    if self.game.achievements is not None:
                        self.game.achievements.unlock("masks_importance")
            self.game.screen_manager.set_screen(ScreenType.WIN)

    def update_level(self):
        if len(self.levels) < self.game.game_data.level:
            self.game.game_data.win = True
            return

        new_level = self.game.game_data.world.next_level()

        if new_level == True:
            self.game.game_data.win = True
            return

        elif type(new_level) == DefaultWorld:
        
            try:
                adding_gun = level_sword_map[f"level{self.game.game_data.level}"]
                found = False

                if any(type(gun) == type(adding_gun) for gun in self.game.game_data.player.available_guns):
                    for i, gun in enumerate(self.game.game_data.player.available_guns):
                        gun: classes.Sword | classes.Gun
                        if type(gun) == type(adding_gun):
                            if classes.material_order[gun.material] <= classes.material_order[adding_gun.material]:
                                self.game.game_data.player.available_guns[i] = adding_gun
                            found = True

                if not found:
                    self.game.game_data.player.available_guns.append(adding_gun)
                self.game.game_data.player.using_gun = adding_gun

            except KeyError:
                pass

            try:
                for item in level_item_map[f"level{self.game.game_data.level}"]:
                    new_item = item.copy()
                    new_item.set_pos(self.game.game_data.world)
                    self.game.game_data.world.items.append(new_item)

            except KeyError:
                pass

            self.game.game_data.enemy_data = {}

            for enemy in self.levels[self.game.game_data.level - 1]:
                fresh_enemy = enemy.copy()
                fresh_enemy.reset(self.game.game_data.world)
                self.game.game_data.enemy_data[fresh_enemy.id] = fresh_enemy

            for enemy in self.game.game_data.enemy_data.values():
                enemy.set_pos(self.game.game_data.world, self.game.info)

            if self.game.settings.get("music"):
                for enemy in self.game.game_data.enemy_data.values():
                    if type(enemy) == classes.Boss and enemy.name.lower() == "uras'ın sümüklü peçetesi":
                        self.game.mixer.music.load(
                            os.path.join(BASE_DIR, r"musics/kim_ne_derse_desin.oga")
                        )
                        self.game.mixer.music.play(-1)
                        break

            dialogues = []

            for enemy in self.game.game_data.enemy_data.values():
                if type(enemy) == classes.Boss and enemy.scene_dialogues:
                    for speaker, text in enemy.scene_dialogues:
                        if speaker == "Boss":
                            image = enemy.full_image
                            target_w = scale(320)
                            target_h = int(image.get_height() * (target_w / image.get_width()))
                            image = pygame.transform.smoothscale(image, (target_w, target_h))

                            boss_typing_sound = enemy.typing_sound

                        elif speaker == "Player":
                            image = create_player_dialogue_portrait(width=380, height=430)

                        dialogues.append(
                            SceneDialogue(
                                speaker,
                                text,
                                image
                            )
                        )

            if dialogues:
                self.scene = Scene(
                    font=self.dfont1,
                    dialogues=dialogues,
                    typing_sound2=self.typing_sound,
                    typing_sound1=boss_typing_sound
                )
                self.scene.start()

        else: # Eğer world özel ise

            level, sword, items = new_level

            self.game.game_data.enemy_data = {}

            for enemy in level:
                fresh_enemy = enemy.copy()
                fresh_enemy.reset(self.game.game_data.world)

                self.game.game_data.enemy_data[fresh_enemy.id] = fresh_enemy

            for enemy in self.game.game_data.enemy_data.values():
                enemy.set_pos(self.game.game_data.world, self.game.info)

            if type(sword) != NoSword: # Kılıç eklenecekse
                adding_gun = sword
                found = False

                if any(type(gun) == type(adding_gun) for gun in self.game.game_data.player.available_guns):
                    for i, gun in enumerate(self.game.game_data.player.available_guns):
                        gun: classes.Sword | classes.Gun
                        if type(gun) == type(adding_gun):
                            if classes.material_order[gun.material] <= classes.material_order[adding_gun.material]:
                                self.game.game_data.player.available_guns[i] = adding_gun
                            found = True

                if not found:
                    self.game.game_data.player.available_guns.append(adding_gun)
                self.game.game_data.player.using_gun = adding_gun

            if type(items) != NoItem:
                for item in items:
                    item: classes.Item
                    
                    new_item = item.copy()
                    new_item.set_pos(self.game.game_data.world)
                    self.game.game_data.world.items.append(new_item)

            # Konuşma sahnesi hazırlama
            dialogues = []

            for enemy in self.game.game_data.enemy_data.values():
                if type(enemy) == classes.Boss and enemy.scene_dialogues:
                    for speaker, text in enemy.scene_dialogues:
                        if speaker == "Boss":
                            image = enemy.full_image
                            target_w = scale(320)
                            target_h = int(image.get_height() * (target_w / image.get_width()))
                            image = pygame.transform.smoothscale(image, (target_w, target_h))

                            boss_typing_sound = enemy.typing_sound

                        elif speaker == "Player":
                            image = create_player_dialogue_portrait(width=380, height=430)

                        dialogues.append(
                            SceneDialogue(
                                speaker,
                                text,
                                image
                            )
                        )

            if dialogues:
                self.scene = Scene(
                    font=self.dfont1,
                    dialogues=dialogues,
                    typing_sound2=self.typing_sound,
                    typing_sound1=boss_typing_sound
                )
                self.scene.start()

    def check_level(self):
        if all(not enemy.living for enemy in self.game.game_data.enemy_data.values()):
            self.game.game_data.level += 1
            self.game.logger.info(f"Started level {self.game.game_data.level}")
            self.update_level()

    def start_new_game(self, mode: str = "campaign"):
        self.mode = mode
        self.esc_screen = False
        self.gun_choosing = False
        self.game.game_data.win = False
        self.max_combo = 0

        self.game.game_data.world.create_rocks(
            self.game.info.current_w,
            self.game.info.current_h
        )

        if self.mode == "freeplay":
            self.freeplay_wave = 1
            p = self.game.game_data.player
            p.available_guns = [
                classes.Sword("Altın Kılıç", 40, colours.YELLOW, 850, MaterialFlags.GOLDEN),
                bronze_gun,
                classes.Gun(
                    "Gümüş Tabanca",
                    colours.WHITE,
                    35,
                    1200,
                    os.path.join(BASE_DIR, "images/silver_silahr.png"),
                    os.path.join(BASE_DIR, "images/silver_silah_mermi.png"),
                    0.25,
                    MaterialFlags.SILVER
                )
            ]
            p.using_gun = p.available_guns[0]
            self.spawn_freeplay_wave(self.freeplay_wave)
        else:
            self.game.game_data.level = 1


            if not getattr(self, "_special_events_injected", False):
                levels[14].append(classes.Enemy.skzoo(self.game.game_data.player, special=True))
                level_item_map["level7"][0].effects.append(
                    classes.Effect(
                        None,
                        None, 
                        -1,
                        self.game.game_data.player.available_guns,
                        [bronze_gun]
                    )
                )
                self._special_events_injected = True

            self.update_level()

    def load_game(self):
        pass

    def save_last(self):
        try:
            self.game.save_manager.save_last_slot(self.game.game_data, self.game.cheated)
        except KeyError:
            pass
        self.saved_last = True
        self.save_last_cd.refresh()

    def on_enter(self, transfer_datas):
        # Oyuncu nesnesine juice referansı ata
        if hasattr(self.game.game_data, "player"):
            self.game.game_data.player.juice = self.game.juice

        self.font1 = get_font(
            self.game.fonts,
            Lang.USING_LANG,
            1,
            "userFont"
        )
        self.font2 = get_font(
            self.game.fonts,
            Lang.USING_LANG,
            2,
            "userFont"
        )
        self.font3 = get_font(
            self.game.fonts,
            Lang.USING_LANG,
            3,
            "userFont"
        )
        self.dfont1 = get_font(
            self.game.fonts,
            Lang.USING_LANG,
            1,
            "DynamicFont"
        )

        self.new_game_button = Button(
            0, 0, 300, 80,
            "Yeni Oyun",
            self.dfont1,
            colours.YELLOW,
            colours.WHITE,
            [ScreenType.MENU, ScreenType.GAME],
            colours.darker(colours.YELLOW, 20),
            colours.darker(colours.YELLOW, 50),
            design="bevel",
            border_radius=0
        )

        self.continue_button = Button(
            0, 0, 300, 80,
            "Devam Et",
            self.dfont1,
            colours.YELLOW,
            colours.WHITE,
            [ScreenType.MENU, ScreenType.GAME],
            colours.darker(colours.YELLOW, 20),
            colours.darker(colours.YELLOW, 50),
            design="bevel",
            border_radius=0
        )

        self.load_button = Button(
            0, 0, 300, 80,
            "Yükle",
            self.dfont1,
            colours.YELLOW,
            colours.WHITE,
            [ScreenType.MENU, ScreenType.GAME],
            colours.darker(colours.YELLOW, 20),
            colours.darker(colours.YELLOW, 50),
            design="bevel",
            border_radius=0
        )

        self.save_button = Button(
            0, 0, 300, 80,
            "Kaydet",
            self.dfont1,
            colours.YELLOW,
            colours.WHITE,
            [ScreenType.MENU, ScreenType.GAME],
            colours.darker(colours.YELLOW, 20),
            colours.darker(colours.YELLOW, 50),
            design="bevel",
            border_radius=0
        )

        self.settings_button = Button(
            0, 0, 300, 80,
            "Ayarlar",
            self.dfont1,
            colours.YELLOW,
            colours.WHITE,
            [ScreenType.MENU, ScreenType.GAME],
            colours.darker(colours.YELLOW, 20),
            colours.darker(colours.YELLOW, 50),
            design="bevel",
            border_radius=0
        )

        self.quit_button = Button(
            0, 0, 300, 80,
            "Çık",
            self.dfont1,
            colours.RED,
            colours.WHITE,
            [ScreenType.MENU, ScreenType.GAME],
            colours.darker(colours.RED, 20),
            colours.darker(colours.RED, 50),
            design="bevel",
            border_radius=0
        )

        self.game.mixer.music.stop()
        self.game.dump("last_music", "__change__")

        if self.game.settings.get("music"):
            for enemy in self.game.game_data.enemy_data.values():
                if type(enemy) == classes.Boss and enemy.name.lower() == "uras'ın sümüklü peçetesi":
                    self.game.mixer.music.load(
                        os.path.join(BASE_DIR, r"musics/kim_ne_derse_desin.oga")
                    )
                    self.game.mixer.music.play(-1)
                    break

            try:
                filename = ""
                if self.game.settings.get("music_source").get("english").lower() == "music path":
                    filename = self.game.settings.get("other_music")
                elif self.game.settings.get("music_source").get("english").lower() == "selected music":
                    if isinstance(self.game.settings.get("selected_music"), (classes.Music, Music)):
                        filename = self.game.settings.get("selected_music").filename

                self.game.mixer.music.load(filename)
                self.game.mixer.music.play(-1)
                self.game.dump("last_music", filename)

            except FileNotFoundError:
                self.game.logger.warning(f"Music {filename} is not found.")
            except pygame.error as e:
                self.game.logger.error(f"Loading File {filename} caused pygame.error: {e}")

        self.game.played = True

    def on_exit(self):
        self.game.mixer.music.stop()