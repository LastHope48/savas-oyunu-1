import pygame
import sys
import colours
from save_manager import SaveManager
import math
from settings_manager import SettingsManager
import os
import classes
import random
import arabic_reshaper
from bidi.algorithm import get_display
import _pickle
import subprocess
import logging
import copy
from exceptions import InvalidGameStateError
from console import CommandParser, Console
from pass_manager import HashManager
from flags import SUCCESS, FAILURE


GAME_VERSION = "2.0"
SUDOPASS = r"koalfret4938(poxz)"
save_manager = SaveManager()
settings_manager = SettingsManager(
    "settings",
    "settings",
    "TEST",
    GAME_VERSION
)
hash_manager = HashManager()

hash_manager.write(SUDOPASS)

command = CommandParser()
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(filename)s: %(lineno)d [%(funcName)s] | %(message)s',
    filename="game.log"
)

command.add_variable("dt_multiplier", 1)



dt_multiplier = 1

def multiply_dt(value):
    global dt_multiplier
    dt_multiplier = value
    command.variables["dt_multiplier"] = value
    return SUCCESS, f"Oyun {dt_multiplier} kat daha hızlı."

command.add_command("dt", multiply_dt, [float], success_text="Delta Time multiplied to [arg1]")
command.add_command("setattr", settings_manager.write_attribute, [str, str], success_text="[arg1] settings attribute changed to [arg2]")
settings_manager.create()
settings_manager.repair_health()
debug = settings_manager.get_attribute("DEBUG")
run = True

pygame.init()
pygame.mixer.init()

logging.info("Pygame initialized successfully.")
info = pygame.display.Info()
screen = pygame.display.set_mode((800, 800), pygame.RESIZABLE)
pygame.display.set_caption("Öz Hakiki GTA 7")
GAME_STATE = "MENU"
logging.info("Screen initialized successfully.")
class userFont:
    fonts = []

    def __init__(self, name: str, size: int, bold=False, italic=False):
        self.name = name
        self.size = size
        self.bold = bold
        self.italic = italic
        size_name_map = {
            0: {"name": "so small", "size": "0-10"},
            1: {"name": "small", "size": "10-20"},
            2: {"name": "mid", "size": "20-30"},
            3: {"name": "big", "size": "30-40"},
            4: {"name": "so big", "size": "40-50"},
            5: {"name": "huge", "size": "50-80"},
            6: {"name": "başlık", "size": "80-160"}
        }
        for index in size_name_map.keys():
            if self.size >= int(size_name_map[index]["size"].split("-")[0]) and self.size <= int(size_name_map[index]["size"].split("-")[1]):
                self.size_name = size_name_map[index]["name"]
        if os.path.exists(name):
            self.font = pygame.font.Font(name, size)
        else:
            self.font = pygame.font.SysFont(self.name, self.size, self.bold, self.italic)
        self.fonts.append(self)

    def return_text(self, text: str, color: tuple, background: tuple = None, antialias=True):
        return self.font.render(text, antialias, color, background)

    def draw_text(self, text: str, pos: tuple, surface: pygame.Surface, color: tuple, hiza: str = None, background: tuple = None, antialias=True):
        rendered = self.return_text(text, color, background, antialias)
        if hiza is not None:
            rect = rendered.get_rect()
            if not hasattr(rect, hiza):
                raise ValueError(f"Geçersiz hiza: {hiza}")
            setattr(rect, hiza, pos)
            surface.blit(rendered, rect)
        else:
            surface.blit(rendered, pos)


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


