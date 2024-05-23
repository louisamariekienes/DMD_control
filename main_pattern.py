# author: Louisa Marie Kienesberger

import numpy as np
import patterns
import matplotlib.pyplot as plt
import pyspeckle


def main():

    width, height = 1920, 1080
    img = patterns.calibration_pattern(width, height, 400)

    plt.imshow(img, cmap='Greys')
    plt.show()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()
