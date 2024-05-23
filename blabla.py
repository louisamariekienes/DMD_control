import numpy as np
import cv2 as cv
from PIL import Image
import matplotlib.pyplot as plt

filepath = 'figures/image_3.png'
image = Image.open(filepath).convert('L')
im = np.asarray(image)


camera_coord = np.array([[789, 880], [1220, 1392], [1225, 399]]).astype(np.float32)
dmd_image_coord = np.array([[340, 760], [740, 760], [340, 1160]]).astype(np.float32)

warp_mat = cv.getAffineTransform(camera_coord, dmd_image_coord)

print(warp_mat)

warp_dst = cv.warpAffine(im, warp_mat, (1080, 1920))

print(warp_dst.shape)

plt.imshow(warp_dst)
plt.show()


