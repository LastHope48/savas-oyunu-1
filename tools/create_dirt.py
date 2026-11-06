import cv2
import numpy as np
from copy import deepcopy
import colours

canvas = np.zeros((300, 1000, 3), dtype=np.uint8)
canvas2 = np.zeros((500, 500, 3), dtype=np.uint8)

color_continue = [0, 255, 0]
color_1 = [5, 117, 183]
color_2 = [5, 84, 133]
color_3 = [5, 65, 105]

color_continue2 = [145, 143, 141]
color_1_2 = [120, 119, 117]
color_2_2 = [237, 139, 40]
color_3_2 = [120, 119, 117]

def create_dirt(name, color_continue, color1, color2, color3):
    img = deepcopy(canvas)

    for y in range(img.shape[0]):
        for x in range(img.shape[1]):
            if y <= 75:
                if y <= 6:
                    img[y, x] = color_continue
                    continue
                if y % 4 == 0:
                    if x % 4 == 0:
                        img[y, x] = color1
                    else:
                        img[y, x] = color2
                else:
                    if x % 4 == 0:
                        img[y, x] = color2
                    else:
                        img[y, x] = color1
            else:
                img[y, x] = color3

    cv2.imwrite(name, img)

def create_map(name, color1, color2):
    img = deepcopy(canvas2)

    for y in range(img.shape[0]):
        for x in range(img.shape[1]):
            if y % 2 == 0:
                if x % 2 == 0:
                    img[y, x] = color1

                else:
                    img[y, x] = color2

            else:
                if x % 2 == 0:
                    img[y, x] = color2

                else:
                    img[y, x] = color1

    cv2.imwrite(name, img)

create_dirt("images/dirt_pattern.png", color_continue, color_1, color_2, color_3)
create_dirt("images/metaldirt_pattern.png", color_continue2, color_1_2, color_2_2, color_3_2)

create_map("images/metalic_map.png", color_continue2, colours.lighter(color_continue2, 30))
