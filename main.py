# author: Louisa Marie Kienesberger

import numpy as np
import patterns
import matplotlib.pyplot as plt


def main():

    width, height = 1920, 1080

    test_img1 = patterns.rect_pattern(height, width, 100)
    test_img2 = patterns.rect_pattern(height, width, 10)
    test_img3 = patterns.ring_pattern(height, width, 400, 80)
    test_img4 = patterns.ring_pattern(height, width, 100, 20)
    test_img5 = patterns.string_pattern(height, width, 100)
    test_img6 = patterns.string_pattern(height, width, 10)
    test_img7 = patterns.image_pattern(height, width, 'figures/wien_skyline.png')
    test_img8 = patterns.image_pattern(height, width, 'figures/KL_skyline.jpg')

    # Create the figure and subplots
    fig, axes = plt.subplots(nrows=4, ncols=2, figsize=(5, 5))

    axes[0, 0].imshow(test_img1, cmap='Greys')
    axes[0, 1].imshow(test_img2, cmap='Greys')
    axes[1, 0].imshow(test_img3, cmap='Greys')
    axes[1, 1].imshow(test_img4, cmap='Greys')
    axes[2, 0].imshow(test_img5, cmap='Greys')
    axes[2, 1].imshow(test_img6, cmap='Greys')
    axes[3, 0].imshow(test_img7, cmap='Greys')
    axes[3, 1].imshow(test_img8, cmap='Greys')
    plt.show()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()