class Button:
    buttons = []

    def __init__(self, x: int, y: int, width: int, height: int, text, font: userFont, color, text_color, game_state: list, on_mouse_color=None, on_click_color=None, border_radius=10, plus_data=None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rect = pygame.Rect(x-width//2, y-height//2, width, height)
        self.text = text
        self.font = font
        self.color = color
        self.origin_color = color
        self.text_color = text_color
        self.on_mouse_color = on_mouse_color or colours.darker(color, 20)
        self.on_click_color = on_click_color or colours.darker(color, 50)
        self.border_radius = border_radius
        self.border_radius_orig = self.border_radius
        self.clicking = False
        self.plus_data = plus_data
        self.game_state = game_state
        self.buttons.append(self)

    def clicked(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if GAME_STATE in self.game_state:
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
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.rect.center = (x, y)

    def set_topleft(self, x, y):
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.rect.topleft = (x, y)


class HizaliRect:
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


class Slot:
    slots = []

    def __init__(self, id, display=None):
        self.id = id
        self.display = display

        self.used = False
        self.info = None
        self.unknown = False
        self.corrupted = False
        self.slots.append(self)

    @classmethod
    def update_infos(cls):
        infos = save_manager.get_all_infos()
        print(infos)

        for slot in cls.slots:
            slot: Slot
            slot.info = infos.get(slot.id)
            print(slot.info)
            slot.used = slot.info is not None
            print(slot.info is not None)
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


font1 = userFont("arial", 70)
font2 = userFont("arial", 50)
font3 = userFont("arial", 30)
font4 = userFont("arial", 20)
console = Console(command, font3, font3)
logging.info("Console created.")
_notofont = pygame.font.Font("arabica.ttf", 30)
notofont = userFont("arabica.ttf", 30)
notofont.font = _notofont
logging.info("Fonts loaded.")
for i in range(70):
    # Zaten otomatik listeye ekliyor
    Slot(i, display=Button(0, 0, 600, 200, f"Slot {i+1}", font2, colours.BLUE, colours.WHITE, ["LOAD_MENU_SL", "SAVE_MENU_SL"], colours.darker(colours.BLUE, 20), border_radius=5))
Slot.update_infos()

PATH = "saves"

game = {}


new_game_button = Button(
    0, 0, 300, 80,
    "Yeni Oyun",
    font1,
    colours.YELLOW,
    colours.WHITE,
    ["MENU", "GAME_ESC"],
    colours.darker(colours.YELLOW, 20),
    colours.darker(colours.YELLOW, 50)
)

continue_button = Button(
    0, 0, 300, 80,
    "Devam Et",
    font1,
    colours.YELLOW,
    colours.WHITE,
    ["MENU", "GAME_ESC"],
    colours.darker(colours.YELLOW, 20),
    colours.darker(colours.YELLOW, 50)
)

load_button = Button(
    0, 0, 300, 80,
    "Yükle",
    font1,
    colours.YELLOW,
    colours.WHITE,
    ["MENU", "GAME_ESC"],
    colours.darker(colours.YELLOW, 20),
    colours.darker(colours.YELLOW, 50)
)

save_button = Button(
    0, 0, 300, 80,
    "Kaydet",
    font1,
    colours.YELLOW,
    colours.WHITE,
    ["MENU", "GAME_ESC"],
    colours.darker(colours.YELLOW, 20),
    colours.darker(colours.YELLOW, 50)
)

settings_button = Button(
    0, 0, 300, 80,
    "Ayarlar",
    font1,
    colours.YELLOW,
    colours.WHITE,
    ["MENU", "GAME_ESC"],
    colours.darker(colours.YELLOW, 20),
    colours.darker(colours.YELLOW, 50)
)

quit_button = Button(
    0, 0, 300, 80,
    "Çık",
    font1,
    colours.RED,
    colours.WHITE,
    ["MENU", "GAME_ESC"],
    colours.darker(colours.RED, 20),
    colours.darker(colours.RED, 50)
)

sonraki_button = Button(
    0, 0, 300, 80,
    "Sonraki",
    font3,
    colours.GRAY,
    colours.WHITE,
    ["LOAD_MENU_SL", "SAVE_MENU_SL"],
    colours.darker(colours.GRAY, 20),
    colours.darker(colours.GRAY, 50),
    20
)

onceki_button = Button(
    0, 0, 300, 80,
    "Önceki",
    font3,
    colours.GRAY,
    colours.WHITE,
    ["LOAD_MENU_SL", "SAVE_MENU_SL"],
    colours.darker(colours.GRAY, 20),
    colours.darker(colours.GRAY, 50),
    20
)

warn_continue_button = Button(
    0, 0, 200, 55,
    "Devam Et",
    font3,
    colours.lighter(colours.BLACK, 30),
    colours.WHITE,
    ["WARN"],
    border_radius=20,
    plus_data=False
)

warn_return_button = Button(
    0, 0, 200, 55,
    "Geri Dön",
    font3,
    colours.lighter(colours.BLACK, 30),
    colours.WHITE,
    ["WARN"],
    border_radius=20,
    plus_data=False
)
logging.info("Static buttons created.")
logging.info("Trying to load last save.")
last = save_manager.get_info_last_slot()
logging.info(f"Last save loaded with data '{last}'")
if last:
    logging.debug(last)
    info_button = Button(
        0, 0, 80, 80,
        "i",
        font2,
        colours.BLUE,
        colours.WHITE,
        ["MENU"],
        plus_data=False
    )

    info_rect = HizaliRect(
        0, 0, 200, 200,
        font4,
        colours.WHITE,
        f"Tarih: {last['date']}\nSürüm: {last['version']}",
        colours.BLACK,
        plus_data=False
    )

return_button = Button(
    0, 0, 50, 50,
    "<-",
    font2,
    colours.RED,
    colours.WHITE,
    ["LOAD_MENU_SL", "SAVE_MENU_SL"]
)


def change_page(delta):
    sayfa.deger += delta


page_buttons = []
sayfa = 0
old_sayfa = sayfa
sayfa = LimitedNumber(0, 0, 1000)
visible_slots = []
escape_screen = False
played = False
saved_last = False
level = 1
def save_last():
    global saved_last
    try:
        save_manager.save_last_slot(game, globals()[game["Level"]])
    except KeyError:
        pass
    saved_last = True

rock_sword = classes.Sword("Taş Kılıç", 20, "Taş", colours.GRAY, 800)
iron_sword = classes.Sword("Demir Kılıç", 30, "Demir", colours.lighter(colours.GRAY, 80), 1500)
normal_gun = classes.Gun("Normal Silah", colours.lighter(colours.BLACK, 30), 20, 500, r"images/bronz_silahr.png", r"images/bronz_silah_mermi.png", 0.3, "bronze")
silver_gun = classes.Gun("Gümüş Silah", colours.lighter(colours.BLACK, 30), 40, 640, r"images/silver_silahr.png", r"images/silver_silah_mermi.png", 0.15, "silver")

level_sword_map = {
    "level2": rock_sword,
    "level4": iron_sword
}

zikkim = classes.Effect("hp", 10, 6)
level_item_map = {
    "level2": [
        classes.Item("Zıkkımın Kökü", colours.PURPLE, [zikkim.copy()], random.choice([classes.Item.REDUCER, classes.Item.APPENDER]), random.choice([classes.Item.YUVARLAK_IKSIR, classes.Item.TUP_IKSIR])),
        classes.Item("Zıkkımın Kökü", colours.PURPLE, [zikkim.copy()], random.choice([classes.Item.REDUCER, classes.Item.APPENDER]), random.choice([classes.Item.YUVARLAK_IKSIR, classes.Item.TUP_IKSIR])),
        classes.Item("Zıkkımın Kökü", colours.PURPLE, [zikkim.copy()], random.choice([classes.Item.REDUCER, classes.Item.APPENDER]), random.choice([classes.Item.YUVARLAK_IKSIR, classes.Item.TUP_IKSIR]))
    ],
    "level5": [
        classes.Item(
            "Can İksiri",
            colours.RED,
            [classes.Effect("hp", 17, -1)],
            classes.Item.TUP_IKSIR,
            classes.Item.APPENDER
        ),
        classes.Item(
            "Can İksiri",
            colours.RED,
            [classes.Effect("hp", 17, -1)],
            classes.Item.TUP_IKSIR,
            classes.Item.APPENDER
        ),
        classes.Item(
            "Can İksiri",
            colours.RED,
            [classes.Effect("hp", 17, -1)],
            classes.Item.TUP_IKSIR,
            classes.Item.APPENDER
        )
    ],
    "level7": [
        classes.Item(
            get_display(arabic_reshaper.reshape("الماءُ النابعُ من الحجرِ الذي استندَ إليهِ نبيُّنا بذراعِهِ.")),
            colours.GREEN,
            [classes.Effect("using_gun", normal_gun, -1)],
            classes.Item.TUP_IKSIR,
            classes.Item.EQUALER,
            pickable=False,
            font=notofont
        ),
        classes.Item(
            "Can İksiri",
            colours.RED,
            [classes.Effect("hp", 30, -1)],
            classes.Item.APPENDER,
            classes.Item.TUP_IKSIR
        ),
        classes.Item(
            "Can İksiri",
            colours.RED,
            [classes.Effect("hp", 30, -1)],
            classes.Item.APPENDER,
            classes.Item.TUP_IKSIR
        ),
        classes.Item(
            "Can İksiri",
            colours.RED,
            [classes.Effect("hp", 30, -1)],
            classes.Item.APPENDER,
            classes.Item.TUP_IKSIR
        )
    ],
    "level8": [
        classes.Item(
            "Tam Can İksiri",
            colours.RED,
            [classes.Effect("hp", 999999, -1)],
            classes.Item.TUP_IKSIR,
            classes.Item.APPENDER
        )
    ],
    "level9": [
        classes.Item(
            "Kraliçe El Abrahamın El Kremi",
            colours.lighter(colours.BLUE, 130),
            [classes.Effect("hp", 400, -1), classes.Effect("ability_healing", True, -1)],
            classes.Item.APPENDER,
            classes.Item.TUP_IKSIR
        )
    ]
}

level1 = [
    classes.Enemy(100, 5, r"images/enemyr.png")
]

level2 = [
    classes.Enemy(100, 5, r"images/enemyr.png")
]

level3 = [
    classes.Enemy(120, 8),
    classes.Enemy(60, 3),
    classes.Enemy(60, 3)
]

level4 = [
    classes.Enemy(200, 30, size=200, boss=True, after_max_hp=350, name="Fondöten")
]

level5 = [
    classes.Enemy(150, 5, image_name=r"images/enemypurpler.png", speed=500, damage_cooldown=0.3)
]

level6 = [
    classes.Enemy(30, 10, [classes.Enemy.ABILITY_ARROWS], image_name=r"images/enemy_arrowr.png")
]

level7 = [
    classes.Enemy(50, 5, [classes.Enemy.ABILITY_ARROWS], speed=250, image_name=r"images/enemy_arrowr.png"),
    classes.Enemy(50, 5, [classes.Enemy.ABILITY_ARROWS], speed=250, image_name=r"images/enemy_arrowr.png"),
    classes.Enemy(50, 5, [classes.Enemy.ABILITY_ARROWS], speed=250, image_name=r"images/enemy_arrowr.png"),
    classes.Enemy(50, 5, [classes.Enemy.ABILITY_ARROWS], speed=250, image_name=r"images/enemy_arrowr.png"),
    classes.Enemy(50, 5, [classes.Enemy.ABILITY_ARROWS], speed=250, image_name=r"images/enemy_arrowr.png"),
]

alberta_summon = classes.Enemy(60, 7, [classes.Enemy.ABILITY_ARROWS], r"images/enemy_arrowr.png", speed=250 ,cooldown=5)
level8 = [
    classes.Enemy(120, 12, speed=350, damage_cooldown=1.7),
    classes.Enemy(40, 46, speed=200, damage_cooldown=1, size=120),
    classes.Enemy(100, 4, speed=450, damage_cooldown=1.7),
    classes.Enemy(80, 3, speed=120, damage_cooldown=1.7),
    classes.Enemy(50, 4, [classes.Enemy.ABILITY_ARROWS], speed=350, damage_cooldown=3, image_name=r"images/enemy_arrowr.png"),
    classes.Enemy(50, 4, [classes.Enemy.ABILITY_ARROWS], speed=350, damage_cooldown=3, image_name=r"images/enemy_arrowr.png"),
    classes.Enemy(50, 4, [classes.Enemy.ABILITY_ARROWS], speed=350, damage_cooldown=3, image_name=r"images/enemy_arrowr.png"),
    classes.Enemy(1600, 45, [classes.Enemy.ABILITY_ARROWS, classes.Enemy.ABILITY_BOMBING], damage_cooldown=1.2, boss=True, after_max_hp=500, name="Kraliçe El Abraham", image_name=r"images/AlbertaChibir.png", size=20, speed=200, cooldown=3, summons=[
        alberta_summon.copy(),
        alberta_summon.copy(),
        alberta_summon.copy()
    ],
    collisions=False,
    arrow_image=r"images/arrow_gold.png")
]

del alberta_summon

level9 = [
    classes.Enemy.prepared_police(),
    classes.Enemy.prepared_police()
]

level10 = [
    classes.Enemy.prepared_police(),
    classes.Enemy.prepared_police()
]

level11 = [
    classes.Enemy.prepared_police(),
    classes.Enemy.prepared_police(),
    classes.Enemy.prepared_police(),
    classes.Enemy.prepared_police(),
    classes.Enemy(
        2200,
        57,
        [classes.Enemy.ABILITY_ARROWS, classes.Enemy.ABILITY_BOMBING],
        r"images/ampul_adamr.png",
        10,
        speed=340,
        damage_cooldown=0.7,
        boss=True,
        after_max_hp=950,
        name="Ampul Adam",
        summons=[
            classes.Enemy.prepared_police(),
        ],
        cooldown=7,
        cooldown_arrow=0.7,
        bagimsiz_summons=[classes.Enemy.prepared_old(True, 10)],
        cooldown_bagimsiz_summons=1,
        arrow_image=r"images/ampul_adam_arrow.png"
    ),
    classes.Enemy(
        900,
        12,
        [classes.Enemy.ABILITY_BOMBING],
        image_name=r"images/enemypurpler.png",
        size=250,
        speed=340,
        boss=True,
        name="Aile ve Yasaklar Bakanı",
        drops=[silver_gun, classes.Effect("heal_cooldown_orig", 3.5, -1, flags=(classes.Item.EQUALER,))]
    )
]

level12 = [
    classes.Enemy.miguel(),
    classes.Enemy.miguel(),
    classes.Enemy.miguel(),
]

level13 = [
    classes.Enemy.luffy(),
    classes.Enemy.miguel(),
    classes.Enemy.miguel()
]

level14 = [
    classes.Enemy.dinosaur(),
    classes.Enemy.luffy(),
    classes.Enemy.miguel(),
    classes.Enemy.miguel()
]

level15_orig = [
    classes.Enemy.dinosaur(),
    classes.Enemy.dinosaur(),
    classes.Enemy.luffy(),
    classes.Enemy.miguel(),
    classes.Enemy.miguel(),
]

level15 = [
    classes.Enemy.dinosaur(),
    classes.Enemy.dinosaur(),
    classes.Enemy.luffy(),
    classes.Enemy.miguel(),
    classes.Enemy.miguel(),
]

level16 = [
    classes.Enemy.dinosaur(),
    classes.Enemy.dinosaur(),
    classes.Enemy.luffy()
]

level17 = [
    classes.Enemy.dinosaur(),
]

levels = []
for k in list(globals().keys()):
    if k.startswith("level") and k[5:].isdigit() and len(k) < 8:
        levels.append(globals()[k])

_ordu = list(classes.Enemy.prepared_old(random_speed=True) for _ in range(12))
for enemy in _ordu:
    level10.append(enemy.copy())
del _ordu

_ordu = list(classes.Enemy.prepared_old(True) for _ in range(43))
for enemy in _ordu:
    level11.append(enemy.copy())
del _ordu

_ordu = list(classes.Enemy.prepared_old(True) for _ in range(10))
for enemy in _ordu:
    for level_enemy in level11:
        if level_enemy.boss:
            level_enemy.summons.append(enemy)
            break
del _ordu
logging.info("Game variables created.")


def update_level():
    global game, level, GAME_STATE
    try:
        try:
            if any(type(gun) == level_sword_map[f"level{level}"] for gun in game["Player"].available_guns):
                for gun in game["Player"].available_guns:
                    if type(gun) == level_sword_map[f"level{level}"]:
                        gun = level_sword_map[f"level{level}"]
            else:
                game["Player"].available_guns.append(level_sword_map[f"level{level}"])
            game["Player"].using_gun = level_sword_map[f"level{level}"]

        except KeyError:
            pass
        try:
            for item in level_item_map[f"level{level}"]:
                item.set_pos(game["World"], game["Player"])
                game["World"].items.append(item)
        except KeyError:
            pass
        game["Level"] = f"level{level}"
        for enemy in globals()[game["Level"]]:
            enemy.set_pos(game["World"], info)
    except KeyError:
        game["Win"] = True
        GAME_STATE = "WIN"
        logging.info("Player won game!")


def check_level():
    global game, level, GAME_STATE
    try:
        if all(not enemy.living for enemy in globals()[game["Level"]]):
            level += 1
            print(level)
            logging.info(f"Started level {level}")
            return update_level()
    except KeyError:
        GAME_STATE = "WIN"


def calculate_size(initialized_size: int, initialized_screen_s: int, size: int):
    '''
    Ekran boyutuna göre boyut hesaplar. Dinamik boyut gerektiren objeler için.
    '''
    calculated = int(initialized_size * (size / initialized_screen_s))
    return calculated


def firstLetterBig(text: str):
    '''
    Verilen metnin ilk harfini büyük yap, diğerlerini küçük.
    '''
    
    _list_text = list(text)
    
    text = ""
    for i, letter in enumerate(_list_text):
        _list_text[i]=letter.lower()
        
    _list_text[0] = _list_text[0].upper()
    for l in _list_text:
        text += l
    return text


clock = pygame.time.Clock()
game = copy.deepcopy(classes.defaults)

_change_drawing = 0.2
_reduce_cooldown_change_drawing = False
gun_choosing = False
cd_gun_choosing = 0.4
old_gun = None
dash_cooldown = 0.13
quick_gun_swap_index = 0
saved_last_cd = 0
change_sets_cd = 1.2

settings_buttons = []

logging.info("Game loop starting.")


def create_settings_buttons(coordinate: tuple):
    global settings_buttons
    settings_buttons.clear()

    for i, attr in enumerate(settings_manager.attrs.keys()):
        settings_buttons.append(
            Button(
                coordinate[0],
                coordinate[1],
                40,
                40,
                "",
                font1,
                colours.LIGHT_BLUE,
                colours.BLACK,
                ["SETTINGS"],
                border_radius=20,
                plus_data=attr
            )
        )

def createSettingsButton():
    settings_buttons.clear()

    for attr in settings_manager.attrs.keys():
        settings_buttons.append(
            Button(
                0,
                0,
                40,
                40,
                "",
                font1,
                colours.LIGHT_BLUE,
                colours.BLACK,
                ["SETTINGS"],
                border_radius=20,
                plus_data=attr
            )
        )
return_state_sets = None
is_music_playing = settings_manager.get_attribute("MUSIC")
music_loaded = False
while run:
    orig_dt = clock.tick(120) / 1000
    dt = orig_dt * dt_multiplier
    cd_gun_choosing -= dt
    dash_cooldown -= dt
    saved_last_cd -= dt
    change_sets_cd -= dt
    keys = pygame.key.get_pressed()
    if _reduce_cooldown_change_drawing:
        _change_drawing -= dt
    if _change_drawing <= 0:
        _reduce_cooldown_change_drawing = False
        _change_drawing = 0.2
        game["Player"].drawing=False
        game["Player"].speed = game["Player"].speed_max
        game["Player"].using_gun.dashing=False
    if saved_last_cd <= 0:
        saved_last_cd = 20
        saved_last = False
    width, height = screen.get_size()
    new_game_button.set_center(width * 0.5, height * 0.27)
    new_game_button.width = calculate_size(300, 800, width) # bu butonların genişliği 300 yüksekliği 800
    new_game_button.height = calculate_size(80, 800, height)
    continue_button.set_center(width * 0.5, height * 0.4)
    continue_button.width = calculate_size(300, 800, width)
    continue_button.height = calculate_size(80, 800, height)
    load_button.set_center(width * 0.5, height * 0.53)
    load_button.width = calculate_size(300, 800, width)
    load_button.height = calculate_size(80, 800, height)
    settings_button.set_center(width * 0.5, height * 0.66)
    settings_button.width = calculate_size(300, 800, width)
    settings_button.height = calculate_size(80, 800, height)
    save_button.set_center(width * 0.5, height * 0.79)
    save_button.width = calculate_size(300, 800, width)
    save_button.height = calculate_size(80, 800, height)
    quit_button.set_center(width * 0.5, height * 0.92)
    quit_button.width = calculate_size(300, 800, width)
    quit_button.height = calculate_size(80, 800, height)
    onceki_button.set_center(width * 0.2, height * 0.93)
    onceki_button.width = calculate_size(300, 800, width)
    onceki_button.height = calculate_size(80, 800, height)
    sonraki_button.set_center(width * 0.8, height * 0.93)
    sonraki_button.width = calculate_size(300, 800, width)
    sonraki_button.height = calculate_size(80, 800, height)
    warn_continue_button.set_center(width * 0.4, height * 0.7)
    warn_continue_button.width = calculate_size(200, 800, width)
    warn_continue_button.height = calculate_size(55, 800, height)
    warn_return_button.set_center(width * 0.6, height * 0.7)
    warn_return_button.width = calculate_size(200, 800, width)
    warn_return_button.height = calculate_size(55, 800, height)
    if last:
        info_button.set_center(continue_button.rect.center[0] + continue_button.width / 2 + 50, height * 0.53)
        info_rect.set_center(continue_button.rect.center[0] + continue_button.width / 2 + 300, height * 0.53)
    return_button.set_center(width * 0.1, height * 0.93)
    return_button.width = calculate_size(50, 800, width)
    return_button.height = calculate_size(50, 800, height)
    
    for event in pygame.event.get():
        console.handle_event(event)
        if event.type == pygame.QUIT:
            run = False
        if new_game_button.clicked(event):
            if GAME_STATE == "MENU":
                game = copy.deepcopy(classes.defaults)
                is_music_playing = settings_manager.get_attribute("MUSIC")
                if is_music_playing:
                    try:
                        pygame.mixer.music.load(settings_manager.get_attribute("MUSIC_PATH"))
                        music_loaded = True
                        pygame.mixer.music.play(settings_manager.get_attribute("MUSIC_LOOP"))
                    except (pygame.error, FileNotFoundError):
                        logging.warning(f"Music not found: {settings_manager.get_attribute("MUSIC_PATH")}")
                        is_music_playing = False
                GAME_STATE = "GAME"
                save_manager.delete_last_slot()
                game["World"].create_rocks(info.current_w, info.current_h)
                for enemy in globals()[game["Level"]]:
                    enemy.set_pos(game["World"], info)
                level15.append(classes.Enemy.skzoo(game["Player"], special=True))
            if not any(e.effect_appending == "using_gun" for e in level_item_map["level7"][0].effects):
                level_item_map["level7"][0].effects.append(
                    classes.Effect(
                        "using_gun",
                        normal_gun,
                        -1,
                        game["Player"].available_guns,
                        [normal_gun]
                    )
                )
            
            if GAME_STATE == "GAME_ESC":
                print("ÖNCE")
                game = classes.reset(info.current_w, info.current_h, game)
                level = 1
                is_music_playing = settings_manager.get_attribute("MUSIC")
                if is_music_playing:
                    pygame.mixer.music.pause()
                    pygame.mixer.music.unload()
                    try:
                        pygame.mixer.music.load(settings_manager.get_attribute("MUSIC_PATH"))
                        music_loaded = True
                        pygame.mixer.music.play(settings_manager.get_attribute("MUSIC_LOOP"))
                    except (pygame.error, FileNotFoundError):
                        logging.warning(f"Music not found: {settings_manager.get_attribute("MUSIC_PATH")}")
                        is_music_playing = False
                for lvl in levels:
                    for enemy in lvl:
                        enemy: classes.Enemy
                        enemy.reset(game["World"])
                level15.clear()
                level15 = copy.deepcopy(level15_orig)
                level15.append(classes.Enemy.skzoo(game["Player"], special=True))
                GAME_STATE = "GAME"
                escape_screen = False
                
            played = True
        for button in Button.buttons:
            button.on_mouse()
        if continue_button.clicked(event):
            if last:
                if last["corrupted"]:
                    continue
                game = save_manager.last_slot()
                level = int(game["Level"].replace("level", ""))
                try:
                    globals()[game["Level"]].clear()
                except KeyError:
                    GAME_STATE = "WIN"
                    continue
                for enemy_id, enemy in game["EnemyData"].items():
                    enemy: classes.Enemy
                    print("YÜKLENDİ:", enemy_id, enemy.x, enemy.y)
                    globals()[game["Level"]].append(enemy)
                GAME_STATE = "GAME"
                played = True
                escape_screen = False
        

        if GAME_STATE == "GAME":
            check_level()
            if game["Win"]:
                GAME_STATE = "WIN"
            for item in game["World"].items:
                if item.rect.colliderect(game["Player"].image_rect):
                    item.use(game["Player"])
                try:
                    varliklar = list(enemy for enemy in globals()[game["Level"]])
                except KeyError:
                    pass
                varliklar.append(game["Player"])
                item.update(event, varliklar)
            if keys[pygame.K_LSHIFT] and type(game["Player"].using_gun) == classes.Gun:
                game["Player"].using_gun.dash_attack(game["Player"])
                _reduce_cooldown_change_drawing = True

            
            keys = pygame.key.get_pressed()
            if keys[pygame.K_r] and cd_gun_choosing <= 0:
                gun_choosing = not gun_choosing
                cd_gun_choosing = 0.4

            if keys[pygame.K_TAB]:
                if cd_gun_choosing <= 0:
                    quick_gun_swap_index += 1
                    old_gun = game["Player"].using_gun
                    try:
                        game["Player"].available_guns[quick_gun_swap_index]
                    except IndexError:
                        quick_gun_swap_index = 0
                    finally:
                        if type(game["Player"].available_guns[quick_gun_swap_index]) == classes.Charm:
                                game["Player"].using_gun = game["Player"].available_guns[quick_gun_swap_index]
                                game["Player"].using_gun.used = False
                                game["Player"].using_gun.equip(game["Player"])
                        else:
                            if old_gun is not None:
                                if type(old_gun) == classes.Charm:
                                    old_gun.unequip(game["Player"])
                                game["Player"].using_gun = game["Player"].available_guns[quick_gun_swap_index]
                    cd_gun_choosing = 0.35
            
            if gun_choosing:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    secilen = game["Player"].weapon_wheel_get_mouse(gun_choosing)
                    if secilen is not None:
                        secilen: int
                        old_gun = game["Player"].using_gun
                        if type(game["Player"].available_guns[secilen]) == classes.Charm:
                            game["Player"].using_gun = game["Player"].available_guns[secilen]
                            game["Player"].using_gun.used = False
                            game["Player"].using_gun.equip(game["Player"])
                        else:
                            if old_gun is not None:
                                if type(old_gun) == classes.Charm:
                                    old_gun.unequip(game["Player"])
                            game["Player"].using_gun = game["Player"].available_guns[secilen]
                        quick_gun_swap_index = secilen
                        print(secilen)
                        print(game["Player"].available_guns[secilen].name)
                        print(game["Player"].using_gun.name)
                        gun_choosing = False
        if GAME_STATE == "LOAD_MENU_SL":
            if warn_continue_button.plus_data:
                game = save_manager.load(warned_slot)
                level = int(game["Level"].replace("level", ""))
                print("Yüklendi")
                print(game)
                GAME_STATE = "GAME"
                escape_screen = False
                played = True
                level_item_map["level7"][0].effects.append(classes.Effect("using_gun", normal_gun, -1, game["Player"].available_guns, [normal_gun]))


        for slot in visible_slots:
            if slot.display.clicked(event):
                slot: Slot
                if GAME_STATE == "LOAD_MENU_SL" and slot.used and not slot.corrupted:
                    if str(save_manager.get_version(slot.id)) != GAME_VERSION:
                        GAME_STATE = "WARN"
                        warned_slot = slot.id
                        logging.warning("User tryed to load a old version save.")
                        continue
                    game = save_manager.load(slot.id)
                    level = int(game["Level"].replace("level", ""))
                    print("Yüklendi")
                    print(game)
                    globals()[game["Level"]].clear()
                    for enemy in game["EnemyData"].values():
                        enemy: classes.Enemy
                        globals()[game["Level"]].append(enemy)
                    escape_screen = False
                    played = True
                    GAME_STATE = "GAME"
                    level_item_map["level7"][0].effects.append(classes.Effect("using_gun", normal_gun, -1, game["Player"].available_guns, [normal_gun]))
                if GAME_STATE == "SAVE_MENU_SL":
                    if played:
                        print("Kaydedilen slot:", slot.id)
                        del game["EnemyData"]
                        game["EnemyData"] = {}
                        for enemy in globals()[game["Level"]]:
                            enemy: classes.Enemy
                            game["EnemyData"][enemy.id] = enemy
                        save_manager.save(slot.id, game, GAME_VERSION)
                        Slot.update_infos()
        if load_button.clicked(event):
            return_button.plus_data = GAME_STATE
            GAME_STATE = "LOAD_MENU_SL"
            sayfa.deger = 0
            old_sayfa = 0
            for enemy in level1:
                enemy.set_pos(game["World"], info)
        if warn_continue_button.clicked(event):
            warn_continue_button.plus_data = True
            GAME_STATE = "LOAD_MENU_SL"
        if warn_return_button.clicked(event):
            GAME_STATE = "LOAD_MENU_SL"
        if save_button.clicked(event):
            return_button.plus_data = GAME_STATE
            GAME_STATE = "SAVE_MENU_SL"
            sayfa.deger = 0
            old_sayfa = 0

        if settings_button.clicked(event):
            return_state_sets = GAME_STATE
            if return_state_sets == "GAME_ESC": return_state_sets = "GAME"
            escape_screen = False
            GAME_STATE = "SETTINGS"
            
        
        if quit_button.clicked(event):
            run = False
        if last:
            if info_button.clicked(event) and info_rect.plus_data:
                info_button.plus_data = not info_button.plus_data
        for button in page_buttons:
            if button.clicked(event):
                sayfa = button.plus_data
            button.on_mouse()
        if GAME_STATE == "GAME":
            if keys[pygame.K_LSHIFT] and dash_cooldown <= 0 and not game["Player"].drawing:
                game["Player"].dash()
                dash_cooldown = 0.13
            if event.type == pygame.KEYDOWN:
                keys = pygame.key.get_pressed()
                if keys[pygame.K_t]:
                    game["Player"].teleport(game["World"])
            for enemy in globals()[game["Level"]]:
                enemy.damage(game["Player"])
            game["Player"].damage(globals()[game["Level"]], dt, True if escape_screen or gun_choosing else False)
            if game["Player"].hp <= 0:
                GAME_STATE = "LOSS"
        if not GAME_STATE in ["MENU", "LOAD_MENU_SL", "SAVE_MENU_SL", "SETTINGS"]:
            if event.type == pygame.KEYDOWN:
                keys = pygame.key.get_pressed()
                if keys[pygame.K_ESCAPE]:
                    escape_screen = not escape_screen
                if escape_screen:
                    if not GAME_STATE.split("_")[-1] == "ESC":
                        GAME_STATE += "_ESC"
                        is_music_playing = settings_manager.get_attribute("MUSIC")
                        if is_music_playing:
                            pygame.mixer.music.pause()
                else:
                    GAME_STATE = GAME_STATE.replace("_ESC", "")
                    is_music_playing = settings_manager.get_attribute("MUSIC")
                    if is_music_playing:
                        pygame.mixer.music.unpause()

        if GAME_STATE == "SETTINGS":
            if keys[pygame.K_ESCAPE]:
                GAME_STATE = return_state_sets
                if GAME_STATE == "GAME_ESC" or return_state_sets == "GAME_ESC":
                    is_music_playing = settings_manager.get_attribute("MUSIC")
                    if not music_loaded:
                        pygame.mixer.music.load(settings_manager.get_attribute("MUSIC_PATH"))
                        pygame.mixer.music.play(settings_manager.get_attribute("MUSIC_LOOP"))
                        continue
                    if is_music_playing:
                        pygame.mixer.music.unpause()

        for button in settings_buttons:
            if button.clicked(event):

                attr_value = settings_manager.get_attribute(button.plus_data, log=True)
                if isinstance(attr_value, bool):
                    settings_manager.write_attribute(button.plus_data, not attr_value)

        
        if onceki_button.clicked(event):
            change_page(-1)

        if sonraki_button.clicked(event):
            change_page(1)
        if event.type == pygame.WINDOWMAXIMIZED:
            if last:
                info_rect.plus_data = True

        if event.type == pygame.WINDOWRESTORED:
            if last:
                info_rect.plus_data = False

        if return_button.clicked(event):
            escape_screen = False
            GAME_STATE = return_button.plus_data.replace("_ESC", "")
    if GAME_STATE == "MENU":
        screen.fill(colours.BLACK)
        _bolum = calculate_size(50, 800, width)
        _font = userFont("arial", int(_bolum))
        _font.draw_text("SAVAŞ OYUNU", (width//2, int(height*0.11)), screen, colours.WHITE, "center")
        new_game_button.draw(screen)
        continue_button.draw(screen)
        load_button.draw(screen)
        save_button.draw(screen)
        settings_button.draw(screen)
        quit_button.draw(screen)
        if last:
            if info_rect.plus_data:
                info_button.draw(screen)
                if info_button.plus_data:
                    info_rect.width = calculate_size(200, 800, width)
                    info_rect.height = calculate_size(200, 800, height)
                    info_rect.draw(screen)
    elif GAME_STATE == "GAME":
        game["World"].draw(screen)
        game["World"].draw_items(screen, font3, game["Player"])
        game["World"].update(globals()[game["Level"]])
        if type(game["Player"].using_gun) == classes.Gun:
            if pygame.mouse.get_pressed()[0]:
                game["Player"].using_gun.fire()
        if type(game["Player"].using_gun) == classes.Sword:
            game["Player"].using_gun.draw(screen, game["Player"].x + game["Player"].hand_spot, game["Player"].y + 10, True if game["Player"].drawing or game["Player"].sword_attacking else False, game["Player"].angle)
        if type(game["Player"].using_gun) == classes.Gun:
            game["Player"].using_gun.draw(screen, game["Player"].x + 30, game["Player"].y + 10)
        if type(game["Player"].using_gun) == classes.Charm:
            game["Player"].using_gun.draw(screen, game["Player"].x + 30, game["Player"].y + 10)
        if not escape_screen and not gun_choosing:
            game["Player"].update(pygame.mouse.get_pos(), game["World"], dt, width, height, globals()[game["Level"]])
            game["Player"].heal(dt)
            game["Player"].sword_attack(dt)
            if type(game["Player"].using_gun) == classes.Gun:
                game["Player"].using_gun.update(game["World"], dt, globals()[game["Level"]])
            if type(game["Player"].using_gun) == classes.Charm:
                game["Player"].using_gun.update(game["Player"].angle, dt)
                game["Player"].using_gun.use_active(game["Player"], dt)
            if type(game["Player"].using_gun) == classes.Sword:
                game["Player"].deflect(globals()[game["Level"]], dt)
            for enemy in globals()[game["Level"]]:
                enemy: classes.Enemy
                enemy.update(game["Player"], game["World"], dt, game["Level"])
                enemy.update_arrows(game["Player"], dt)
                enemy.summon(dt, globals()[game["Level"]], game["World"])
                enemy.update_bombs(game["Player"], dt)
                enemy.draw_sgrounds(screen)

            for item in game["World"].items:
                item.update_pos(dt)
            try:
                for enemy in globals()[game["Level"]]:
                    enemy.use_arrow(dt)
                    enemy.use_bombing(dt, game["Player"])
                    enemy.use_split_ground(dt, game["Player"])
            except KeyError:
                pass
        for enemy in globals()[game["Level"]]:
            enemy.draw_arrows(screen)
            enemy.draw_bombs(screen, dt)
        classes.Enemy.draw(screen, font3, globals()[game["Level"]], font1)
        game["Player"].draw(screen)
        game["Player"].draw_dash(screen)
        game["Player"].draw_teleport(screen)
        game["Player"].draw_statistics(screen, font2, info)
        if gun_choosing:
            game["Player"].draw_available_guns(screen)
    elif GAME_STATE.split("_")[-1] == "ESC":
        new_game_button.draw(screen)
        continue_button.draw(screen)
        load_button.draw(screen)
        save_button.draw(screen)
        settings_button.draw(screen)
        quit_button.draw(screen)
    elif GAME_STATE.split("_")[-1] == "SL":
        screen.fill(colours.BLACK)
        slot = Slot.slots[0]
        slot_w = slot.display.width
        slot_h = slot.display.height
        gap = 20

        satir_basina = max(1, (width - gap) // (slot_w + gap))
        sutun_basina = max(1, (height - gap - 100) // (slot_h + gap))

        sayfa_basina = satir_basina * sutun_basina
        sayfa_sayisi = math.ceil(len(Slot.slots) / sayfa_basina)
        sayfa.max = sayfa_sayisi-1
        baslangic = sayfa.deger * sayfa_basina
        bitis = min(baslangic + sayfa_basina, len(Slot.slots))
        index = baslangic
        visible_slots.clear()
        for satir in range(sutun_basina):
            for sutun in range(satir_basina):

                if index >= bitis:
                    break

                slot = Slot.slots[index]
                slot: Slot
                visible_slots.append(slot)
                x = gap + sutun * (slot_w + gap)
                y = gap + satir * (slot_h + gap)

                slot.display.set_topleft(x, y)
                slot.display.text = f"Slot {slot.id + 1}"
                if slot.used:
                    slot.display.color = colours.GREEN
                    slot.display.on_mouse_color = colours.darker(colours.GREEN, 20)
                    slot.display.text += (
                        f"\n{slot.info['date']}"
                        f"\nSürüm: {save_manager.get_version(slot.id)}"
                    )

                else:
                    if slot.corrupted:
                        slot.display.color = colours.RED
                        slot.display.on_mouse_color = colours.RED
                        slot.display.text += "\nBozuk Slot"

                    elif slot.unknown:
                        slot.display.color = colours.GRAY
                        slot.display.on_mouse_color = colours.GRAY
                        slot.display.text += f"\nBilinmeyen Hata"
                    
                    else:
                        slot.display.text += "\nBoş Slot"

                slot.display.draw(screen)
                index += 1
        onceki_button.draw(screen)
        sonraki_button.draw(screen)
        return_button.draw(screen)
        font2.draw_text(f"{sayfa.deger+1}. sayfa", (width * 0.5, height * 0.93), screen, (255, 255, 255), "center")

    elif GAME_STATE == "SETTINGS":
        screen.fill(colours.BLACK)
        column_width = width // 2
        row_height = calculate_size(100, 800, height)

        max_rows = max(
            1,
            (height - calculate_size(420, 800, height)) // row_height
        )

        button_size = calculate_size(40, 800, width)

        for i, button in enumerate(settings_buttons):

            column = i // max_rows
            row = i % max_rows

            x = calculate_size(20, 800, width) + column * column_width
            y = calculate_size(20, 800, height) + row * row_height

            rendered = font2.return_text(
                firstLetterBig(button.plus_data),
                colours.WHITE
            )

            button.width = button_size
            button.height = button_size

            button.set_center(
                x + rendered.get_width() + calculate_size(50, 800, width),
                y + rendered.get_height() // 2
            )
        for i, attr in enumerate(settings_manager.attrs.keys()):

            # İlk sütunda kaç satır olabileceği
            max_rows = max(1, (height - 420) // row_height)

            column = i // max_rows
            row = i % max_rows

            x = 20 + column * column_width
            y = 20 + row * row_height

            rendered = font2.return_text(
                firstLetterBig(attr),
                colours.WHITE
            )

            screen.blit(rendered, (x, y))

            value = settings_manager.get_attribute(attr, log=False)
            if value==None:
                pass
            elif isinstance(value, bool):
                pygame.draw.circle(
                    screen,
                    colours.LIGHT_BLUE if value else colours.GRAY,
                    (
                        x + rendered.get_width() + 50,
                        y + rendered.get_height() // 2
                    ),
                    20
                )
            elif isinstance(value, int):
                font2.draw_text(str(value), 
                                (x + rendered.get_width() + 70,
                                y + rendered.get_height() // 2), screen, colours.WHITE, hiza="midleft")
            elif isinstance(value, str):
                input_box = classes.InputBox(x + rendered.get_width() + 70,
                                             y + rendered.get_height() // 2,
                                            (width // 2 - (x + rendered.get_width() + 70)) - 30,
                                            120,
                                            colours.GRAY,
                                            font3
                                             )
                input_box.text = value
                input_box.width = width // 2
                input_box.draw(screen)



        console.calculate_height(height)
        pygame.draw.line(
            screen,
            colours.WHITE,
            (width // 2, 0),
            (width // 2, height - console.console_height),
            3
        )

        console.draw(screen, height)
        for button in settings_buttons:
            pygame.draw.rect(
                screen,
                colours.RED,
                button.rect,
                2
            )
    elif GAME_STATE == "WARN":
        screen.fill(colours.BLACK)
        warn_rect = pygame.Rect(
            info.current_w / 2,
            info.current_h / 2,
            700,
            400
        )
        warn_rect.center = (
            info.current_w / 2,
            info.current_h / 2
        )
        pygame.draw.rect(
            screen,
            colours.lighter(colours.BLACK, 30),
            warn_rect,
            border_radius=20
        )
        font1.draw_text("UYARI!", (info.current_w / 2, info.current_h / 2 - 120), screen, colours.WHITE, hiza="center")
        font2.draw_text(
            "Yüklemekte bulunduğunuz kayıt ile",
            (info.current_w / 2, info.current_h / 2),
            screen,
            colours.WHITE,
            "center"
        )
        font2.draw_text(
            "şuanki oyunun sürümü aynı DEĞİL!",
            (info.current_w / 2, info.current_h / 2 + font2.font.get_height() + 20),
            screen,
            colours.WHITE,
            "center"
        )
        warn_continue_button.draw(screen)
        warn_return_button.draw(screen)

    elif GAME_STATE == "LOSS":
        screen.fill(colours.RED)
        _bolum = calculate_size(50, 800, width)
        _font = userFont("arial", int(_bolum))
        _font.draw_text("KAYBETTİNİZ", (width//2, int(height*0.11)), screen, colours.WHITE, "center")
    elif GAME_STATE == "WIN":
        screen.fill(colours.YELLOW)
    elif not saved_last and played:
        save_last()
        logging.info("Saving last.")
    else:
        raise InvalidGameStateError(GAME_STATE)
    pygame.display.flip()

if played and settings_manager.get_attribute("SAVE_LAST"):
    if played:
        try:
            _level = globals()[game["Level"]]
        except KeyError:
            level_ = int(game["Level"].replace("level", ""))
            level_ -= 1
            _level = globals()[f"level{level_}"]

        save_manager.save_last_slot(game, _level)
        logging.info("Saving last slot after exiting game.")

if GAME_STATE == "LOSS":
    save_manager.delete_last_slot()
    logging.info("Deleting last slot due to loss.")

if bool(settings_manager.get_attribute("DEL_OUTPUTS")):
    if os.name == "nt":
        subprocess.run("cls", shell=True)
    else:
        subprocess.run(["clear"])
    logging.info("Deleting console outputs.")

logging.info("Quitting game.")
pygame.mixer.music.pause()
pygame.quit()
pygame.mixer.quit()
sys.exit(0)
