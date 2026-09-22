import logging
import classes
import colours
from bidi.algorithm import get_display
import arabic_reshaper
import random
import pygame
from cooldown import Cooldown
import os
from basedir import BASE_DIR
from fonts import notofont

pygame.font.init()

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(filename)s: "
            "%(lineno)d [%(funcName)s] | %(message)s",
    filename="game.log",
)

zikkim = classes.Effect("hp", 10, 6)
rock_sword = classes.Sword("Taş Kılıç", 20, colours.GRAY, 800, classes.MaterialFlags.ROCK)
iron_sword = classes.Sword("Demir Kılıç", 30, colours.lighter(colours.GRAY, 80), 1500, classes.MaterialFlags.IRON)
bronze_gun = classes.Gun("Normal Silah", colours.lighter(colours.BLACK, 30), 20, 500, os.path.join(BASE_DIR,r"images/bronz_silahr.png"), os.path.join(BASE_DIR,r"images/bronz_silah_mermi.png"), 0.3, classes.MaterialFlags.BRONZE)
silver_gun = classes.Gun("Gümüş Silah", colours.lighter(colours.BLACK, 30), 40, 640, os.path.join(BASE_DIR,r"images/silver_silahr.png"), os.path.join(BASE_DIR,r"images/silver_silah_mermi.png"), 0.15, classes.MaterialFlags.SILVER)

level1 = [
    classes.Enemy(100, 5, image_name=os.path.join(BASE_DIR,r"images/enemyr.png"))
]

level2 = [
    classes.Enemy(100, 5, image_name=os.path.join(BASE_DIR,r"images/enemyr.png"))
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
    classes.Enemy(150, 5, image_name=os.path.join(BASE_DIR,r"images/enemypurpler.png"), speed=500, damage_cooldown=Cooldown(0.3))
]

level6 = [
    classes.Enemy(30, 10, [classes.EnemyAbilities.ABILITY_ARROWS], image_name=os.path.join(BASE_DIR,r"images/enemy_arrowr.png"))
]

level7 = [
    classes.Enemy(50, 5, [classes.EnemyAbilities.ABILITY_ARROWS], speed=250, image_name=os.path.join(BASE_DIR,r"images/enemy_arrowr.png")),
    classes.Enemy(50, 5, [classes.EnemyAbilities.ABILITY_ARROWS], speed=250, image_name=os.path.join(BASE_DIR,r"images/enemy_arrowr.png")),
    classes.Enemy(50, 5, [classes.EnemyAbilities.ABILITY_ARROWS], speed=250, image_name=os.path.join(BASE_DIR,r"images/enemy_arrowr.png")),
    classes.Enemy(50, 5, [classes.EnemyAbilities.ABILITY_ARROWS], speed=250, image_name=os.path.join(BASE_DIR,r"images/enemy_arrowr.png")),
    classes.Enemy(50, 5, [classes.EnemyAbilities.ABILITY_ARROWS], speed=250, image_name=os.path.join(BASE_DIR,r"images/enemy_arrowr.png")),
]

alberta_summon = classes.Enemy(60, 7, [classes.EnemyAbilities.ABILITY_ARROWS], os.path.join(BASE_DIR,r"images/enemy_arrowr.png"), speed=250 ,cooldown=Cooldown(5))
level8 = [
    classes.Enemy(120, 12, speed=350, damage_cooldown=Cooldown(1.7)),
    classes.Enemy(40, 46, speed=200, damage_cooldown=Cooldown(1), size=120),
    classes.Enemy(100, 4, speed=450, damage_cooldown=Cooldown(1.7)),
    classes.Enemy(80, 3, speed=120, damage_cooldown=Cooldown(1.7)),
    classes.Enemy(50, 4, [classes.EnemyAbilities.ABILITY_ARROWS], speed=350, damage_cooldown=Cooldown(3), image_name=os.path.join(BASE_DIR,r"images/enemy_arrowr.png")),
    classes.Enemy(50, 4, [classes.EnemyAbilities.ABILITY_ARROWS], speed=350, damage_cooldown=Cooldown(3), image_name=os.path.join(BASE_DIR,r"images/enemy_arrowr.png")),
    classes.Enemy(50, 4, [classes.EnemyAbilities.ABILITY_ARROWS], speed=350, damage_cooldown=Cooldown(3), image_name=os.path.join(BASE_DIR,r"images/enemy_arrowr.png")),
    classes.Enemy(1600, 45, [classes.EnemyAbilities.ABILITY_ARROWS, classes.EnemyAbilities.ABILITY_BOMBING], damage_cooldown=Cooldown(1.2), boss=True, after_max_hp=500, name="Kraliçe El Abraham", image_name=os.path.join(BASE_DIR,r"images/AlbertaChibir.png"), size=20, speed=200, cooldown=Cooldown(3), summons=[
        alberta_summon.copy(),
        alberta_summon.copy(),
        alberta_summon.copy()
    ],
    collisions=False,
    arrow_image=os.path.join(BASE_DIR,r"images/arrow_gold.png"))
]

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
        [classes.EnemyAbilities.ABILITY_ARROWS, classes.EnemyAbilities.ABILITY_BOMBING],
        os.path.join(BASE_DIR,r"images/ampul_adamr.png"),
        10,
        speed=340,
        damage_cooldown=Cooldown(0.7),
        boss=True,
        after_max_hp=950,
        name="Ampul Adam",
        summons=[
            classes.Enemy.prepared_police(),
        ],
        cooldown=Cooldown(7),
        cooldown_arrow=Cooldown(0.75),
        bagimsiz_summons=[classes.Enemy.prepared_old(True, 10)],
        cooldown_bagimsiz_summons=Cooldown(1),
        arrow_image=os.path.join(BASE_DIR,r"images/ampul_adam_arrow.png")
    ),
    classes.Enemy(
        900,
        12,
        [classes.EnemyAbilities.ABILITY_BOMBING],
        image_name=os.path.join(BASE_DIR,r"images/enemypurpler.png"),
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
    classes.Enemy.luffy(),
    classes.Enemy.floppa(),
    classes.Enemy.miguel(),
    classes.Enemy.miguel(),
    classes.Enemy.miguel(),
    classes.Enemy.miguel(),
    classes.Enemy.miguel(),
    classes.Enemy.miguel(),
    classes.Enemy.miguel()
]

level17 = [
    classes.Enemy.dinosaur(),
    classes.Enemy.floppa(),
    classes.Enemy.dinosaur(),
    classes.Enemy.skzoo(),
    classes.Enemy.skzoo(),
    classes.Enemy.luffy(),
    classes.Enemy.miguel(),
    classes.Enemy.miguel(),
    classes.Enemy.miguel(),
    classes.Enemy.demirbt()
]

levels: list[list[classes.Enemy]] = []


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

levels.append(level1)
levels.append(level2)
levels.append(level3)
levels.append(level4)
levels.append(level5)
levels.append(level6)
levels.append(level7)
levels.append(level8)
levels.append(level9)
levels.append(level10)
levels.append(level11)
levels.append(level12)
levels.append(level13)
levels.append(level14)
levels.append(level15)
levels.append(level16)
levels.append(level17)



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
            [classes.Effect("using_gun", bronze_gun, -1)],
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

level_sword_map = {
    "level2": rock_sword,
    "level4": iron_sword
}

logging.info("Level variables created.")