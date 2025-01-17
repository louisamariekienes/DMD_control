# author: Louisa Marie Kienesberger

import numpy as np
import patterns
import matplotlib.pyplot as plt
import scienceplots
from PIL import Image

plt.style.use('science')
plt.rcParams["text.usetex"] = True


def main():

    width, height = 1920, 1080

    square_gs = patterns.rect_pattern(height, width, 400)*0.6
    dmd_image = floyd_steinberg(square_gs)

    plt.imshow(dmd_image)
    plt.show()


def floyd_steinberg(image):
    # image: np.array of shape (height, width), dtype=float, 0.0-1.0
    # works in-place!
    h, w = image.shape
    for y in range(h):
        for x in range(w):
            old = image[y, x]
            new = np.round(old)
            image[y, x] = new
            error = old - new
            #    precomputing the constants helps
            if x + 1 < w:
                image[y, x + 1] += error * 0.4375  # right, 7 / 16
            if (y + 1 < h) and (x + 1 < w):
                image[y + 1, x + 1] += error * 0.0625  # right, down, 1 / 16
            if y + 1 < h:
                image[y + 1, x] += error * 0.3125  # down, 5 / 16
            if (x - 1 >= 0) and (y + 1 < h):
                image[y + 1, x - 1] += error * 0.1875  # left, down, 3 / 16
    return image * 255


    # fig, ([ax1, ax2], [ax3, ax4]) = plt.subplots(2, 2, figsize=(8, 4))
    # ax1.imshow(patterns.rect_pattern(height, width, 400), cmap='gray_r')
    # ax1.set_ylabel('pixel')
    # ax2.imshow(patterns.ring_pattern(height, width, 200, 50), cmap='gray_r')
    # ax3.imshow(patterns.string_pattern(height, width, 50), cmap='gray_r')
    # ax3.set_ylabel('pixel')
    # ax3.set_xlabel('pixel')
    # ax4.set_xlabel('pixel')
    # ax4.imshow(patterns.image_pattern(height, width, "figures/diewildenatomis_schwarz.jpg", (1000, 800)), cmap='gray_r')

    # fig, ([ax1, ax2, ax3]) = plt.subplots(1, 3, figsize=(9, 3))
    # ax1.imshow(patterns.speckle_disorder(height, width, 1, 0.5), cmap='gray_r')
    # ax1.set_ylabel('pixel')
    # ax1.set_xlabel('pixel')
    # ax2.imshow(patterns.speckle_disorder(height, width, 6, 0.7), cmap='gray_r')
    # ax2.set_xlabel('pixel')
    # ax3.imshow(patterns.speckle_disorder(height, width, 15, 0.3), cmap='gray_r')
    # ax3.set_xlabel('pixel')

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()
