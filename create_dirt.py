import cv2

img = cv2.imread("images/dirt.png")

for y in range(img.shape[0]):
    for x in range(img.shape[1]):
        if y <= 75:
            if y <= 6:
                img[y, x] = [0, 255, 0]
                continue
            if y % 4 == 0:
                if x % 4 == 0:
                    img[y, x] = [5, 117, 183]
                else:
                    img[y, x] = [5, 84, 133]
            else:
                if x % 4 == 0:
                    img[y, x] = [5, 84, 133]
                else:
                    img[y, x] = [5, 117, 183]
        else:
            img[y, x] = [5, 65, 105]

cv2.imwrite("images/dirt_pattern.png", img)

