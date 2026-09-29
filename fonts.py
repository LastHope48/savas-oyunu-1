import pygame
from userfont import userFont
import logging
from dfont import DynamicFont
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(filename)s: %(lineno)d [%(funcName)s] | %(message)s',
    filename="game.log"
)

pygame.font.init()

font1 = userFont("arial", 70)
font2 = userFont("arial", 50)
font3 = userFont("arial", 30)
font4 = userFont("arial", 20)

dfont1 = DynamicFont("arial", 10, 70)
dfont2 = DynamicFont("arial", 5, 50)

_notofont = pygame.font.Font(os.path.join(BASE_DIR, r"fonts/arabica.ttf"), 30)
notofont = userFont(os.path.join(BASE_DIR, r"fonts/arabica.ttf"), 30)
notofont.font = _notofont

fonts = [
    font1,
    font2,
    font3,
    font4,
    dfont1,
    dfont2,
    notofont
]

logging.info("Fonts loaded.")

def update_fonts(lang_dict, lang):
    global fonts, font1, font2, font3, font4, dfont1, dfont2, notofont

    for i, font in enumerate(fonts):
        if type(font) == userFont:
            fonts[i] = userFont(
                lang_dict[lang],
                font.size,
                font.bold,
                font.italic
            )

        elif type(font) == DynamicFont:
            fonts[i] = DynamicFont(
                lang_dict[lang],
                font.min_size,
                font.max_size
            )

    font1, font2, font3, font4, dfont1, dfont2, notofont = fonts

    return fonts

del logging
