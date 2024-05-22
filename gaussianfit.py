'''import numpy as np
from scipy.optimize import curve_fit
from PIL import Image
import matplotlib.pyplot as plt

# Load a single PNG image
png_filepath = 'figures/image_3.png'
png_pil_img = Image.open(png_filepath).convert('L')
image_array = np.asarray(png_pil_img)

# Display image shape and type
print(image_array.shape)
plt.imshow(image_array)
plt.show()

# Define a 2D Gaussian function
def gaussian_2d(xy, A, x0, y0, sigma_x, sigma_y):
    x, y = xy
    return A * np.exp(-((x - x0)**2 / (2 * sigma_x**2) + (y - y0)**2 / (2 * sigma_y**2)))


# Get the shape of the image array
height, width = image_array.shape

# Generate x and y coordinates for each pixel
x_coords, y_coords = np.meshgrid(np.arange(width), np.arange(height))

# Flatten the arrays for curve fitting
x_data = x_coords.flatten()
y_data = y_coords.flatten()
intensity_data = image_array.flatten()

# Initial guess for parameters (you can adjust these)
initial_params = [max(intensity_data), 100, 100, 10, 10]

# Fit the Gaussian function to the data
params, _ = curve_fit(gaussian_2d, (x_data, y_data), intensity_data, p0=initial_params)

# Extract the coordinates
x_coord, y_coord = params[1], params[2]


import numpy as np
import scipy.optimize as opt
from PIL import Image

# Load the image (replace 'my_image.png' with your actual image path)
png_filepath = 'figures/image_3.png'
png_pil_img = Image.open(png_filepath).convert('L')
image_array = np.asarray(png_pil_img)

print(image_array.shape)

# Define a 2D Gaussian function
def gaussian_2d(xy, A, x0, y0, sigma_x, sigma_y):
    x, y = xy
    return A * np.exp(-((x - x0)**2 / (2 * sigma_x**2) + (y - y0)**2 / (2 * sigma_y**2)))

# Initial guess for parameters (adjust as needed)
initial_guess = (3, 100, 100, 20, 40, 0, 10)

# Fit the Gaussian function to the data
popt, pcov = opt.curve_fit(gaussian_2d, (x, y), image_array.flatten(), p0=initial_guess)

# Extract the coordinates (xo, yo) from the fitted parameters
x_coords = popt[1::7]  # Extract every 7th element starting from index 1
y_coords = popt[2::7]  # Extract every 7th element starting from index 2

# Print the coordinates
for i in range(3):
    print(f"Point {i+1} coordinates (x, y): ({x_coords[i]:.2f}, {y_coords[i]:.2f})")

print(f"Coordinates (x, y): ({x_coord:.2f}, {y_coord:.2f})")
print(popt)
'''

import numpy as np
from scipy.ndimage import minimum_filter
from PIL import Image
import matplotlib.pyplot as plt

data = np.array([[2, 100, 1000, -5],
        [-10, 9, 1800, 0],
        [112, 10, 111, 100],
        [50, 110, 50, 140]])

# Load a single PNG image
png_filepath = 'figures/image_3.png'
png_pil_img = Image.open(png_filepath).convert('L')
image_array = np.asarray(png_pil_img)*(-1)
plt.imshow(image_array)
plt.show()

minima = (image_array == minimum_filter(image_array, 20, mode='nearest', cval=0.0))
# print(data)
# print(minima)
res = np.asarray(np.where(1 == minima))
print(type(res))

plt.imshow(minima)
plt.show()

