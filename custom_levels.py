r'''
Bu dosya `Dünya Seç` butonundaki farklı dünyaların seviyelerini içerir.

NOT: VARSAYILAN SEVİYELER (`Yeni Oyun` butonundaki dünya) İÇİN `levels.py` DOSYASINI KULLANIN.

Her dünyanın seviyeleri için bir dict açılacak ve içinde bütün seviyelerin olduğu bir liste ile seviye-kılıç, seviye-item sözlükleri içerecek.
Örnek seviyeler listesi.
Example:

    >>> import classes
    >>> import colours

    >>> levels_cyber_world = {
        "levels": [
            [
                classes.Enemy(100, 5),
                classes.Enemy(100, 10),
            ],
            [
                classes.Enemy(200, 23),
                classes.Enemy(300, 40)
            ]
        ],
        "levels_sword_map": {
            "level1": classes.Sword(
                "Demir Kılıç",
                30,
                colours.lighter(colours.GRAY, 80),
                1500,
                classes.MaterialFlags.IRON
            )
        },
        "levels_item_map": {
            "level1": classes.Item(
                "Can İksiri",
                colours.RED,
                [classes.Effect("hp", 17, -1)],
                classes.Item.TUP_IKSIR,
                classes.Item.APPENDER
            )
        }
    }
'''

import logging
import classes
import colours
from gamedata import GameData
import pygame
from cooldown import Cooldown
import os
from basedir import BASE_DIR
from typing import Literal

pygame.font.init()

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(filename)s: "
            "%(lineno)d [%(funcName)s] | %(message)s",
    filename="game.log",
)

aether_katana = classes.CyberKatana()
iron_sword = classes.Sword(
    "Demir Kılıç",
    60,
    colours.GRAY,
    900,
    classes.MaterialFlags.IRON
)

LEVEL_TYPE = dict[Literal["levels", "levels_sword_map", "levels_item_map"], list[list[classes.Enemy]] | dict[str, classes.Sword] | dict[str, classes.Item]]

# Cyber World

levels_cyber_world: LEVEL_TYPE = {
    "levels": [
        [
            classes.Enemy(300, 5, sprites_name=os.path.join(BASE_DIR, r"sprites/ledadam.sospr")),
            classes.Enemy(300, 5, sprites_name=os.path.join(BASE_DIR, r"sprites/ledadam.sospr"))
        ]
    ],
    "levels_item_map": {
        "level1": [
            classes.Item(
                "Yalıtkan Su",
                (0, 255, 255),
                [
                    classes.Effect(
                        "hp",
                        50,
                        0,
                        flags=classes.Item.APPENDER
                    )
                ],
                classes.Item.APPENDER,
                classes.Item.TUP_IKSIR
            )
        ]
    },
    "levels_sword_map": {
        "level1": iron_sword
    }
}

player_cyber_world: classes.Player = classes.Player(
    200,
    iron_sword,
    os.path.join(BASE_DIR, r"images/stickmanr.png"),
    None,
    anim_dir=os.path.join(BASE_DIR, r"images/stickman_sprites")
)

world_cyber_world: classes.World = classes.World(
    colours.GRAY,
    colours.darker(colours.GRAY, 45),
    colours.lighter(colours.GRAY, 10),
    [],
    os.path.join(BASE_DIR, r"images/metalic_map.png"),
    os.path.join(BASE_DIR, r"images/metaldirt_pattern.png"),
    "cyber",
    levels_cyber_world,
    grid=True,
    rock_type="cyber"
)

game_data_cyber_world: GameData = GameData(
    player_cyber_world,
    world_cyber_world
)
