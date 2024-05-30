import numpy as np
import cv2 as cv
from PIL import Image
import matplotlib.pyplot as plt
from dmd_control import DigitalMicroMirrorDevice
import patterns

filepath = 'figures/image_16.png'
image = Image.open(filepath).convert('L')
im = np.asarray(image)


#camera_coord = np.array([[789, 880], [1220, 1392], [1225, 399]]).astype(np.float32)
#camera_coord = np.array([[1188.1548684459847, 1592.2850790863133], [1244.3545587253743, 205.67869373260044], [521.2555116404054, 870.4500489384596]]).astype(np.float32)
camera_coord = np.array([[1189.071587151918, 1590.7301765529498], [1245.2603488514508, 204.30487868383136], [521.9114223991563, 868.6797376239697]]).astype(np.float32)
dmd_image_coord = np.array([[1160, 340], [760, 740], [760, 340]]).astype(np.float32)
dmd = DigitalMicroMirrorDevice(dummy=False)
cal_pattern, dmd_coords = patterns.calibration_pattern(dmd.height, dmd.width, 400)

print(dmd_image_coord)
dmd_coords_switched = np.flip(dmd_coords, axis=None)
print(dmd_coords_switched)

warp_mat = cv.getAffineTransform(camera_coord, dmd_coords_switched)

print(warp_mat)

warp_dst = cv.warpAffine(im, warp_mat, (1920, 1080))

print(warp_dst.shape)

plt.imshow(warp_dst)
plt.show()


