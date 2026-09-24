from .screen import Screen
import pygame
from levels import level_sword_map, level_item_map, levels, bronze_gun
import typehint_game
import classes
from fonts import font1, font2, font3, font4
import colours
from classes import Button, defaults as game_data_defaults
from calcs import calculate_size
from lang_support import Lang

from gamedata import GameData

from .types import ScreenType

from cooldown import Cooldown

class GameScreen(Screen):
    def __init__(self, game):
        super().__init__(game)
        self.game: typehint_game.Game

        self.langs = {
            "new_game_button": Lang(türkçe="Yeni Oyun", english="New Game"),
            "continue_button": Lang(türkçe="Devam Et", english="Continue"),
            "load_button": Lang(türkçe="Yükle", english="Load"),
            "save_button": Lang(türkçe="Kaydet", english="Save"),
            "settings_button": Lang(türkçe="Ayarlar", english="Settings"),
            "quit_button": Lang(türkçe="Çık", english="Quit")
        }

        self.levels: list[list[classes.Enemy]] = levels

        self.dash_cooldown = Cooldown(0.13)
        self.cd_gun_choosing = Cooldown(0.4, 0.35)

        self.gun_choosing = False
        self.esc_screen = False

        self.quick_gun_swap_index = 0
        self.saved_last = False
        self.save_last_cd = Cooldown(20)


        self.new_game_button = Button(
            0, 0, 300, 80,
            "Yeni Oyun",
            font1,
            colours.YELLOW,
            colours.WHITE,
            [ScreenType.MENU, ScreenType.GAME],
            colours.darker(colours.YELLOW, 20),
            colours.darker(colours.YELLOW, 50)
        )

        self.continue_button = Button(
            0, 0, 300, 80,
            "Devam Et",
            font1,
            colours.YELLOW,
            colours.WHITE,
            [ScreenType.MENU, ScreenType.GAME],
            colours.darker(colours.YELLOW, 20),
            colours.darker(colours.YELLOW, 50)
        )

        self.load_button = Button(
            0, 0, 300, 80,
            "Yükle",
            font1,
            colours.YELLOW,
            colours.WHITE,
            [ScreenType.MENU, ScreenType.GAME],
            colours.darker(colours.YELLOW, 20),
            colours.darker(colours.YELLOW, 50)
        )

        self.save_button = Button(
            0, 0, 300, 80,
            "Kaydet",
            font1,
            colours.YELLOW,
            colours.WHITE,
            [ScreenType.MENU, ScreenType.GAME],
            colours.darker(colours.YELLOW, 20),
            colours.darker(colours.YELLOW, 50)
        )

        self.settings_button = Button(
            0, 0, 300, 80,
            "Ayarlar",
            font1,
            colours.YELLOW,
            colours.WHITE,
            [ScreenType.MENU, ScreenType.GAME],
            colours.darker(colours.YELLOW, 20),
            colours.darker(colours.YELLOW, 50)
        )

        self.quit_button = Button(
            0, 0, 300, 80,
            "Çık",
            font1,
            colours.RED,
            colours.WHITE,
            [ScreenType.MENU, ScreenType.GAME],
            colours.darker(colours.RED, 20),
            colours.darker(colours.RED, 50)
        )
    
    def draw(self, surface: pygame.Surface):
        self.game.game_data.world.draw(surface)
        self.game.game_data.world.draw_items(surface, font3, self.game.game_data.player)

        if type(self.game.game_data.player.using_gun) == classes.Sword:
            self.game.game_data.player.using_gun.draw(
                surface,
                self.game.game_data.player.x + self.game.game_data.player.hand_spot,
                self.game.game_data.player.y + 10,
                True if self.game.game_data.player.drawing or self.game.game_data.player.sword_attacking else False, self.game.game_data.player.angle
            )

        elif type(self.game.game_data.player.using_gun) == classes.Gun:
            self.game.game_data.player.using_gun.draw(
                surface,
                self.game.game_data.player.x + 30,
                self.game.game_data.player.y + 10
            )
    
        elif type(self.game.game_data.player.using_gun) == classes.Charm:
            self.game.game_data.player.using_gun.draw(
                surface,
                self.game.game_data.player.x + 30,
                self.game.game_data.player.y + 10
            )

        for enemy in self.game.game_data.enemy_data.values():
            enemy.draw_arrows(surface)
            enemy.draw_bombs(surface)
            enemy.draw_sgrounds(surface)

        classes.Enemy.draw(
            surface,
            font3,
            list(self.game.game_data.enemy_data.values()),
            font1
        )

        self.game.game_data.player.draw(surface)
        self.game.game_data.player.draw_dash(surface)
        self.game.game_data.player.draw_teleport(surface)
        self.game.game_data.player.draw_statistics(surface, font2, self.game.info)

        for enemy in self.game.game_data.enemy_data.values():
            enemy.draw_scr_lazers(surface)

        if self.gun_choosing:
            self.game.game_data.player.draw_available_guns(surface)

        elif self.esc_screen:
            self.new_game_button.draw(surface)
            self.continue_button.draw(surface)
            self.load_button.draw(surface)
            self.save_button.draw(surface)
            self.settings_button.draw(surface)
            self.quit_button.draw(surface)

    def update(self, dt):
        if not self.esc_screen and not self.gun_choosing:

            self.dash_cooldown.reduce(dt)
            self.cd_gun_choosing.reduce(dt)

        self.save_last_cd.reduce(dt)

        if self.save_last_cd.check():
            self.saved_last = False

        keys = pygame.key.get_pressed()

        if not self.gun_choosing and not self.esc_screen:

            if keys[pygame.K_LSHIFT] and self.dash_cooldown.check() and not self.game.game_data.player.drawing and type(self.game.game_data.player.using_gun) == classes.Sword:
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
                self.game.game_data.player.sword_attack(dt)

                if type(self.game.game_data.player.using_gun) == classes.Gun:
                    self.game.game_data.player.using_gun.update(
                        self.game.game_data.world,
                        dt,
                        self.game.game_data.enemy_data.values(),
                        self.game.game_data.player
                    )

                if type(self.game.game_data.player.using_gun) == classes.Charm:
                    self.game.game_data.player.using_gun.update(self.game.game_data.player.angle, dt)
                    self.game.game_data.player.using_gun.use_active(self.game.game_data.player, dt)

                if type(self.game.game_data.player.using_gun) == classes.Sword:
                    self.game.game_data.player.deflect(self.game.game_data.enemy_data.values(), dt)

                for enemy in self.game.game_data.enemy_data.values():
                    enemy: classes.Enemy
                    enemy.update(self.game.game_data.player, self.game.game_data.world, dt, self.game.game_data.enemy_data.values())
                    enemy.update_arrows(self.game.game_data.player, dt)
                    enemy.summon(dt, self.game.game_data.enemy_data.values(), self.game.game_data.world)
                    enemy.update_bombs(self.game.game_data.player, dt)
                    enemy.update_cat_jump(self.game.game_data.player, dt)
                    enemy.update_scr_lazers(self.game.game_data.player, dt)

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
                except KeyError:
                    pass

            self.game.game_data.player.damage(
                self.game.game_data.enemy_data.values(),
                dt,
                self.gun_choosing
                )

            if self.game.game_data.player.hp <= 0:
                self.game.screen_manager.set_screen(ScreenType.LOSE)
                return

            self.check_level()

        if self.esc_screen:
            width = self.game.width
            height = self.game.height

            self.new_game_button.set_center(width * 0.5, height * 0.27)
            self.new_game_button.width = calculate_size(300, 800, width) # bu butonların genişliği 300 yüksekliği 800
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



        self.check_win()

        if not self.saved_last:
            self.save_last()
        self.game.logger.info("Saving last.")

    def handle_event(self, event: pygame.event.Event):

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
                        if type(self.game.game_data.player.available_guns[self.quick_gun_swap_index]) == classes.Charm:
                                self.game.game_data.player.using_gun = self.game.game_data.player.available_guns[self.quick_gun_swap_index]
                                self.game.game_data.player.using_gun.used = False
                                self.game.game_data.player.using_gun.equip(self.game.game_data.player)
                        else:
                            if old_gun is not None:
                                if type(old_gun) == classes.Charm:
                                    old_gun.unequip(self.game.game_data.player)
                                self.game.game_data.player.using_gun = self.game.game_data.player.available_guns[self.quick_gun_swap_index]
                    self.cd_gun_choosing.refresh(1)
                    self.game.game_data.player.drawing = False

            if event.key == pygame.K_ESCAPE and not self.gun_choosing:
                self.esc_screen = not self.esc_screen

        if self.gun_choosing:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                secilen = self.game.game_data.player.weapon_wheel_get_mouse(self.gun_choosing)
                if secilen is not None:
                    secilen: int
                    old_gun = self.game.game_data.player.using_gun
                    if type(self.game.game_data.player.available_guns[secilen]) == classes.Charm:
                        self.game.game_data.player.using_gun = self.game.game_data.player.available_guns[secilen]
                        self.game.game_data.player.using_gun.used = False
                        self.game.game_data.player.using_gun.equip(self.game.game_data.player)
                    else:
                        if old_gun is not None:
                            if type(old_gun) == classes.Charm:
                                old_gun.unequip(self.game.game_data.player)
                        self.game.game_data.player.using_gun = self.game.game_data.player.available_guns[secilen]
                    self.quick_gun_swap_index = secilen

                    self.gun_choosing = False
                    self.game.game_data.player.drawing = False

        elif self.esc_screen:
            if self.new_game_button.clicked(event, ScreenType.GAME):
                self.game.game_data = GameData.to_gamedata(game_data_defaults)
                game_screen = self.game.screen_manager.get_screen(ScreenType.GAME)
                game_screen.start_new_game()
                self.game.screen_manager.set_screen(ScreenType.GAME)
                return

            if self.continue_button.clicked(event, ScreenType.GAME):
                self.esc_screen = False
                return

            if self.save_button.clicked(event, ScreenType.GAME):
                self.game.screen_manager.set_screen(ScreenType.SAVE, screen_type_before=ScreenType.GAME)

            if self.load_button.clicked(event, ScreenType.GAME):
                self.game.screen_manager.set_screen(ScreenType.LOAD, screen_type_before=ScreenType.GAME)

            if self.settings_button.clicked(event, ScreenType.GAME):
                self.game.screen_manager.set_screen(ScreenType.SETTINGS)

            if self.quit_button.clicked(event, ScreenType.GAME):
                self.game.running = False
                return

    def check_win(self):
        if self.game.game_data.win:
            self.game.screen_manager.set_screen(ScreenType.WIN)

    def update_level(self):
        if len(self.levels) < self.game.game_data.level: # +1 yapmamamın sebebi seviye 1den başlıyor ama indexler 0dan.
            self.game.game_data.win = True
            return
        
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
                item.set_pos(self.game.game_data.world, self.game.game_data.player)
                self.game.game_data.world.items.append(item)
        except KeyError:
            pass

        self.game.game_data.enemy_data = {}

        for enemy in self.levels[self.game.game_data.level - 1]:
            enemy: classes.Enemy
            self.game.game_data.enemy_data[enemy.id] = enemy

        for enemy in self.game.game_data.enemy_data.values():
            enemy: classes.Enemy
            enemy.set_pos(self.game.game_data.world, self.game.info)


    def check_level(self):
        if all(not enemy.living for enemy in self.game.game_data.enemy_data.values()):
            self.game.game_data.level += 1

            self.game.logger.info(f"Started level {self.game.game_data.level}")

            self.update_level()

    def start_new_game(self):

        self.game.game_data.world.create_rocks(
            self.game.info.current_w,
            self.game.info.current_h
        )

        levels[14].append(classes.Enemy.skzoo(self.game.game_data.player, special=True))
        level_item_map["level7"][0].effects.append( # levels.py'da oluşturulamayacak effect ekleniyor
            classes.Effect(
                None,
                None, 
                -1,
                self.game.game_data.player.available_guns,
                [bronze_gun]
            )
        )

        self.update_level()

    def load_game(self):
        pass

    def save_last(self):
        try:
            self.game.save_manager.save_last_slot(self.game.game_data)
        except KeyError:
            pass
        self.saved_last = True
        self.save_last_cd.refresh()

    def on_enter(self, transfer_datas):
        self.game.mixer.music.stop()

        if self.game.settings.get("music"):
            self.game.mixer.music.load(
                self.game.settings.get("other_music")
            )

            self.game.mixer.music.play(-1)

        self.game.played = True

    def on_exit(self):
        self.game.mixer.music.stop()
