import pygame
import colours
import os
import math
import random
from zaman import after
import copy
import uuid
import logging
import settings_manager
from exceptions import EnemyPositionError
from enum import Enum, auto
import _pickle
from cooldown import Cooldown
from helper_funcs import draw_aa_line
from screens.types import ScreenType
from fonts import font2
from userfont import userFont
from basedir import BASE_DIR


manager = settings_manager.SettingsManager("settings", os.path.join(BASE_DIR,"settings"), "TEST", "2.0")


logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(filename)s: %(lineno)d [%(funcName)s] | %(message)s',
    level=logging.DEBUG if manager.get_attribute("DEBUG") else logging.INFO,
    filename="game.log"
)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG if manager.get_attribute("DEBUG") else logging.INFO)
pygame.init()
info = pygame.display.Info()


class LimitedNumber:
    def __init__(self, deger: float, minimum: float, maksimum: float):
        self.min = minimum
        self.max = maksimum
        self.deger = deger

    @property
    def deger(self):
        return self._deger

    @deger.setter
    def deger(self, yeni):
        self._deger = max(self.min, min(yeni, self.max))


class Slot:
    slots = []

    def __init__(self, id, display=None):
        self.id = id
        self.display = display
        self.display: Button

        self.used = False
        self.version = "Unknown"
        self.info = None
        self.unknown = False
        self.corrupted = False
        self.slots.append(self)

    @classmethod
    def update_infos(cls, save_manager):
        infos = save_manager.get_all_infos()

        for slot in cls.slots:
            slot: Slot
            slot.info = infos.get(slot.id)

            slot.used = slot.info is not None
            

            try:
                save_manager.get_info(slot.id)
            except _pickle.UnpicklingError:
                slot.corrupted = True
            except EOFError:
                logging.warning(f"Slot {slot.id} caused EOFError.")
                slot.used = False
            except Exception as e:
                logging.error(e)
                slot.unknown = True
            logging.debug(slot.info)

    @staticmethod
    def create_slots(save_manager):
        for i in range(70):
            # Zaten otomatik listeye ekliyor
            Slot(
                i,
                display=Button(
                        0, 0, 600, 200, f"Slot {i+1}",
                        font2,
                        colours.BLUE,
                        colours.WHITE,
                        [ScreenType.LOAD, ScreenType.SAVE],
                        colours.darker(colours.BLUE, 20),
                        border_radius=5
                        )
            )
        Slot.update_infos(save_manager)


