# author: Louisa Marie Kienesberger

import numpy as np
from ALP4 import *
import time
import matplotlib.pyplot as plt
from PIL import Image

height, width = 1080, 1920

def rect_pattern(height, width, size):
    img = np.zeros([height, width])

    centery = int(height / 2)
    centerx = int(width / 2)
    r = int(size / 2)

    if size == 1:
        img[centery, centerx] = (2 ** 8 - 1)
    elif size % 2 == 0:
        img[centery - r:centery + r - 1, centerx - r:centerx + r - 1] = (2 ** 8 - 1)
    elif size % 2 == 1:
        img[centery - r:centery + r, centerx - r:centerx + r] = (2 ** 8 - 1)

    return img

def ring_pattern(height, width, radius, ring_width):

    # Create a grid of coordinates
    y, x = np.ogrid[:height, :width]

    # Calculate the distance from the center of the array
    distance_from_center = np.sqrt((x - width / 2) ** 2 + (y - height / 2) ** 2)

    # Create a mask for the ring
    ring_mask = np.logical_and(distance_from_center >= radius - ring_width / 2,
                               distance_from_center <= radius + ring_width / 2)

    # Create a binary array with the ring imprinted
    img = np.zeros((height, width))
    img[ring_mask] = (2 ** 8 - 1)

    return img

def string_pattern(height, width, string_width):
    img = np.zeros((height, width))

    h = int(string_width/2)
    centery = int(height / 2)

    if string_width == 1:
        img[centery, :] = (2 ** 8 - 1)
    elif string_width % 2 == 0:
        img[centery - h:centery + h - 1, :] = (2 ** 8 - 1)
    elif string_width % 2 == 1:
        img[centery - h:centery + h, :] = (2 ** 8 - 1)

    return img


def image_pattern(height, width, image_path):
    # Open the input image
    img = Image.open(image_path)

    # Resize the image to fit the desired dimensions while maintaining aspect ratio
    img.thumbnail((width, height))

    # Convert the resized image to grayscale
    gray_img = img.convert('1')
    matrix = np.invert(np.array(gray_img))
    print(matrix)

    # Get the dimensions of the resized image
    resized_height, resized_width = matrix.shape

    # Calculate the starting indices for placing the matrix in the center
    start_row = (height - resized_height) // 2
    start_col = (width - resized_width) // 2

    # Create a matrix of desired dimensions and fill it with zeros
    final_matrix = np.zeros((height, width))

    # Place the resized matrix in the center of the final matrix
    final_matrix[start_row:start_row + resized_height, start_col:start_col + resized_width] = matrix

    return final_matrix


def speckle_disorder():
    pass


