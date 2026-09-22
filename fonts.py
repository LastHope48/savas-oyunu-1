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

_notofont = pygame.font.Font(os.path.join(BASE_DIR,"arabica.ttf"), 30)
notofont = userFont(os.path.join(BASE_DIR,"arabica.ttf"), 30)
notofont.font = _notofont
logging.info("Fonts loaded.")

del logging