class AlignedRect:
    rects = []

    def __init__(self, x: int, y: int, width: int, height: int, font: userFont, color, text=None, text_color=None, on_mouse_color=None, border_radius=10, plus_data=None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rect = pygame.Rect(x-width//2, y-height//2, width, height)
        self.text = text or ""
        self.font = font
        self.color = color
        self.origin_color = color
        self.text_color = text_color
        self.on_mouse_color = on_mouse_color or colours.darker(color, 20)
        self.border_radius = border_radius
        self.clicking = False
        self.plus_data = plus_data
        self.rects.append(self)

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect, border_radius=self.border_radius)

        lines = self.text.splitlines()

        line_height = self.font.font.get_height()
        total_height = len(lines) * line_height

        y = self.rect.centery - total_height // 2

        for line in lines:
            text_surface = self.font.font.render(line, True, self.text_color)
            text_rect = text_surface.get_rect(center=(self.rect.centerx, y + line_height // 2))
            surface.blit(text_surface, text_rect)
            y += line_height

    def set_center(self, x, y):
        self.rect.center = (x, y)

    def set_topleft(self, x, y):
        self.rect.topleft = (x, y)

    def on_mouse(self):
        if self.clicking:
            return
        mouse_pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(mouse_pos):
            if self.on_mouse_color is not None:
                self.color = self.on_mouse_color
            return True
        else:
            self.color = self.origin_color
            return False


class Button:
    buttons = []

    def __init__(self, x: int, y: int, width: int, height: int, text, font: userFont, color, text_color, game_state: list, on_mouse_color=None, on_click_color=None, border_radius=10, plus_data=None):
        self.id = 0 if self.buttons == [] else self.buttons[-1].id + 1
        self.x = x
        self.y = y
        self.rect = pygame.Rect(x-width//2, y-height//2, width, height)
        self.text = text
        self.font = font
        self.color = color
        self.origin_color = color
        self.text_color = text_color
        self.on_mouse_color = on_mouse_color or colours.darker(color, 20)
        self.on_click_color = on_click_color or colours.darker(color, 50)
        self.border_radius = border_radius
        self.game_state = game_state
        self.plus_data = plus_data
        self.clicking = False

    @property
    def width(self):
        return self.rect.width

    @width.setter
    def width(self, value):
        self.rect.width = value

    @property
    def height(self):
        return self.rect.height

    @height.setter
    def height(self, value):
        self.rect.height = value
            
    def clicked(self, event, state):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if state in self.game_state:
                if event.button == 1 and self.rect.collidepoint(event.pos):
                    self.clicking = True

                    if self.on_click_color is not None:
                        self.color = self.on_click_color

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.clicking:
                self.clicking = False

                if self.rect.collidepoint(event.pos):
                    if self.on_mouse_color is not None:
                        self.color = self.on_mouse_color
                    else:
                        self.color = self.origin_color
                    return True
                else:
                    self.color = self.origin_color

        return False

    def on_mouse(self):
        if self.clicking:
            return
        mouse_pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(mouse_pos):
            if self.on_mouse_color is not None:
                self.color = self.on_mouse_color
            return True
        else:
            self.color = self.origin_color
            return False

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect, border_radius=self.border_radius)

        lines = self.text.splitlines()

        line_height = self.font.font.get_height()
        total_height = len(lines) * line_height

        y = self.rect.centery - total_height // 2

        for line in lines:
            text_surface = self.font.font.render(line, True, self.text_color)
            text_rect = text_surface.get_rect(center=(self.rect.centerx, y + line_height // 2))
            surface.blit(text_surface, text_rect)
            y += line_height

    def set_center(self, x, y):
        self.rect.center = (x, y)

    def set_topleft(self, x, y):
        self.rect.topleft = (x, y)


class InputBox:
    def __init__(self, x, y, width, height, color: tuple, font: userFont, waiting_font: userFont = None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rect = pygame.Rect(
            self.x,
            self.y,
            self.width,
            self.height
        )
        self.rect.midleft = (self.x, self.y)
        self.color = color
        self.text = ""
        self.active = False
        self.font = font
        self.waiting_font = waiting_font or font

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.key == 1:
                if self.rect.collidepoint(event.pos):
                    self.active = True
                else:
                    self.active = False
            else:
                self.active = False
        if self.active:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    self.text[-1]=""
                else:
                    if event.unicode.isprintable():
                        self.text += event.unicode

    def draw(self, surface: pygame.Surface):
        pygame.draw.rect(surface, self.color, self.rect, 3)
        self.font.draw_text(self.text, (self.x + 10, self.y), surface, colours.WHITE, hiza="midleft")
        

class MaterialFlags(Enum):
    WOODEN = auto()
    ROCK = auto()
    IRON = auto()
    BRONZE = auto()
    SILVER = auto()
    GOLDEN = auto()
    DIAMOND = auto()
    OTHER = auto()
    SPECIAL = auto()

material_order = {
        MaterialFlags.WOODEN: 1,
        MaterialFlags.ROCK: 2,
        MaterialFlags.IRON: 3,
        MaterialFlags.BRONZE: 4,
        MaterialFlags.SILVER: 5,
        MaterialFlags.GOLDEN: 6,
        MaterialFlags.DIAMOND: 7,
        MaterialFlags.OTHER: 8,
        MaterialFlags.SPECIAL: 9
}


class Sword:
    def __init__(self, name: str, attack: int, color: tuple, dash_speed, material):
        self.name = name
        self.attack = attack
        self.material = material
        self.color = color
        self.dash_speed = dash_speed
        print("RENK:",self.color)

    def draw(self, surface, x, y, dashing: bool, angle):
        blade_length = 60
        blade_width = 8
        handle_length = 18
        guard_width = 24
        if not dashing:
            rad = math.radians(-90)
        else:
            if angle < 90 and angle > -90:
                rad = math.radians(0)
            else:
                rad = math.radians(180)

        dx = math.cos(rad)
        dy = math.sin(rad)

        px = -dy
        py = dx

        # Bıçak ucu
        tip_x = x + dx * blade_length
        tip_y = y + dy * blade_length

        blade = [
            (x + px * blade_width/2, y + py * blade_width/2),
            (x - px * blade_width/2, y - py * blade_width/2),
            (tip_x - px * blade_width/2, tip_y - py * blade_width/2),
            (tip_x, tip_y),
            (tip_x + px * blade_width/2, tip_y + py * blade_width/2)
        ]

        # Bıçak
        pygame.draw.polygon(surface, self.color, blade)

        # Kabza
        handle_x = x - dx * handle_length
        handle_y = y - dy * handle_length

        pygame.draw.line(
            surface,
            (110, 70, 30),
            (x, y),
            (handle_x, handle_y),
            6
        )

        # El koruması
        pygame.draw.line(
            surface,
            (255, 215, 0),
            (
                x + px * guard_width/2,
                y + py * guard_width/2
            ),
            (
                x - px * guard_width/2,
                y - py * guard_width/2
            ),
            5
        )

        # Kabza ucu
        pygame.draw.circle(
            surface,
            (180, 180, 180),
            (int(handle_x), int(handle_y)),
            4
        )


class SwapValue:
    def __init__(self, value=None):
        self.value = value


class Charm:
    def __init__(self, name: str, image_name: os.PathLike, image_size, passive_effects: list, active_effects: list, cooldown: int):
        self.name = name
        self.image_name = image_name
        self.image = pygame.image.load(self.image_name)
        self.image_size = image_size
        self.image = pygame.transform.scale_by(self.image, image_size)
        self.passive_effects = passive_effects
        self.active_effects = active_effects
        self.or_cooldown = cooldown
        self.cooldown = cooldown
        self.used = False
        self.texts = []
        self.effected = False
        self.old_player = None

    def draw(self, surface: pygame.Surface, x: int, y: int):
        for text in self.texts:
            text: dict
            rendered = text["font"].return_text(text["text"], colours.darker(colours.GREEN, 130))
            rendered: pygame.Surface
            rendered.set_alpha(text["progress"])
            surface.blit(rendered, text["pos"])
        surface.blit(self.image, (x, y))

    def update(self, angle, dt):
        if angle < 45 and angle > -45:
            self.image_name = self.image_name.replace("l.png", "r.png")
            self.image_name = os.path.join(BASE_DIR, self.image_name)
        if angle < 180 and angle < -135 or angle < 180 and angle > 135:
            self.image_name = self.image_name.replace("r.png", "l.png")
            self.image_name = os.path.join(BASE_DIR, self.image_name)
        self.image = pygame.image.load(self.image_name)
        self.image = pygame.transform.scale_by(self.image, self.image_size)
        for text in self.texts:
            text: dict
            text["pos"].y -= 80 * dt
            if text["progress"] - dt * 63.75 > 0:
                text["progress"] -= dt * 63.75
            else:
                self.texts.remove(text)
            

    def copy(self):
        return copy.deepcopy(self)

    def equip(self, player):
        self.old_values = {}

        for effect in self.passive_effects:
            attribute = effect.effect_appending

            if attribute is not None:
                self.old_values[attribute] = getattr(player, attribute)

            effect.use(player, ())

        self.effected = True

    def unequip(self, player):
        if not self.effected:
            return

        for attribute, old_value in self.old_values.items():
            setattr(player, attribute, old_value)

        self.old_values.clear()
        self.effected = False

    def draw_copy(self, surface: pygame.Surface, x: int, y: int):
        surface.blit(self.image, (x, y))

    def use_active(self, player, dt):
        player: Player
        self.cooldown -= dt
        pos = pygame.mouse.get_pos()
        if pygame.mouse.get_pressed()[0] and self.cooldown <= 0:
            for effect in self.active_effects:
                effect: Effect
                effect.use(player, ())
                print(effect.appending)
            self.texts.append(
                {
                    "text": f"{'+' if Item.APPENDER in effect.flags else '-'}{effect.effect}{effect.effect_appending}",
                    "pos": pygame.Vector2(pos[0], pos[1]),
                    "progress": 255,
                    "font": userFont("arial", 50),
                    "font_conf": {"name": "arial", "size": 50}
                }
            )
            self.cooldown = self.or_cooldown

    def __getstate__(self):
        state = self.__dict__.copy()

        del state["image"]

        state["texts"] = []

        for text in self.texts:
            text_copy = text.copy()

            text_copy["font"] = None

            state["texts"].append(text_copy)

        return state

    def __setstate__(self, state):
        self.__dict__.update(state)

        self.image = pygame.image.load(self.image_name)
        self.image = pygame.transform.scale_by(
            self.image,
            self.image_size
        )

        for text in self.texts:
            text["font"] = userFont(
                text["font_conf"]["name"],
                text["font_conf"]["size"]
            )


class Bullet:
    def __init__(
        self,
        x, y,
        image_name: str,
        attack: int,
        speed,
        mx, my,
        range: float | int | None,
        material: str
    ):
        self.x = x
        self.y = y

        self.image_name = image_name
        self.image = pygame.image.load(self.image_name)

        self.angle = 360
        self.speed = speed

        self.rotated = None
        self.rotated_rect = None

        self.attack = attack
        self.material = material

        range_map = {
            MaterialFlags.BRONZE: 800,
            MaterialFlags.SILVER: 1200
        }

        print(material)

        self.range = range or range_map[material]
        self.travelled = 0

        self.mx = mx
        self.my = my

        self.deleted = False

        # Mouse yönünü hesapla
        dx = mx - x
        dy = my - y

        length = math.hypot(dx, dy)

        if length != 0:
            self.dir_x = dx / length
            self.dir_y = dy / length
        else:
            self.dir_x = 0
            self.dir_y = 0
    
    def get_mouse_pos(self):
        self.mx, self.my = pygame.mouse.get_pos()

    def update(self, world, dt, enemies: list):
        if self.mx is not None and self.my is not None:
            self.dx = self.mx - self.x
            self.dy = self.my - self.y
            self.angle = math.degrees(math.atan2(-self.dy, self.dx))

            self.image_rect = self.image.get_rect(center=(self.x, self.y))
            rect = self.rotated_rect or self.image_rect

            rect.topleft = (self.x, self.y)

            move_distance = self.speed * dt

            remaining = self.range - self.travelled

            if move_distance >= remaining:
                self.x += self.dir_x * remaining
                self.y += self.dir_y * remaining
                self.travelled = self.range
                self.deleted = True
            else:
                if rect.collidelist(world.rocks_rects) == -1:
                    self.x += self.dir_x * move_distance
                    self.y += self.dir_y * move_distance
                    self.travelled += move_distance
                else:
                    self.deleted = True

            for enemy in enemies:
                enemy: Enemy

                if rect.colliderect(enemy.image_rect) and enemy.living:
                    if Enemy.DAMAGE_BULLET in enemy.damagables or self.material == "__deflected__":
                        enemy.hp -= self.attack
                    else:
                        if (
                            Enemy.DAMAGE_BRONZE_BULLET in enemy.damagables
                            and self.material == MaterialFlags.BRONZE
                        ) or (
                            Enemy.DAMAGE_SILVER_BULLET in enemy.damagables
                            and self.material == MaterialFlags.SILVER
                        ):
                            enemy.hp -= self.attack

                    self.deleted = True
                    break

                for arrow in enemy.arrows:
                    arrow: Arrow
                    arrow_rect = arrow.rotated_rect or arrow.image_rect

                    if rect.colliderect(arrow_rect):
                        enemy.arrows.remove(arrow)
                        self.deleted = True
                        break

            self.rotated = pygame.transform.rotate(self.image, self.angle)
            self.rotated_rect = self.rotated.get_rect(center=(self.x, self.y))
    
    def draw(self, surface: pygame.Surface):
        if self.rotated is not None:
            surface.blit(self.rotated, self.rotated_rect)
        else:
            surface.blit(self.image, (self.x, self.y))
    
    def __getstate__(self):
        state = self.__dict__.copy()
        del state["image"]
        del state["rotated"]
        return state
    
    def __setstate__(self, state):
        self.__dict__.update(state)
        self.image = pygame.image.load(self.image_name)
        self.rotated = None


class Gun:
    def __init__(self, name: str, color: tuple, attack: int, bullet_speed: int, image_name: os.PathLike, bullet_name: os.PathLike, cooldown: int, material):
        self.name = name
        self.color = color
        self.attack = attack
        self.bullet_speed = bullet_speed
        self.image_name = image_name
        image = pygame.image.load(self.image_name)
        self.image = pygame.transform.scale_by(image, 0.5)
        self.bullet_name = bullet_name
        self.bullets = []
        self.rotated = None
        self.rotated_rect = None
        self.dash_duration = Cooldown(0.3)
        self.angle = 360
        self.x = None
        self.y = None
        self.origin_cooldown = cooldown
        self.cooldown = self.origin_cooldown
        self.dashing = False
        self.material = material
        print(material)

    def draw(self, surface: pygame.Surface, x: int, y: int):
        self.x = x
        self.y = y
        if self.rotated_rect is None and self.rotated is None:
            surface.blit(self.image, (x, y))
        else:
            surface.blit(self.rotated, self.rotated_rect)
        # if angle < 90 and angle > -90:
        #     self.image_name: str
        #     self.image_name = self.image_name.replace("l.png", "r.png")
        # else:
        #     self.image_name = self.image_name.replace("r.png", "l.png")
        image = pygame.image.load(self.image_name)
        self.image = pygame.transform.scale_by(image, 0.5)
        for bullet in self.bullets:
            bullet: Bullet
            bullet.draw(surface)
    
    def draw_copy(self, surface: pygame.Surface, x: int, y: int):
        surface.blit(self.image, (x, y))
    
    def update(self, world, dt, enemies: list, player):
        self.cooldown -= dt
        self.dash_duration.reduce(dt)

        if self.dash_duration.check():
            self.dashing = False
            player.drawing = False
            player.old_x = None
            player.old_y = None

        world: World
        mx, my = pygame.mouse.get_pos()
        if self.x is not None:
            dx, dy = mx - self.x, my - self.y
        else:
            return
        for bullet in self.bullets:
            bullet: Bullet
            bullet.update(world, dt, enemies)
            if bullet.deleted:
                self.bullets.remove(bullet)
        if not self.dashing:
            self.angle = math.degrees(math.atan2(-dy, dx))
        self.rotated = pygame.transform.rotate(self.image, self.angle)
        self.rotated_rect = self.rotated.get_rect(center=(self.x, self.y))

    def fire(self):
        if self.cooldown <= 0:
            if self.x is not None:
                print(self.material)
                self.bullets.append(
                    Bullet(
                        self.x,
                        self.y,
                        self.bullet_name,
                        self.attack,
                        self.bullet_speed,
                        pygame.mouse.get_pos()[0],
                        pygame.mouse.get_pos()[1],
                        None,
                        self.material
                    )
                )
            self.cooldown = self.origin_cooldown
    
    def dash_attack(self, player):
        player: Player

        if self.x is None: return

        mx, my = pygame.mouse.get_pos()
        dx, dy = mx - self.x, my - self.y
        self.angle = math.degrees(math.atan2(-dy, dx))
        self.dashing = True
        # if self.x is not None:
        #     if self.angle < 90 and self.angle > -90:
        #         self.angle = -90
        #     else:
        #        self.angle = 180
        self.angle = -90
        player.speed = player.speed_max + 130
        self.dash_duration.refresh()
        player.drawing = True
        self.rotated = pygame.transform.rotate(self.image, self.angle)
        self.rotated_rect = self.rotated.get_rect(center=(self.x, self.y))

    def __getstate__(self):
        state = self.__dict__.copy()

        del state["image"]
        if self.__dict__.get("rotated"):
            del state["rotated"]

        return state
    
    def __setstate__(self, state):
        self.__dict__.update(state)

        image = pygame.image.load(self.image_name)
        self.image = pygame.transform.scale(image, (image.get_width() / 2, image.get_height() / 2))
        self.rotated = None
        self.rotated_rect = None


class Effect:
    def __init__(self, effect_appending, effect, seconds: int, append_to_list: list=None, appending=[], flags: tuple = ()):
        self.effect = effect
        self.effect_appending = effect_appending
        self.append_to_list = append_to_list
        self.appending = appending
        self.seconds = seconds
        self.flags = flags
    
    def use_global(self, flags, varlik):
        if self.append_to_list is None:
            try:
                if Item.APPENDER in flags:
                    if self.seconds <= 0:
                        setattr(varlik, self.effect_appending, getattr(varlik, self.effect_appending)+self.effect)
                    else:
                        after(setattr, varlik, self.effect_appending, getattr(varlik, self.effect_appending)+self.effect, secs=self.seconds)
                if Item.EQUALER in flags:
                    if self.seconds <= 0:
                        setattr(varlik, self.effect_appending, self.effect)
                    else:
                        after(setattr, varlik, self.effect_appending, self.effect, secs=self.seconds)
                if Item.REDUCER in flags:
                    if self.seconds <= 0:
                        setattr(varlik, self.effect_appending, getattr(varlik, self.effect_appending)-self.effect)
                    else:
                        after(setattr, varlik, self.effect_appending, getattr(varlik, self.effect_appending)-self.effect, secs=self.seconds)
            except AttributeError:
                print(f"No attribute {self.effect_appending} in {varlik}")
        
        else:
            for append in self.appending:
                self.append_to_list.append(append)
    
    def use(self, player, flags):
        player: Player
        if self.append_to_list is None:
            if Item.APPENDER in flags or Item.APPENDER in self.flags:
                if self.seconds <= 0:
                    setattr(player, self.effect_appending, min(getattr(player, self.effect_appending)+self.effect, player.max_hp))
                else:
                    after(setattr, player, self.effect_appending, min(getattr(player, self.effect_appending)+self.effect, player.max_hp), secs=self.seconds)
            if Item.EQUALER in flags or Item.EQUALER in self.flags:
                if self.seconds <= 0:
                    setattr(player, self.effect_appending, self.effect)
                else:
                    after(setattr, player, self.effect_appending, self.effect, secs=self.seconds)
            if Item.REDUCER in flags or Item.REDUCER in self.flags:
                if self.seconds <= 0:
                    setattr(player, self.effect_appending, min(getattr(player, self.effect_appending)-self.effect, player.max_hp))
                else:
                    after(setattr, player, self.effect_appending, min(getattr(player, self.effect_appending)-self.effect, player.max_hp), secs=self.seconds)
        else:
            for append in self.appending:
                self.append_to_list.append(append)

    def copy(self):
        return copy.deepcopy(self)


class Item:
    APPENDER = 1
    EQUALER = 2
    REDUCER = 3
    YUVARLAK_IKSIR = 4
    TUP_IKSIR = 5

    def __init__(self, name: str, color: tuple, effects: list, *flags, pickable=None, font=None):
        self.name = name
        self.color = color
        self.effects = effects
        self.flags = flags
        print(f"FLAGS: {self.flags}")
        self.used = False
        self.pickable = pickable or True if self.YUVARLAK_IKSIR in self.flags else False
        self.picked = False
        self.touching = False
        self.drag_to_player = True
        self.mouse_getted = False
        self.effect_rect = None
        self.font = font
        self.use_timer_started = False
        if self.font is not None:
            self.font_name = self.font.name
            self.font_size = self.font.size
            self.font: userFont
        if self.YUVARLAK_IKSIR in self.flags:
            self.speed = 900
        print(self.flags)
    
    def set_pos(self, world, player):
        count = 0

        while True:
            count += 1

            if count > 50:
                print("ITEM YER BULAMADI", self.name)
                return

            self.x = random.randint(200, info.current_w - 200)
            self.y = random.randint(200, info.current_h - 200)

            self.rect = pygame.Rect(self.x, self.y, 20, 50)

            if self.rect.collidelist(world.rocks_rects) == -1 and not world.dirt_rect.colliderect(self.rect):
                print("item deneme:", count)
                break

    def draw(self, surface: pygame.surface.Surface, font: userFont, player):

        if not self.used:
            if not self.picked:
                if self.font is not None:
                    self.font: userFont
                    self.font.draw_text(self.name, (self.x+20, self.y-60), surface, colours.BLACK, hiza="center")
                else:
                    font.draw_text(self.name, (self.x+20, self.y-60), surface, colours.BLACK, hiza="center")
                if Item.TUP_IKSIR in self.flags:
                    pygame.draw.rect(surface, self.color, self.rect, border_radius=10)
                    pygame.draw.rect(surface, colours.WHITE, self.rect,5 ,border_radius=10)
                    pygame.draw.rect(surface, colours.BROWN, (self.x+5, self.y-3, 10, 15), border_radius=2)
                    pygame.draw.rect(surface, colours.darker(colours.BROWN, -20), (self.x+7, self.y-5, 5, 10))
                    pygame.draw.line(surface, colours.WHITE, (self.x+7, self.y+23), (self.x+10, self.y+13), 1)
                    pygame.draw.line(surface, colours.WHITE, (self.x+10, self.y+29), (self.x+13, self.y+19), 1)

                if Item.YUVARLAK_IKSIR in self.flags:
                    pygame.draw.circle(surface, self.color, (self.x, self.y), 20)
                    pygame.draw.circle(surface, colours.WHITE, (self.x, self.y), 20, 6)
                    pygame.draw.line(surface, colours.WHITE, (self.x+12, self.y-12), (self.x+25, self.y-23), 10)
                    pygame.draw.line(surface, colours.BROWN, (self.x+14, self.y-14), (self.x+27, self.y-25), 5)
                    pygame.draw.line(surface, colours.WHITE, (self.x-6, self.y+5), (self.x-1, self.y-8), 1)
                    pygame.draw.line(surface, colours.WHITE, (self.x, self.y+5), (self.x+4, self.y-8), 1)
            else:
                if self.drag_to_player:
                    self.x = player.x
                    self.y = player.y
                if Item.TUP_IKSIR in self.flags:
                    pygame.draw.rect(surface, self.color, self.rect, border_radius=10)
                    pygame.draw.rect(surface, colours.WHITE, self.rect,5 ,border_radius=10)
                    pygame.draw.rect(surface, colours.BROWN, (self.x+5, self.y-3, 10, 15), border_radius=2)
                    pygame.draw.rect(surface, colours.darker(colours.BROWN, -20), (self.x+7, self.y-5, 5, 10))
                    pygame.draw.line(surface, colours.WHITE, (self.x+7, self.y+23), (self.x+10, self.y+13), 1)
                    pygame.draw.line(surface, colours.WHITE, (self.x+10, self.y+29), (self.x+13, self.y+19), 1)

                if Item.YUVARLAK_IKSIR in self.flags:
                    pygame.draw.circle(surface, self.color, (self.x, self.y), 20)
                    pygame.draw.circle(surface, colours.WHITE, (self.x, self.y), 20, 6)
                    pygame.draw.line(surface, colours.WHITE, (self.x+12, self.y-12), (self.x+25, self.y-23), 10)
                    pygame.draw.line(surface, colours.BROWN, (self.x+14, self.y-14), (self.x+27, self.y-25), 5)
                    pygame.draw.line(surface, colours.WHITE, (self.x-6, self.y+5), (self.x-1, self.y-8), 1)
                    pygame.draw.line(surface, colours.WHITE, (self.x, self.y+5), (self.x+4, self.y-8), 1)
                if self.touching:
                    self.effect_rect = pygame.Rect(self.x, self.y, 200, 200)
                    self.effect_rect.center = (self.x, self.y)
                    pygame.draw.circle(surface, self.color, (self.x, self.y), 100, 4)
                    pygame.draw.rect(surface, self.color, self.effect_rect, 4, 100)

    def update(self, varliklar: list):
        if not self.used:
            if self.effect_rect is not None:
                for varlik in varliklar:
                    if self.effect_rect.colliderect(varlik.image_rect):
                        try:
                            for effect in self.effects:
                                effect: Effect
                                effect.use_global(self.flags, varlik)
                        except AttributeError:
                            print(f"No attribute {self.effect_appending} in {varlik}")
                        self.used = True

    def handle_event(self, event: pygame.event.Event):
        if self.picked and self.pickable:
            if event.type == pygame.MOUSEBUTTONDOWN and not self.mouse_getted:
                if event.button == 3:
                    self.drag_to_player = False
    
    def update_pos(self, dt):

        if not self.drag_to_player and not self.used:
            if not self.mouse_getted:
                self.mx, self.my = pygame.mouse.get_pos()
            self.mouse_getted = True

            self.dx = self.mx - self.x
            self.dy = self.my - self.y

            self.distance = math.hypot(self.dx, self.dy)
            if self.distance > 1.0:
                self.touching = False
                move_distance = self.speed * dt
                if move_distance >= self.distance:
                    self.x = self.mx
                    self.y = self.my
                    self.touching = True
                else:
                    self.x += (self.dx / self.distance) * move_distance
                    self.y += (self.dy / self.distance) * move_distance

            else:
                self.touching = True
        if not self.use_timer_started and self.touching and not self.used:
                self.use_timer_started = True
                # self.used = True
    
    def use(self, player):
        if not self.used and not self.pickable:
            for effect in self.effects:
                effect: Effect
                effect.use(player, self.flags)
            self.used = True
        if not self.picked:
            if not self.used and self.pickable:
                self.picked = True
                self.drag_to_player = True
    
    def copy(self):
        return copy.deepcopy(self)
    
    def __getstate__(self):
        state = self.__dict__.copy()

        if state["font"]:
            del state["font"]
        return state
    
    def __setstate__(self, state):
        self.__dict__.update(state)
        
        if not self.__dict__.get("font") and self.__dict__.get("font_name"):
            self.font = userFont(self.font_name, self.font_size)



class Player:
    def __init__(self, hp, using_gun: Sword, image_name: os.PathLike, speed_normal=400, speed_max=600):
        self.max_hp = 200
        self.hp = hp
        self.items = []
        self.using_gun = using_gun
        self.speed = speed_normal
        self.speed_normal = speed_normal
        self.speed_max = speed_max
        self.image_name = image_name
        self.image = pygame.image.load(self.image_name)
        self.image_rect = self.image.get_rect()
        self.rotated = None
        self.rotated_rect = None
        self.touching = False
        self._maximized = False
        self.change_angle = True
        self.angle = 360
        self.distance = None
        self.drawing = False
        self.teleport_drawing = False
        self.teleport_mx, self.teleport_my = None, None
        self.teleporting = False
        self.last_pressed = None
        self.damaged_cooldown = 0.6
        self.ability_healing = False
        self.available_guns = [self.using_gun]
        self.heal_cooldown_orig = 8
        self.heal_cooldown = self.heal_cooldown_orig
        self.sword_attacking = False
        self.hand_spot = 30
        self.sword_rect = None
        self.deflecting = False
        self.sword_angle = None
        self.cd_deflect = 0
        self.cd_deflect_orig = 2
        self.parlama_image_orig = pygame.image.load(os.path.join(BASE_DIR,r"images/parlama.png"))
        self.parlama_image = pygame.transform.scale_by(self.parlama_image_orig, 0.18)
        self.parlama_image2 = pygame.transform.scale_by(self.parlama_image_orig, 0.12)
        self.parlama_rect = None
        self.parlama_rect2 = None
        self.parlama_image_angle = 0
        self.parlama_image_angle2 = 0
        self.parlama_rotate_speed_conf = (
            1600,
            240
        )
        self.parlama_rotate_speed = 1600
        self.look_dir = "right"
        self.old_x = None
        self.old_y = None
        self.movable = True
        self.deflect_bullets = []

    def set_pos(self, world):
        world: World
        while True:
            x = random.randint(200, info.current_w - 200)
            y = random.randint(200, info.current_h - 200)
            self.image_rect = pygame.image.load(self.image_name).get_rect(topleft=(x, y))
            if not self.image_rect.collidelist(world.rocks_rects) != -1 and not self.image_rect.colliderect(world.dirt_rect):
                self.x = x
                self.y = y
                break

    def draw(self, surface: pygame.Surface):
        surface.blit(self.image, (self.x, self.y))
        if self.sword_rect is not None:
            pygame.draw.rect(surface, "red", self.sword_rect, 5)
        if self.deflecting:
            if self.parlama_rect is None: self.parlama_rect = self.parlama_image.get_rect()
            if self.parlama_rect2 is None: self.parlama_rect2 = self.parlama_image2.get_rect()
            if self.drawing or self.sword_attacking:
                if self.look_dir == "right":
                    self.parlama_rect.center = (self.x + 105, self.y)
                    self.parlama_rect2.center = (self.x + 80, self.y + 10)
                elif self.look_dir == "left":
                    self.parlama_rect.center = (self.x - 68, self.y)
                    self.parlama_rect2.center = (self.x - 50, self.y + 10)
            else:
                self.parlama_rect.center = (self.x + 20, self.y - 40)
                self.parlama_rect2.center = (self.x + 32, self.y - 25)
            center = self.parlama_rect.center
            center2 = self.parlama_rect2.center
            rotated = pygame.transform.rotate(
                self.parlama_image,
                self.parlama_image_angle
            )
            
            rotated2 = pygame.transform.rotate(
                self.parlama_image2,
                self.parlama_image_angle2
            )

            rect = rotated.get_rect(center=center)
            rect2 = rotated2.get_rect(center=center2)
            surface.blit(rotated, rect)
            surface.blit(rotated2, rect2)
        for bullet in self.deflect_bullets:
            bullet: Bullet
            bullet.draw(surface)

    def update(self, mouse_pos, world, dt, swidth: int, sheight: int, enemies: list):
        for bullet in self.deflect_bullets:
            bullet: Bullet
            bullet.update(world, dt, enemies)
            if bullet.deleted:
                self.deflect_bullets.remove(bullet)

        if not self.drawing:
            self.speed = self.speed_normal

        if self.movable:
            if type(self.using_gun) == Sword or type(self.using_gun) == Charm:
                if self.change_angle:
                    self.mx, self.my = mouse_pos

                    self.dx = self.mx - self.x
                    self.dy = self.my - self.y

                    self.distance = math.hypot(self.dx, self.dy)
                if not self.teleporting:
                    if int(self.distance) > 0:
                        self.touching = False
                        new_x = self.x + (self.dx / self.distance) * self.speed * dt
                        new_y = self.y + (self.dy / self.distance) * self.speed * dt
                        self.image_rect = pygame.image.load(self.image_name).get_rect(topleft=(new_x, new_y))
                        self.rect = pygame.image.load(self.image_name).get_rect(topleft=(new_x, new_y))
                        if self.rotated_rect is None:
                            if not self.image_rect.collidelist(world.rocks_rects) != -1 and not self.image_rect.colliderect(world.dirt_rect):
                                self.x += (self.dx / self.distance) * self.speed * dt
                                self.y += (self.dy / self.distance) * self.speed * dt
                        else:
                            self.rotated_rect.topleft = (new_x, new_y)
                            if not self.rotated_rect.collidelist(world.rocks_rects) != -1 and not self.rotated_rect.colliderect(world.dirt_rect):
                                self.x += (self.dx / self.distance) * self.speed * dt
                                self.y += (self.dy / self.distance) * self.speed * dt
                    else:
                        self.touching = True
                    if self.change_angle and not self.sword_attacking:
                        self.angle = math.degrees(math.atan2(-self.dy, self.dx))
                    if self.angle < 45 and self.angle > -45:
                        self.image_name = os.path.join(BASE_DIR,r"images/stickmanr.png")
                        self.look_dir = "right"
                    if self.angle < 180 and self.angle < -135 or self.angle < 180 and self.angle > 135:
                        self.image_name = os.path.join(BASE_DIR,r"images/stickmanl.png")
                        self.look_dir = "left"
                    self.image = pygame.image.load(self.image_name)
            elif type(self.using_gun) == Gun:
                if not self.drawing:
                    keys = pygame.key.get_pressed()
                    if keys[pygame.K_w]:
                        self.image_rect.center = (self.x, self.y - self.speed * dt)
                        if not self.image_rect.collidelist(world.rocks_rects) != -1 and not self.image_rect.colliderect(world.dirt_rect):
                            self.y = max(self.y - self.speed * dt, 0)
                            self.last_pressed = "w"
                    if keys[pygame.K_s]:
                        self.image_rect.center = (self.x, self.y + self.speed * dt)
                        if not self.image_rect.collidelist(world.rocks_rects) != -1 and not self.image_rect.colliderect(world.dirt_rect):
                            self.y = min(self.y + self.speed * dt, sheight)
                            self.last_pressed = "s"
                    if keys[pygame.K_d]:
                        self.image_rect.center = (self.x + self.speed * dt, self.y)
                        if not self.image_rect.collidelist(world.rocks_rects) != -1 and not self.image_rect.colliderect(world.dirt_rect):
                            self.x = min(self.x + self.speed * dt, swidth)
                            self.last_pressed = "d"
                        self.image_name = os.path.join(BASE_DIR,r"images/stickmanr.png")
                    if keys[pygame.K_a]:
                        self.image_rect.center = (self.x - self.speed * dt, self.y)
                        if not self.image_rect.collidelist(world.rocks_rects) != -1 and not self.image_rect.colliderect(world.dirt_rect):
                            self.x = max(self.x - self.speed * dt, 0)
                            self.last_pressed = "a"
                        self.image_name = os.path.join(BASE_DIR,r"images/stickmanl.png")
                    self.image = pygame.image.load(self.image_name)
                    self.image_rect = self.image.get_rect(center=(self.x, self.y))
                else:
                    if self.last_pressed is not None:
                        pressing = getattr(pygame, f"K_{self.last_pressed}")
                        if pressing == pygame.K_w:
                            self.image_rect.center = (self.x, self.y - self.speed * dt)
                            if not self.image_rect.collidelist(world.rocks_rects) != -1 and not self.image_rect.colliderect(world.dirt_rect):
                                self.y = max(self.y - self.speed * dt, 0)
                        if pressing == pygame.K_s:
                            self.image_rect.center = (self.x, self.y + self.speed * dt)
                            if not self.image_rect.collidelist(world.rocks_rects) != -1 and not self.image_rect.colliderect(world.dirt_rect):
                                self.y = min(self.y + self.speed * dt, sheight)
                        if pressing == pygame.K_d:
                            self.image_rect.center = (self.x + self.speed * dt, self.y)
                            if not self.image_rect.collidelist(world.rocks_rects) != -1 and not self.image_rect.colliderect(world.dirt_rect):
                                self.x = min(self.x + self.speed * dt, swidth)
                            self.image_name = os.path.join(BASE_DIR,r"images/stickmanr.png")
                        if pressing == pygame.K_a:
                            self.image_rect.center = (self.x - self.speed * dt, self.y)
                            if not self.image_rect.collidelist(world.rocks_rects) != -1 and not self.image_rect.colliderect(world.dirt_rect):
                                self.x = max(self.x - self.speed * dt, 0)
                            self.image_name = os.path.join(BASE_DIR,r"images/stickmanl.png")
                        self.image = pygame.image.load(self.image_name)
                        self.image_rect = self.image.get_rect(center=(self.x, self.y))
        
    def heal(self, dt):
        if self.ability_healing:
            self.heal_cooldown -= dt
            if self.heal_cooldown <= 0:
                self.hp = min(self.max_hp, self.hp + 10)
                self.heal_cooldown = self.heal_cooldown_orig

    def sword_attack(self, dt):
        if not type(self.using_gun) == Sword:
            return
        if pygame.mouse.get_pressed()[0]:
            self.sword_attacking = True
            self.change_angle = False
            if self.image_name == os.path.join(BASE_DIR,r"images/stickmanl.png"):
                self.hand_spot = -5
                

        if self.sword_attacking:
            if self.image_name == os.path.join(BASE_DIR,r"images/stickmanr.png"):
                self.sword_rect = pygame.Rect(self.x + self.hand_spot, self.y + 10, 70, self.image.get_height() - 10)
                self.hand_spot += 200 * dt
                if self.hand_spot > 70:
                    self.hand_spot = 30
                    self.sword_attacking = False
                    self.change_angle = True
                    self.sword_rect = None
            else:
                self.sword_rect = pygame.Rect(self.x - 5 - 70, self.y + 10, 70, self.image.get_height() - 10)
                self.hand_spot -= 200 * dt
                if self.hand_spot < -30:
                    self.hand_spot = 30
                    self.sword_attacking = False
                    self.change_angle = True
                    self.sword_rect = None

    def deflect(self, enemies: list, dt):
        if type(self.using_gun) != Sword: return
        keys = pygame.key.get_pressed()
        if keys[pygame.K_q] and not self.deflecting:
            self.deflecting = True
            self.cd_deflect = self.cd_deflect_orig
            self.parlama_rotate_speed = self.parlama_rotate_speed_conf[0]
    
        if self.deflecting:
            self.cd_deflect -= dt
            if self.cd_deflect > 0:
                for enemy in enemies:
                    enemy: Enemy
                    for arrow in enemy.arrows:
                        arrow: Arrow
                        arrow_rect = arrow.rotated_rect or arrow.image_rect
                        rect = pygame.Rect(self.x - 100, self.y - 100, 250, 250)
                        rect.center = (self.x, self.y)
                        if rect.colliderect(arrow_rect):
                            enemy.arrows.remove(arrow)
                            new_bullet = Bullet(self.x, self.y, arrow.image_name, arrow.attack * 3, arrow.speed + 700, enemy.x, enemy.y, 2000, "__deflected__",)
                            new_bullet.angle = math.degrees(math.atan2(-(enemy.y - self.y), (pygame.mouse.get_pos()[0] - self.x)))
                            new_bullet.rotated = pygame.transform.rotate(new_bullet.image, new_bullet.angle)
                            new_bullet.rotated_rect = new_bullet.rotated.get_rect(center=(new_bullet.x, new_bullet.y))
                            self.deflect_bullets.append(new_bullet)
                            self.deflecting = False
                            self.cd_deflect = 0
                self.parlama_image_angle += self.parlama_rotate_speed * dt
                self.parlama_image_angle2 += (self.parlama_rotate_speed + 600) * dt
                self.parlama_rotate_speed = max(self.parlama_rotate_speed_conf[1], self.parlama_rotate_speed - 800 * dt)
            else:
                self.deflecting = False

    def dash(self):
        if type(self.using_gun) == Sword:
            def reduce():
                nonlocal self
                if not self._maximized:
                    self.speed = self.speed_normal
                else:
                    self.speed = self.speed_max
                self.change_angle = True
                self.drawing = False
            self.old_x = self.x
            self.old_y = self.y
            self.speed += self.using_gun.dash_speed
            self.change_angle = False
            self.drawing = True
            self.damaged = False
            after(reduce, secs=0.2)
    
    def teleport(self, world):

        def go():
            nonlocal self
            self.x = self.teleport_mx
            self.y = self.teleport_my
            self.teleport_drawing = False
            self.teleporting = False

        if not self.teleporting:
            mx, my = pygame.mouse.get_pos()
            mouse_rect = pygame.Rect(mx, my, self.image.get_width(), self.image.get_height())
            if mouse_rect.collidelist(world.rocks_rects) != -1:
                print("TAŞA DEĞİYOR")
                return
            self.teleport_drawing = True
            self.teleport_mx = mx
            self.teleport_my = my
            after(go, secs=1.75)
        self.teleporting = True

    def draw_teleport(self, surface: pygame.Surface):
        if self.teleport_drawing:
            if self.teleport_mx is not None and self.teleport_my is not None:
                pygame.draw.circle(surface, colours.BLUE, (self.teleport_mx, self.teleport_my), 20, 3)
                pygame.draw.circle(surface, colours.LIGHT_BLUE, (self.teleport_mx, self.teleport_my), 8, 3)
    
    def draw_dash(self, surface: pygame.Surface):
        if self.drawing and type(self.using_gun) == Sword and self.old_x is not None and self.old_y is not None:
            draw_aa_line(surface, colours.WHITE, (int(self.old_x), int(self.old_y)), (int(self.x), int(self.y)), 5)
    
    def damage(self, enemies: list, dt, menu=False):
        if menu: return

        self.damaged_cooldown -= dt

        if type(self.using_gun) == Sword:
            if self.drawing:
                if self.damaged_cooldown <= 0:
                    for enemy in enemies:
                        enemy: Enemy
                        if Enemy.DAMAGE_SWORD_DASH in enemy.damagables:
                            if self.image_rect.colliderect(enemy.image_rect):
                                enemy.hp -= self.using_gun.attack
                                self.damaged_cooldown = 0.2

            elif self.sword_attacking:
                if self.damaged_cooldown <= 0:
                    for enemy in enemies:
                        enemy: Enemy
                        if Enemy.DAMAGE_SWORD in enemy.damagables:
                            if self.sword_rect.colliderect(enemy.image_rect) or self.image_rect.colliderect(enemy.image_rect):
                                enemy.hp -= self.using_gun.attack
                                enemy.recoil = 0.43
                                if self.image_name == os.path.join(BASE_DIR, r"images/stickmanr.png"):
                                    enemy.recoil_dir = "right"
                                elif self.image_name == os.path.join(BASE_DIR, r"images/stickmanl.png"):
                                    enemy.recoil_dir = "left"
                                self.damaged_cooldown = 0.2

        if type(self.using_gun) == Gun:
            if self.drawing:
                if self.damaged_cooldown <= 0:
                    for enemy in enemies:
                        enemy: Enemy
                        if Enemy.DAMAGE_BRONZE_GUN in enemy.damagables and self.using_gun.material == MaterialFlags.BRONZE or Enemy.DAMAGE_SILVER_GUN in enemy.damagables and self.using_gun.material == MaterialFlags.SILVER:
                            self.using_gun: Gun
                            if enemy.living:
                                if enemy.image_rect is not None and self.using_gun.rotated_rect is not None:
                                    if self.using_gun.rotated_rect.colliderect(enemy.image_rect):
                                        enemy.hp -= self.using_gun.attack + 12
                                        self.damaged_cooldown = 0.2
                                        break

    def reset(self, world, default_gun):
        self.max_hp = 200
        self.hp = 200
        self.items = []
        self.using_gun = default_gun
        self.set_pos(world)
        self.speed_normal = self.speed_normal
        self.speed_max = self.speed_max
        if self._maximized:
            self.speed = self.speed_max
        else:
            self.speed = self.speed_normal
        self.image = pygame.image.load(self.image_name)
        self.rotated = None
        self.rotated_rect = None
        self.touching = False
        self._maximized = False
        self.angle = 0
        self.available_guns.clear()
        self.available_guns.append(self.using_gun)
    
    def draw_statistics(self, surface: pygame.Surface, font: userFont, info):
        pygame.draw.rect(surface, colours.GRAY, (10, info.current_h-225, 200, 60), border_radius=20)
        percent = self.hp / self.max_hp
        pygame.draw.rect(surface, colours.RED, (10, info.current_h-225, 200 * percent, 60), border_radius=20)
        font.draw_text(f"Can: {self.hp}", (100, info.current_h-200), surface, colours.WHITE, hiza="center")
        if not self.ability_healing:
            font.draw_text(f"Silah: {self.using_gun.name}", (250, info.current_h-200), surface, colours.WHITE, hiza="midleft")
            font.draw_text(f"Hız: {int(self.speed / 100)}", (750, info.current_h-200), surface, colours.WHITE, hiza="midleft")
        else:
            percent_heal = self.heal_cooldown / self.heal_cooldown_orig

            full_rect = pygame.Rect(300, info.current_h-225, 200, 60)

            pygame.draw.rect(surface, colours.BLUE, full_rect, border_radius=20)
            pygame.draw.rect(surface, colours.GRAY, (300, info.current_h-225, 200 * percent_heal, 60), border_radius=20)

            font.draw_text(f"{self.heal_cooldown:.2f}", (full_rect.centerx, full_rect.centery), surface, colours.WHITE, "center")

            font.draw_text(f"Silah: {self.using_gun.name}", (550, info.current_h-200), surface, colours.WHITE, hiza="midleft")
            font.draw_text(f"Hız: {int(self.speed / 100)}", (1050, info.current_h-200), surface, colours.WHITE, hiza="midleft")

    def copy(self):
        return copy.deepcopy(self)
    
    def draw_available_guns(self, surface: pygame.Surface):
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        center = (info.current_w / 2, info.current_h / 2)
        self.center_wheel = center
        yari_cap = 400
        parca_sayisi = len(self.available_guns)
        aci = 360 / parca_sayisi
        pygame.draw.circle(surface, colours.BLACK, center, yari_cap, 10)
        if parca_sayisi > 1:
            for i, gun in enumerate(self.available_guns):
                orta_aci = i * aci + aci / 2

                radyan = math.radians(orta_aci)

                x = center[0] + math.cos(radyan) * yari_cap

                y = center[1] + math.sin(radyan) * yari_cap

                r = yari_cap * 0.65
                x2 = center[0] + math.cos(radyan) * r

                y2 = center[1] + math.sin(radyan) * r
                if type(gun) == Sword:
                    gun.draw(surface, int(x2), int(y2), angle=0, dashing=False)
                elif type(gun) == Gun:
                    gun.draw_copy(surface, int(x2), int(y2))
                elif type(gun) == Charm:
                    gun.draw(surface, int(x2), int(y2))

            for i in range(parca_sayisi):
                baslangic = math.radians(i * aci)
                bitis = math.radians((i + 1) * aci)

                noktalar = [center]

                # Yay boyunca noktalar oluştur
                derece = i * aci
                while derece <= (i + 1) * aci:
                    r = math.radians(derece)
                    x = center[0] + math.cos(r) * yari_cap
                    y = center[1] + math.sin(r) * yari_cap
                    noktalar.append((x, y))
                    derece += 2
                
                x = center[0] + math.cos(bitis) * yari_cap
                y = center[1] + math.sin(bitis) * yari_cap
                noktalar.append((x, y))
                pygame.draw.polygon(overlay, (255, 255, 255, 60), noktalar)


                pygame.draw.line(surface, colours.lighter(colours.BLACK, 50), center, (x, y), 2)
        else:
            self.available_guns[0].draw(surface, center[0], center[1], angle=0, dashing=False)
        surface.blit(overlay, (0, 0))

    def weapon_wheel_get_mouse(self, weapon_choosing: bool):
        if weapon_choosing:
            mx, my = pygame.mouse.get_pos()
            if self.center_wheel is None:
                return None
            dx = mx - self.center_wheel[0]
            dy = my - self.center_wheel[1]

            mesafe = math.hypot(dx, dy)
            if mesafe <= 400:
                aci = math.degrees(math.atan2(dy, dx))

                if aci < 0:
                    aci += 360

                secilen = int(aci // (360 / len(self.available_guns)))

                return secilen
        else:
            return None


    def __getstate__(self):
        state = self.__dict__.copy()
        if state.get("image"):
            del state["image"]
        state.pop("rotated", None)
        state.pop("rotated_rect", None)
        state.pop("parlama_image", None)
        state.pop("parlama_image2", None)
        state.pop("parlama_image_orig", None)
        
        return state
    
    def __setstate__(self, state):

        self.__dict__.update(state)
        self.image = pygame.image.load(self.image_name)
        self.rotated = None
        self.rotated_rect = None
        self.parlama_image_orig = pygame.image.load(os.path.join(BASE_DIR,r"images/parlama.png"))
        self.parlama_image = pygame.transform.scale_by(self.parlama_image_orig, 0.18)
        self.parlama_image2 = pygame.transform.scale_by(self.parlama_image_orig, 0.12)


class World:

    def __init__(self, terrain_color: tuple, rock0: tuple, rock1: tuple, items: list, terrain_image: os.PathLike=None, dirt_image: os.PathLike=None):
        self.rocks = []
        self.rocks_rects = []
        self.terrain_color = terrain_color
        self.rock0 = rock0
        self.rock1 = rock1
        self.rockChance = random.randint(3, 7)
        self.rockNum = random.randint(4, 10)
        self.items = copy.deepcopy(items)
        self.terrain_image_name = terrain_image
        if self.terrain_image_name:
            self.terrain_image = pygame.image.load(self.terrain_image_name)
            self.terrain_image = pygame.transform.scale(self.terrain_image, (info.current_w, info.current_w))
        else:
            self.terrain_image = None
        self.dirt_image_name = dirt_image
        if self.dirt_image_name:
            self.dirt_image = pygame.image.load(self.dirt_image_name)
            self.dirt_image = pygame.transform.scale(self.dirt_image, (info.current_w, info.current_h/5))
            self.dirt_rect = self.dirt_image.get_rect(topleft=(0, info.current_h/5*4))
        else:
            self.dirt_image = None

    def create_rocks(self, screen_x: int, screen_y: int):
        for _ in range(self.rockNum):
            deneme = 0
            uyarildi = False
            while True:
                deneme += 1
                rolled = random.randint(0, 10)
                x = random.randint(0, screen_x)
                y = random.randint(0, screen_y)

                width = random.randint(40, 200)
                height = random.randint(20, 100)

                rect = pygame.Rect(
                    x,
                    y,
                    width,
                    height
                )

                if not rect.colliderect(self.dirt_rect):

                    if rolled < self.rockChance:

                        rockData = {
                            "x": x,
                            "y": y,
                            "color": random.choice(
                                [self.rock0, self.rock1]
                            ),
                            "width": width,
                            "height": height,
                            "rect": rect
                        }

                        self.rocks.append(rockData)

                        # Aynı rect'i doğrudan ekle
                        self.rocks_rects.append(rect)

                        break
                if deneme > 10 and not uyarildi:
                    logging.warning("Creating rocks try exceed 10.")
                if deneme > 50:
                    logging.error("Creating rocks limit.")
                    break
    def draw(self, screen: pygame.Surface):
        if self.terrain_image_name:
            screen.blit(self.terrain_image, (0, 0))
        else:
            screen.fill(self.terrain_color)
        if self.dirt_image_name:
            screen.blit(self.dirt_image, (0, info.current_h/5*4))
        for rock in self.rocks:
            rockRect = pygame.Rect(rock["x"], rock["y"], rock["width"], rock["height"])
            pygame.draw.rect(screen, rock["color"], rockRect)
    
    def draw_items(self, surface: pygame.Surface, font: userFont, player):
        for item in self.items:
            item.draw(surface, font, player)

    def update(self, enemy_list: list):
        self.items = [
            item for item in self.items
            if not item.used
        ]
        enemy_list = [
            enemy for enemy in enemy_list
            if enemy.living
        ]
        return enemy_list

    def __getstate__(self):
        state = self.__dict__.copy()
        if state.get("terrain_image"):
            del state["terrain_image"]
        if state.get("dirt_image"):
            del state["dirt_image"]
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        if self.terrain_image_name:
            self.terrain_image = pygame.image.load(self.terrain_image_name)
            self.terrain_image = pygame.transform.scale(self.terrain_image, (info.current_w, info.current_w))
        if self.dirt_image_name:
            self.dirt_image = pygame.image.load(self.dirt_image_name)
            self.dirt_image = pygame.transform.scale(self.dirt_image, (info.current_w, info.current_h/5))


class Arrow:

    def __init__(self, x, y, image_name: str, attack=10):
        self.x = x
        self.y = y
        self.attack = attack
        self.rotated = None
        self.image_name = image_name
        self.image = pygame.image.load(self.image_name)
        self.image_rect = self.image.get_rect()
        self.rotated_rect = None
        self.touching = False
        self.angle = 360
        self.speed = 450

    def update(self, player: Player, dt):
    
        self.mx, self.my = player.x, player.y

        self.dx = self.mx - self.x
        self.dy = self.my - self.y

        self.distance = math.hypot(self.dx, self.dy)
        if self.distance > 2:
            new_x = self.x + (self.dx / self.distance) * self.speed * dt
            new_y = self.y + (self.dy / self.distance) * self.speed * dt
            self.image_rect = pygame.image.load(self.image_name).get_rect(topleft=(new_x, new_y))
            if self.rotated_rect is None:
                self.x += (self.dx / self.distance) * self.speed * dt
                self.y += (self.dy / self.distance) * self.speed * dt
            else:
                self.rotated_rect.topleft = (new_x, new_y)
                self.x += (self.dx / self.distance) * self.speed * dt
                self.y += (self.dy / self.distance) * self.speed * dt
        else:
            self.touching = True
        self.angle = math.degrees(math.atan2(-self.dy, self.dx))
        self.rotated = pygame.transform.rotate(self.image, self.angle)
        self.rotated_rect = self.rotated.get_rect(center=(self.x, self.y))
        if self.touching:
            player.hp -= self.attack
    def draw(self, surface: pygame.Surface):
        if self.rotated_rect is not None:
            surface.blit(self.rotated, self.rotated_rect)
        else:
            surface.blit(self.image, (self.x, self.y))
    
    def __getstate__(self):
        state = self.__dict__.copy()
        if state.get("image"):
            del state["image"]
            del state["rotated"]
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.image = pygame.image.load(self.image_name)


class Bomb:
    def __init__(self, attack, x, y, color=colours.YELLOW, radius=200, progress_per_sec = 23):
        self.attack = attack
        self.x = x
        self.y = y
        self.progress = 0
        self.color = color
        self.radius = radius
        self.progress_per_sec = progress_per_sec
        self.rect = None
        self.deleted = False

    def draw(self, surface: pygame.Surface):
        pygame.draw.circle(surface, self.color, (self.x, self.y), self.radius, 4)
        pygame.draw.circle(
            surface,
            colours.lighter(self.color, 40),
            (self.x, self.y),
            self.radius / 100 * self.progress
        )
        self.rect = pygame.Rect(0, 0, self.radius / 2, self.radius / 2)
        self.rect.center = (self.x, self.y)
    
    def update(self, player, dt):
        player: Player
        self.progress += self.progress_per_sec * dt
        if self.progress >= 100:
            if self.rect.colliderect(player.image_rect):
                player.hp -= self.attack
            self.deleted = True


class SplitGround:
    def __init__(self, attack: int, x, y, image_name: os.PathLike, angle: int, player_x, player_y, copy_cd=0.01):
        self.x = x
        self.y = y
        self.pos = (x, y)
        self.attack = attack
        self.image_name = image_name
        self.image = pygame.image.load(image_name).convert_alpha()
        self.image = pygame.transform.rotate(self.image, angle)
        self.angle = angle
        self.destroyed = False
        self.copy_cd = copy_cd
        self.orig_copy_cd = copy_cd
        self.player_x = player_x
        self.player_y = player_y
        self.copied = False
        self.speed = 700
        if not self.copied:
            self.copies = []
        else:
            self.copy_master = None
        self.image_rect = self.image.get_rect(midtop=(self.x, self.y))
        self.destroy_cd = 2.3
        dx = self.player_x - self.x
        dy = self.player_y - self.y
        distance = math.hypot(dx, dy)

        if distance != 0:
            self.vx = dx / distance
            self.vy = dy / distance
        else:
            self.vx = 0
            self.vy = 0
    
    def copy(self):
        return copy.deepcopy(self)

    def draw(self, surface: pygame.Surface):
        if not self.destroyed: surface.blit(self.image, self.image_rect)
        for sg in self.copies:
            sg: SplitGround
            sg.draw(surface)
    
    def update(self, dt):

        if self.destroyed:
            return

        self.destroy_cd -= dt

        if self.destroy_cd <= 0:
            self.destroyed = True
            return

        # Her frame hareket et
        self.x += self.vx * self.speed * dt
        self.y += self.vy * self.speed * dt

        self.image_rect.midtop = (
            self.x,
            self.y
        )

        # Kopya oluşturma süresi
        self.copy_cd -= dt

        if self.copy_cd <= 0:

            if len(self.copies) > 0:
                _self = self.copies[-1].copy()
            else:
                _self = self.copy()

            _self.copied = True
            _self.copy_master = self

            # Fırlatıldığı anda kaydedilmiş oyuncu konumuna göre
            # kopyanın başlangıç konumunu hesapla
            dx = self.player_x - self.x
            dy = self.player_y - self.y

            distance = math.hypot(dx, dy)

            if distance != 0:
                _self.x = self.x + (dx / distance) * 10
                _self.y = self.y + (dy / distance) * 10

            _self.image_rect = _self.image.get_rect(
                midtop=(_self.x, _self.y)
            )
            _self.angle = self.angle
            _self.image = pygame.transform.rotate(_self.image, _self.angle)

            self.copies.append(_self)

            self.copy_cd = self.orig_copy_cd
    
    def update_collision(self, player: Player):
        if player.image_rect.colliderect(self.image_rect):
            player.hp -= self.attack
            self.destroyed = True
            return
        else:
            for sg in self.copies:
                sg: SplitGround
                if not sg.copy_master.destroyed:
                    if player.image_rect.colliderect(sg.image_rect) and not sg.destroyed:
                        player.hp -= sg.attack
                        sg.destroyed = True
                        sg.copy_master.destroyed = True
                        del sg
                        break
                else:
                    sg.destroyed = True

    def __getstate__(self):
        state = self.__dict__.copy()

        del state["image"]

        return state
    
    def __setstate__(self, state):
        self.__dict__.update(state)
        self.image = pygame.image.load(self.image_name).convert_alpha()


class SCRLazerBeam:
    def __init__(self, attack, color: tuple[int, int, int], start_pos: tuple, end_pos: tuple):
        self.duration = Cooldown(1.4)
        self.attack = attack
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.color = color
        self.dark_color = colours.darker(self.color, 50)
        self.rect = None
        self.destroyed = False

    def draw(self, surface: pygame.Surface):
        if self.destroyed: return

        self.rect = pygame.draw.line(
            surface,
            self.color,
            self.start_pos,
            self.end_pos,
            info.current_w // 300
        )

        pygame.draw.line(
            surface,
            self.dark_color,
            self.start_pos,
            self.end_pos,
            int(info.current_w // 250 * (self.duration.cooldown / self.duration.durations[0]))
        )

    def update(self, player: Player, dt):
        self.duration.reduce(dt)

        if self.duration.check():
            self.destroyed = True
            return

        if self.rect is not None:
            if self.rect.colliderect(player.rect) and not self.destroyed:
                player.hp -= self.attack
                self.destroyed = True


class EnemyAbilities(Enum):
    ABILITY_BOMBING = auto()
    ABILITY_ARROWS = auto()
    ABILITY_SPLIT_GROUND = auto()
    ABILITY_CAT_JUMP = auto()
    ABILITY_SCR_LAZER_BEAM = auto()

print(type(EnemyAbilities.ABILITY_ARROWS))


class Enemy:
    enemies = []
    DAMAGE_SWORD_DASH = "4"
    DAMAGE_BULLET = "5"
    DAMAGE_BRONZE_BULLET = "6"
    DAMAGE_SILVER_BULLET = "7"
    DAMAGE_BRONZE_GUN = "8"
    DAMAGE_SILVER_GUN = "9"
    DAMAGE_SWORD = "10"
    
    def __init__(self, hp: int, attack: int, abilities: list = None, image_name: os.PathLike = os.path.join(BASE_DIR,"images/enemyr.png"), size = 100, speed=300, damage_cooldown: Cooldown=Cooldown(2), boss=False, after_max_hp=None, name=None, summons: list = [], cooldown: Cooldown = Cooldown(10), collisions=True, damagables=[DAMAGE_BULLET, DAMAGE_BRONZE_GUN, DAMAGE_SILVER_GUN, DAMAGE_SWORD_DASH, DAMAGE_SWORD], cooldown_arrow: Cooldown = None, bagimsiz_summons=[], cooldown_bagimsiz_summons: Cooldown=Cooldown(10), arrow_image=os.path.join(BASE_DIR,r"images/arrow.png"), drops=[]):
        self.hp = hp
        self.x = None
        self.y = None
        self.name = name or ""
        self.origin_hp = hp
        self.attack = attack
        self.living = True
        self.image_name = image_name
        self.size = size
        self.image = pygame.image.load(image_name)
        self.image = pygame.transform.smoothscale(self.image, (int(self.image.get_width() * self.size / 100), int(self.image.get_height() * self.size / 100)))
        self.speed = speed
        self.image_rect = self.image.get_rect()
        self.rotated_rect = None
        self.angle = 0
        self.damaged = False
        self.damage_cooldown = damage_cooldown
        self.boss = boss
        self.abilities = abilities if abilities is not None else []

        assert type(self.abilities) == list, f"{self}.abilities is not list"
        print("Enemy abilities:", self.abilities)
        print("Type:", type(self.abilities))
        self.arrow_image_name = arrow_image
        self.arrow_image = pygame.image.load(self.arrow_image_name)
        self.rotated_rect_arrow = self.arrow_image.get_rect()
        self.arrows = []
        self.origin_cooldown = cooldown
        self.cooldown = self.origin_cooldown
        self.arrow_cooldown = cooldown_arrow
        self.summon_cooldown = self.origin_cooldown
        self.summoned = False
        self.bombing_cooldown = self.origin_cooldown + 3
        self.split_ground_cd = self.origin_cooldown + 2
        self.cat_jump_cd = self.origin_cooldown + 4
        self.scr_lazer_beam_cd = self.origin_cooldown + 6
        self.cat_jumping = False
        self.bombs = []
        if self.boss:
            self.after_max_hp = after_max_hp
            self.summons = summons
        self.collisions = collisions
        self.damagables = damagables
        self.bagimsiz_summons = bagimsiz_summons
        self.bsummons_cooldown = cooldown_bagimsiz_summons
        self.drops = drops
        self.id = str(uuid.uuid4())
        self.sgrounds: list[SplitGround] = []
        self.recoil = 0
        self.recoil_dir = None
        self.cat_jumping_y_dir = "up"
        self.c_jump_player_pos = None
        self.c_jumping_duration = Cooldown(2)
        self.c_jump_dx = None
        self.scr_lazers: list[SCRLazerBeam] = []

    def set_pos(self, world, info):
        for _ in range(1000):
            x = random.randint(200, info.current_w - 200)
            y = random.randint(200, info.current_h - 200)

            rect = pygame.Rect(x, y, self.image.get_width(), self.image.get_height())

            if rect.collidelist(world.rocks_rects) == -1 and not rect.colliderect(world.dirt_rect):
                self.x = x
                self.y = y
                return
        level = "Unknown"

        for name, variable in globals().items():
            if isinstance(variable, dict):
                for in_var in variable.values():
                    if in_var == world:
                        level = variable.get("Level", "Unknown")

        raise EnemyPositionError(self.name, _, level)
    
    def update_arrows(self, player: Player, dt):
        for arrow in self.arrows:
            arrow: Arrow
            arrow.update(player, dt)
            if arrow.touching:
                self.arrows.remove(arrow)
                del arrow
    
    def update_bombs(self, player: Player, dt):
        for bomb in self.bombs:
            bomb: Bomb
            bomb.update(player, dt)
            if bomb.deleted:
                self.bombs.remove(bomb)
    
    def update_sgrounds(self, player: Player, dt):
        for sg in self.sgrounds:
            sg: SplitGround
            sg.update(dt)
            sg.update_collision(player)

    def update_cat_jump(self, player: Player, dt):
        if self.cat_jumping:
            self.c_jumping_duration.reduce(dt)

            if self.c_jumping_duration.check():
                self.cat_jumping = False
                player.movable = True
                return

            if self.cat_jumping_y_dir == "up":
                self.y -= 200 * dt
            elif self.cat_jumping_y_dir == "down":
                self.y += 200 * dt

            dx = self.c_jump_player_pos[0] - self.x

            if abs(self.c_jump_dx / 2) > abs(dx):
                self.cat_jumping_y_dir = "down"
            
            self.x += 850 * dt if dx > 0 else -850 * dt

            self.image_rect = self.image.get_rect(topleft=(self.x, self.y))
            self.rect = self.image.get_rect(topleft=(self.x, self.y))

            if player.image_rect.colliderect(self.image_rect):
                player.movable=False
                player.hp -= int(30 * dt)

    def update_scr_lazers(self, player: Player, dt):
        for scr_l_b in self.scr_lazers:
            scr_l_b.update(player, dt)
    
    def draw_arrows(self, surface: pygame.Surface):
        for arrow in self.arrows:
            arrow.draw(surface)
    
    def draw_bombs(self, surface: pygame.Surface):
        for bomb in self.bombs:
            bomb: Bomb
            bomb.draw(surface)
    
    def draw_sgrounds(self, surface: pygame.Surface):
        for sg in self.sgrounds:
            sg: SplitGround
            sg.draw(surface)

    def draw_scr_lazers(self, surface: pygame.Surface):
        for scr_l_b in self.scr_lazers:
            scr_l_b.draw(surface)
    
    def use_arrow(self, dt):
        if self.arrow_cooldown is not None:
            if EnemyAbilities.ABILITY_ARROWS in self.abilities and self.living:
                self.arrow_cooldown.reduce(dt)
                if self.arrow_cooldown.check():
                    self.arrows.append(Arrow(
                        self.x,
                        self.y,
                        self.arrow_image_name
                    ))
                    self.arrow_cooldown.refresh()
        else:
            if EnemyAbilities.ABILITY_ARROWS in self.abilities and self.living:
                self.cooldown.reduce(dt)
                if self.cooldown.check():
                    self.arrows.append(Arrow(
                        self.x,
                        self.y,
                        self.arrow_image_name
                    ))
                    self.cooldown.refresh()
    
    def use_bombing(self, dt, player: Player):
        if EnemyAbilities.ABILITY_BOMBING in self.abilities and self.living:
            self.bombing_cooldown.reduce(dt)
            if self.bombing_cooldown.check():
                self.bombs.append(
                    Bomb(
                        24,
                        player.x,
                        player.y
                    )
                )
                self.bombing_cooldown.refresh()
    def use_split_ground(self, dt, player: Player):
        if self.living:
            if EnemyAbilities.ABILITY_SPLIT_GROUND in self.abilities:
                mx, my = player.x, player.y
                dx, dy = self.x - mx, self.y - my
                self.split_ground_cd.reduce(dt)
                if self.split_ground_cd.check():
                    self.sgrounds.append(
                        SplitGround(
                            46,
                            self.x,
                            self.y,
                            os.path.join(BASE_DIR,r"images/splitground_noback.png"),
                            math.degrees(math.atan2(-dy, dx)),
                            player.x,
                            player.y

                        )
                    )
                    self.split_ground_cd.refresh()
    def use_cat_jump(self, dt, player: Player):
        if self.living:
            if EnemyAbilities.ABILITY_CAT_JUMP in self.abilities:
                self.cat_jump_cd.reduce(dt)

                if self.cat_jump_cd.check():
                    self.c_jump_player_pos = (player.x, player.y)
                    self.cat_jumping = True
                    self.c_jump_dx = self.c_jump_player_pos[0] - self.x
                    self.c_jumping_duration.refresh()
                    self.cat_jump_cd.refresh()

    def use_scr_lazer_beam(self, dt):
        if self.living:
            if EnemyAbilities.ABILITY_SCR_LAZER_BEAM in self.abilities:
                self.scr_lazer_beam_cd.reduce(dt)

                if self.scr_lazer_beam_cd.check():
                    for _ in range(5):
                        self.scr_lazers.append(
                            SCRLazerBeam(
                                5,
                                colours.lighter(colours.BLUE, 75),
                                (0, random.randint(0, info.current_h)),
                                (info.current_w, random.randint(0, info.current_h))
                            )
                        )

                    self.scr_lazer_beam_cd.refresh()

    def copy(self):
        return copy.deepcopy(self)

    def summon(self, dt, level: list, world):
        self.bsummons_cooldown.reduce(dt)
        level = list(level)
        if self.__dict__.get("summons"):
            if self.living:
                _withoutself = copy.deepcopy(level)
                try:
                    if all(not enemy.summoned for enemy in level) or self.summon_cooldown.check() and all(enemy.summoned for enemy in _withoutself):
                        self.summon_cooldown.reduce(dt)
                        if self.summon_cooldown.check():
                            for summoning in self.summons:
                                summoning: Enemy
                                new_enemy = summoning.copy()
                                new_enemy.summoned = True
                                new_enemy.set_pos(world, info)
                                level.append(new_enemy)
                            self.summon_cooldown.refresh()
                except TypeError:
                    pass
        if self.living:
            if self.bsummons_cooldown.check():
                for summoning in self.bagimsiz_summons:
                    summoning: Enemy
                    new_enemy = summoning.copy()
                    new_enemy.set_pos(world, info)
                    level.append(new_enemy)
                self.bsummons_cooldown.refresh()

    @staticmethod
    def draw(surface: pygame.Surface, font: userFont, level: list, bossFont: userFont = None):
        bosses=[]
        padding = 160
        for enemy in level:
            enemy: Enemy
            if enemy.living:
                if enemy.boss:
                    bosses.append(enemy)
                else:
                    font.draw_text(str(enemy.hp), (enemy.x+enemy.image.get_width()/2, enemy.y-10), surface, colours.BLACK, hiza="center")
                surface.blit(enemy.image, (enemy.x, enemy.y))
        for i, enemy in enumerate(bosses):
            if i>1:
                continue
            bossFont = bossFont or font
            font.draw_text(enemy.name, (info.current_w/2, 50+i*(padding)), surface, colours.BLACK, hiza="center")
            pygame.draw.rect(surface, colours.GRAY, (100, 100+i*padding, info.current_w-200, 100), border_radius=20)
            percent = enemy.hp / enemy.origin_hp
            pygame.draw.rect(surface, colours.RED, (100, 100+i*padding, (info.current_w-200) * percent, 100), border_radius=20)
            bossFont.draw_text(f"{enemy.origin_hp}/{enemy.hp}", (info.current_w/2, 150+i*padding), surface, colours.BLACK, hiza="center")
    
    @classmethod
    def default(cls):
        return cls(100, 10, [])
    
    @classmethod
    def miguel(cls):
        return cls(
            500,
            70,
            [EnemyAbilities.ABILITY_BOMBING],
            os.path.join(BASE_DIR,r"images/miguelr.png"),
            speed=270,
            damagables=[Enemy.DAMAGE_SWORD_DASH, Enemy.DAMAGE_SILVER_BULLET],
            drops=[Item("Miguel'in Kanı", colours.RED, [Effect("hp", 15, -1)], Item.YUVARLAK_IKSIR, Item.APPENDER)],
            size=60
        )

    @classmethod
    def luffy(cls):
        return cls(
            300,
            25,
            image_name=os.path.join(BASE_DIR,r"images/luffyr.png"),
            speed=420,
            damagables=[Enemy.DAMAGE_SWORD_DASH],
            size=8
        )
    
    @classmethod
    def dinosaur(cls):
        return cls(
            1000,
            120,
            image_name=os.path.join(BASE_DIR,r"images/urasr.png"),
            speed=210,
            size=40,
            abilities=[EnemyAbilities.ABILITY_SPLIT_GROUND],
            collisions=False,
            cooldown=Cooldown(1)
        )

    @classmethod
    def skzoo(cls, player=None, special=False):
        player: Player
        return cls(
            700,
            50,
            image_name=os.path.join(BASE_DIR,r"images/denizinseyir.png"),
            speed=350,
            size=12,
            abilities=[],
            damagables=[Enemy.DAMAGE_SWORD_DASH, Enemy.DAMAGE_BRONZE_GUN, Enemy.DAMAGE_SILVER_GUN],
            drops=[Effect("hp", 0, -1, player.available_guns, [Charm("Deniz'in şeyi", os.path.join(BASE_DIR,r"images/denizinseyir.png"), 0.09, [Effect("heal_cooldown_orig", 0.75, -1, flags=(Item.EQUALER,))], [Effect("hp", 15, -1, flags=(Item.APPENDER,))], 0.45)], (Item.APPENDER))] if special else []
        )

    @classmethod
    def floppa(cls):
        return cls(
            250,
            14,
            image_name=os.path.join(BASE_DIR, r"images/floppa.png"),
            speed = 450,
            abilities=[EnemyAbilities.ABILITY_CAT_JUMP],
            damagables = [Enemy.DAMAGE_SWORD_DASH, Enemy.DAMAGE_BRONZE_GUN, Enemy.DAMAGE_BRONZE_BULLET],
            size = 45
        )

    @classmethod
    def demirbt(cls):
        return cls(
            10_000,
            200,
            image_name=os.path.join(BASE_DIR, r"images/demirboklutf.png"),
            size=30,
            abilities=[EnemyAbilities.ABILITY_BOMBING, EnemyAbilities.ABILITY_SCR_LAZER_BEAM],
            boss=True,
            name="Demirin Boklu Telefonu",
            damage_cooldown = Cooldown(3.4),
            cooldown=Cooldown(7),
            summons=[Enemy.miguel(), Enemy.miguel(), Enemy.luffy()],
            after_max_hp = 2000,
            collisions=False
        )

    def update(self, player: Player, world: World, dt, level: list):


        if not self.cat_jumping:


            self.mx, self.my = player.x, player.y
            if self.recoil > 0:

                if self.recoil_dir == "right":
                    new_x = self.x + (self.speed + 500) * dt
                elif self.recoil_dir == "left":
                    new_x = self.x - (self.speed + 500) * dt
                self.image_rect = self.image.get_rect(topleft=(new_x, self.y))
                if not self.image_rect.collidelist(world.rocks_rects) != -1 or not self.collisions:
                    self.x = new_x
                self.recoil -= 1 * dt

            try:
                self.dx = self.mx - self.x
                self.dy = self.my - self.y
            except TypeError:
                self.set_pos(world, info)
                self.dx = self.mx - self.x
                self.dy = self.my - self.y

            self.distance = math.hypot(self.dx, self.dy)

            if self.distance > 0:

                new_x = self.x + (self.dx / self.distance) * self.speed * dt
                new_y = self.y + (self.dy / self.distance) * self.speed * dt
                self.image_rect = self.image.get_rect(topleft=(new_x, new_y))
                self.rect = self.image.get_rect(topleft=(new_x, new_y))
        
                if self.rotated_rect is None:
                    if not self.image_rect.collidelist(world.rocks_rects) != -1 or not self.collisions:
                        self.x += (self.dx / self.distance) * self.speed * dt
                        self.y += (self.dy / self.distance) * self.speed * dt
                
                else:
                    self.rotated_rect.topleft = (new_x, new_y)
                    if not self.rotated_rect.collidelist(world.rocks_rects) != -1 or not self.collisions:
                        self.x += (self.dx / self.distance) * self.speed * dt
                        self.y += (self.dy / self.distance) * self.speed * dt

            else:
                self.touching = True
        self.angle = math.degrees(math.atan2(-self.dy, self.dx))
        old_image_name = self.image_name

        if -45 < self.angle < 45:
            self.image_name = self.image_name.replace("l.png", "r.png")

        elif self.angle < -135 or self.angle > 135:
            self.image_name = self.image_name.replace("r.png", "l.png")

        if self.image_name != old_image_name:
            self.image = pygame.image.load(os.path.join(BASE_DIR,self.image_name)).convert_alpha()
            self.image = pygame.transform.smoothscale(
                self.image,
                (
                    int(self.image.get_width() * self.size / 100),
                    int(self.image.get_height() * self.size / 100)
                )
            )
        self.update_sgrounds(player, dt)
        self.sgrounds = [sg for sg in self.sgrounds if not sg.destroyed]
        self.scr_lazers = [scr_lazer for scr_lazer in self.scr_lazers if not scr_lazer.destroyed]
        if self.hp <= 0:
            self.living = False
            self.summoned = False
            self.drops: list
            for drop in self.drops:
                if type(drop) == Sword or type(drop) == Gun:
                    player.available_guns.append(drop)
                elif type(drop) == Item:
                    drop.set_pos(world, player)
                    world.items.append(drop)
                elif type(drop) == Effect:
                    drop.use(player, ())
                elif type(drop) == Enemy:
                    level.append(drop)
            self.drops.clear()
            if self.boss:
                if self.after_max_hp is not None:
                    player.max_hp = self.after_max_hp
                self.after_max_hp = None
            return
    
    @classmethod
    def create_boss(cls, hp, attack, name: str, after_max_hp: int, cooldown: Cooldown = Cooldown(10), abilities: list = [], summons: list = [], image_name = os.path.join(BASE_DIR,r"images/enemyr.png")):
        return cls(hp, attack, boss=True, name=name, after_max_hp=after_max_hp, cooldown=cooldown, abilities=abilities, summons=summons, image_name=image_name)
    
    @classmethod
    def prepared_police(cls):
        return cls(
        450,
        34,
        image_name=os.path.join(BASE_DIR,r"images/enemy_policer.png"),
        size=120,
        speed=280,
        damage_cooldown=Cooldown(1.7),
        damagables=[
            Enemy.DAMAGE_BRONZE_GUN,
            Enemy.DAMAGE_SILVER_GUN,
            Enemy.DAMAGE_SWORD_DASH,
            Enemy.DAMAGE_SILVER_BULLET
        ]
    )

    @classmethod
    def prepared_old(cls, random_speed=False, hp=40):
        if random_speed:
            speed = random.randint(350, 380)

        return cls(
            hp,
            2,
            image_name=os.path.join(BASE_DIR,r"images/enemy_oldr.png"),
            size=89,
            speed=speed if random_speed else 360,
            damage_cooldown=Cooldown(2.1),
            damagables=[
                Enemy.DAMAGE_BULLET,
                Enemy.DAMAGE_BRONZE_GUN,
                Enemy.DAMAGE_SILVER_GUN,
                Enemy.DAMAGE_SWORD_DASH
            ]
        )

    def damage(self, player: Player, dt):
        self.damage_cooldown.reduce(dt)

        if self.damage_cooldown.check():
            self.damaged = False

        if not self.damaged and self.living:
            if not player.drawing and not player.sword_attacking:
                if self.image_rect.colliderect(player.image_rect):
                    player.hp -= self.attack
                    self.damaged = True
                    self.damage_cooldown.refresh()

    def reset(self, world: World):
        self.set_pos(world, info)
        self.living = True
        self.hp = self.origin_hp
        self.recoil = 0
        self.recoil_dir = None

    def __getstate__(self):
        state = self.__dict__.copy()
        if state.get("image"):
            del state["image"]
            del state["arrow_image"]
        
        return state
    
    def __setstate__(self, state):
        self.__dict__.update(state)
        self.image = pygame.image.load(self.image_name)
        self.image = pygame.transform.smoothscale(self.image, (int(self.image.get_width() * self.size / 100), int(self.image.get_height() * self.size / 100)))
        self.arrow_image = pygame.image.load(self.arrow_image_name)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


logging.info("Created classes.")
item1 = Item("Zıkkımın Kökü", colours.GREEN, 20, "hp", 20, Item.REDUCER, Item.TUP_IKSIR)
item_map = {
    "item1": Item("Can İksiri", colours.RED, [Effect("hp", 20, -1)], Item.APPENDER, Item.TUP_IKSIR),
    "item2": Item("Ölüm İksiri", colours.BLUE, [Effect("hp", 20, -1)], Item.YUVARLAK_IKSIR, Item.REDUCER, pickable=True)
}

level1 = [
    Enemy(100, 5, image_name=os.path.join(BASE_DIR,r"images/enemyr.png"))
]


defaults = {
    "Player": Player(200, Sword("Tahta Kılıç", 15, colours.BROWN, 700, MaterialFlags.WOODEN), os.path.join(BASE_DIR, r"images/stickmanr.png")),
    "World": World(colours.darker(colours.GREEN, 75), colours.YELLOW, colours.darker(colours.YELLOW, 40), list(item_map[item] for item in item_map.keys()), os.path.join(BASE_DIR,"images/green_pattern.png"), os.path.join(BASE_DIR,"images/dirt_pattern.png")),
    "Level": "level1",
    "Win": False,
    "EnemyData": {}
}
logging.info("Created reference defaults.")
for enemy in level1:
    defaults["EnemyData"][enemy.id] = enemy
print(defaults["EnemyData"])

defaults["Player"].set_pos(defaults["World"])
for item in defaults["World"].items:
    item.set_pos(defaults["World"], defaults["Player"])

for enemy in globals()[defaults["Level"]]:
    enemy.set_pos(defaults["World"], info)

# hileli silah
# defaults["Player"].available_guns.append(Gun("At Kafası", colours.lighter(colours.BLACK, 30), 40, 800, os.path.join(BASE_DIR,r"images/silver_silahr.png"), os.path.join(BASE_DIR,r"images/silver_silah_mermi.png"), 0.03, MaterialFlags.SILVER))

def reset(screen_x: int, screen_y: int, game: dict):
    logging.info("Called reset.")
    global defaults
    del game["World"]
    game["World"] = World(colours.darker(colours.GREEN, 75), colours.YELLOW, colours.darker(colours.YELLOW, 40), [], terrain_image=os.path.join(BASE_DIR,"images/green_pattern.png"), dirt_image=os.path.join(BASE_DIR,"images/dirt_pattern.png"))
    game["Level"] = "level1"
    for enemy in globals()[game["Level"]]:
        enemy: Enemy
        enemy.reset(game["World"])
    game["World"].create_rocks(screen_x, screen_y)
    for item in item_map.values():
        new_item = item.copy()

        new_item.used = False
        new_item.picked = False
        new_item.touching = False
        new_item.drag_to_player = True
        new_item.mouse_getted = False
        new_item.effect_rect = None

        game["World"].items.append(new_item)
    for item in game["World"].items:
        item.used = False
        item.picked = False
        item.touching = False
        item.drag_to_player = True
        item.mouse_getted = False
        item.effect_rect = None
        item.set_pos(game["World"], game["Player"])
    for item in game["World"].items:
        print(item.name, id(item))
    game["Player"].reset(
    game["World"],
    Sword("Tahta Kılıç", 15, colours.BROWN, 700, MaterialFlags.WOODEN)
    )
    logging.info("Reseted variables successfully.")
    logger.debug(str(game))
    print("PLAYER")
    print(id(game["Player"]))
    print("WORLD")
    print(id(game["World"]))
    print("USING GUN")
    print(id(game["Player"].using_gun))
    print(type(game["Player"].using_gun))
    print("AVAILABLE GUNS")
    print(len(game["Player"].available_guns))

    for gun in game["Player"].available_guns:
        print(gun.name, id(gun), type(gun))
    print("PLAYER DICT")
    for key, value in game["Player"].__dict__.items():
        print(key, type(value))
    game["Player"]=Player(200, Sword("Tahta Kılıç", 15, colours.BROWN, 700, MaterialFlags.WOODEN), os.path.join(BASE_DIR,r"images/stickmanr.png"))
    game["Player"].set_pos(game["World"])
    return game
