import cv2
import numpy as np

image = cv2.imread('1.png', -1)
original = image.copy()
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 11, 2)

cnts = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

cv2.drawContours(original, cnts[0], -1, (0,.0, 255), 3, lineType=cv2.LINE_AA)

max_width = 0
max_height = 0
for c in cnts[0]:
    x,y,w,h = cv2.boundingRect(c)
    if w > max_width:
        max_width = w
    if h > max_height:
        max_height = h

sprite_number = 0
for c in cnts[0]:
    x,y,w,h = cv2.boundingRect(c)
    ROI = image[y:y+h, x:x+w]
    bg = np.zeros((max_height, max_width, 4), np.uint8)
    x_offset = (max_width - w) // 2
    y_offset = (max_height - h) // 2
    bg[y_offset:y_offset+h, x_offset:x_offset+w, :4] = ROI
    cv2.imwrite('sprite_{}.png'.format(sprite_number), bg)
    sprite_number += 1

cv2.imshow('thresh', thresh)
cv2.imshow('contours', original)
cv2.waitKey()
cv2.destroyAllWindows()
