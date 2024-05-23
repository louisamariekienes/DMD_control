import scipy.optimize as opt
from scipy.signal import find_peaks
import numpy as np
from PIL import Image, ImageFilter
import matplotlib.pyplot as plt

def twoD_Gaussian(xy, amplitude, xo, yo, sigma_x, sigma_y, theta, offset):
    x, y = xy
    xo = float(xo)
    yo = float(yo)
    a = (np.cos(theta)**2)/(2*sigma_x**2) + (np.sin(theta)**2)/(2*sigma_y**2)
    b = -(np.sin(2*theta))/(4*sigma_x**2) + (np.sin(2*theta))/(4*sigma_y**2)
    c = (np.sin(theta)**2)/(2*sigma_x**2) + (np.cos(theta)**2)/(2*sigma_y**2)
    g = offset + amplitude*np.exp( - (a*((x-xo)**2) + 2*b*(x-xo)*(y-yo)
                            + c*((y-yo)**2)))
    return g.ravel()


# Load your grayscale image into a NumPy array (replace with your actual data)

# use your favorite image processing library to load an image
filepath = 'figures/image_3.png'
image = Image.open(filepath).convert('L')
#im_blurred = image.filter(filter=ImageFilter.BLUR)
im = np.asarray(image)
h, w = im.shape
flattened_data = im.ravel()

x = np.linspace(0, w, w)
y = np.linspace(0, h, h)
x, y = np.meshgrid(x, y)

# initial guess of parameters
peaks, _ = find_peaks(flattened_data, distance=1000000, height=150)
print(peaks)
plt.plot(flattened_data)
plt.plot(peaks, flattened_data[peaks], 'x')
plt.show()

y_1, x_1 = np.unravel_index(peaks[0], im.shape)
initial_guess1 = (flattened_data[peaks[0]], x_1, y_1, 10, 10, 0, 0)
y_2, x_2 = np.unravel_index(peaks[1], im.shape)
initial_guess2 = (flattened_data[peaks[1]], x_2, y_2, 10, 10, 0, 0)
y_3, x_3 = np.unravel_index(peaks[2], im.shape)
initial_guess3 = (flattened_data[peaks[2]], x_3, y_3, 10, 10, 0, 0)
print(initial_guess1, initial_guess2, initial_guess3)



# find the optimal Gaussian parameters
popt1, pcov1 = opt.curve_fit(twoD_Gaussian, (x, y), flattened_data, p0=initial_guess1)
popt2, pcov2 = opt.curve_fit(twoD_Gaussian, (x, y), flattened_data, p0=initial_guess2)
popt3, pcov3 = opt.curve_fit(twoD_Gaussian, (x, y), flattened_data, p0=initial_guess3)
print(popt1)
print(popt2)
print(popt3)


# create new data with these parameters
data_fitted1 = twoD_Gaussian((x, y), *popt1)
data_fitted2 = twoD_Gaussian((x, y), *popt2)
data_fitted3 = twoD_Gaussian((x, y), *popt3)

fig, ax = plt.subplots(1, 1)
#ax.hold(True) For older versions. This has now been deprecated and later removed
ax.imshow(flattened_data.reshape(im.shape),  origin='lower', extent=(x.min(), x.max(), y.min(), y.max()))
ax.contour(x, y, data_fitted1.reshape(im.shape), 8, colors='w')
ax.contour(x, y, data_fitted2.reshape(im.shape), 8, colors='w')
ax.contour(x, y, data_fitted3.reshape(im.shape), 8, colors='w')
plt.show()

width, height = 1920, 1080

# Calculate the center of the matrix
centery = int(height / 2)
centerx = int(width / 2)

# Calculate the half size of the square
block_size = 20
half_block = block_size // 2
half_square = 400 // 2

# Define the corner positions for the square
top_left_start = (centerx - half_square, centery - half_square)
top_right_start = (centerx + half_square, centery - half_square)
bottom_left_start = (centerx - half_square, centery + half_square)

print(top_right_start, top_left_start, bottom_left_start)

