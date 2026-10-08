import pygame
from userfont import userFont
import logging
from dfont import DynamicFont
import os
from typing import Literal

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(filename)s: %(lineno)d [%(funcName)s] | %(message)s',
    filename="game.log"
)

pygame.font.init()

all_font1 = userFont(os.path.join(BASE_DIR, r"fonts/unifont-18.0.01.otf"), 70)
all_font2 = userFont(os.path.join(BASE_DIR, r"fonts/unifont-18.0.01.otf"), 50)
all_font3 = userFont(os.path.join(BASE_DIR, r"fonts/unifont-18.0.01.otf"), 30)
all_font4 = userFont(os.path.join(BASE_DIR, r"fonts/unifont-18.0.01.otf"), 20)

clarity_city = os.path.join(BASE_DIR, r"fonts/Clarity-city.ttf")

font1_univ = userFont(clarity_city, 70)
font2_univ = userFont(clarity_city, 50)
font3_univ = userFont(clarity_city, 30)
font4_univ = userFont(clarity_city, 20)

font1_arabic = userFont(os.path.join(BASE_DIR, r"fonts/arabica.ttf"), 70)
font2_arabic = userFont(os.path.join(BASE_DIR, r"fonts/arabica.ttf"), 50)
font3_arabic = userFont(os.path.join(BASE_DIR, r"fonts/arabica.ttf"), 30)
font4_arabic = userFont(os.path.join(BASE_DIR, r"fonts/arabica.ttf"), 20)

font1_sanskrit = userFont(os.path.join(BASE_DIR, r"fonts/sanskrit.ttf"), 70)
font2_sanskrit = userFont(os.path.join(BASE_DIR, r"fonts/sanskrit.ttf"), 50)
font3_sanskrit = userFont(os.path.join(BASE_DIR, r"fonts/sanskrit.ttf"), 30)
font4_sanskrit = userFont(os.path.join(BASE_DIR, r"fonts/sanskrit.ttf"), 20)


dfont1_univ = DynamicFont(clarity_city, 10, 70)
dfont2_univ = DynamicFont(clarity_city, 5, 50)
dfont3_univ = DynamicFont(
    clarity_city,
    20,
    60
)

dfont4_univ = DynamicFont(
    clarity_city,
    12,
    30
)

dfont5_univ = DynamicFont(
    clarity_city,
    10,
    50
)

dfont6_univ = DynamicFont(
    os.path.join(BASE_DIR, r"fonts/notosans.ttf"),
    20,
    50
)

dfont7_univ = DynamicFont(
    os.path.join(BASE_DIR, r"fonts/notosans.ttf"),
    20,
    50
)

dfont1_arabic = DynamicFont(os.path.join(BASE_DIR, r"fonts/arabica.ttf"), 10, 70)
dfont2_arabic = DynamicFont("arial", 5, 50)
dfont3_arabic = DynamicFont(
    os.path.join(BASE_DIR, r"fonts/arabica.ttf"),
    20,
    60
)

dfont4_arabic = DynamicFont(
    os.path.join(BASE_DIR, r"fonts/arabica.ttf"),
    12,
    30
)

dfont5_arabic = DynamicFont(
    os.path.join(BASE_DIR, r"fonts/arabica.ttf"),
    10,
    50
)

dfont6_arabic = DynamicFont(
    os.path.join(BASE_DIR, r"fonts/arabica.ttf"),
    20,
    50
)

dfont7_arabic = DynamicFont(
    os.path.join(BASE_DIR, r"fonts/arabica.ttf"),
    20,
    50
)

dfont1_sanskrit = DynamicFont(os.path.join(BASE_DIR, r"fonts/sanskrit.ttf"), 10, 70)
dfont2_sanskrit = DynamicFont(os.path.join(BASE_DIR, r"fonts/sanskrit.ttf"), 5, 50)
dfont3_sanskrit = DynamicFont(
    os.path.join(BASE_DIR, r"fonts/sanskrit.ttf"),
    20,
    60
)

dfont4_sanskrit = DynamicFont(
    os.path.join(BASE_DIR, r"fonts/sanskrit.ttf"),
    12,
    30
)

dfont5_sanskrit = DynamicFont(
    os.path.join(BASE_DIR, r"fonts/sanskrit.ttf"),
    10,
    50
)

dfont6_sanskrit = DynamicFont(
    os.path.join(BASE_DIR, r"fonts/sanskrit.ttf"),
    20,
    50
)

dfont7_sanskrit = DynamicFont(
    os.path.join(BASE_DIR, r"fonts/sanskrit.ttf"),
    20,
    50
)

def get_font(
        font_dict: dict[str, userFont | DynamicFont],
        lang: str,
        id: int,
        font_type: str | Literal["userFont"] | Literal["DynamicFont"] = "userFont"
    ):

    _char = ""

    if font_type.lower() == "userfont":
        _char = ""

    elif font_type.lower() == "dynamicfont":
        _char = "d"

    else:
        raise ValueError("font_type parameters value is unknown.")

    return font_dict[f"{_char}{lang.lower()}-{id}"]


logging.info("Fonts loaded.")
