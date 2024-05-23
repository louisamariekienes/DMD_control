import numpy as np
import cv2
from scipy.signal import find_peaks
import scipy.optimize as opt

import patterns


# Import your DMD control framework


class OpticalFeedbackLoop:
    def __init__(self, dmd_controller, camera):
        self.dmd = dmd_controller
        self.camera = camera
        self.target_image = None
        self.trans_matrix = None

    def set_target_image(self, target_image):
        self.target_image = target_image

    def capture_image(self):
        print("here I am")
        # Capture image from the camera
        self.camera.make_image = True
        # wait until image has been made
        while self.camera.make_image:
            pass
        print("image captured")
        return self.camera.current_image

    def calculate_error(self, current_image):
        # Calculate error between current image and target image
        if self.target_image is None:
            print("Error: Target image is not set")
            return None
        #error = np.mean(np.abs(current_image - self.target_image))
        error = 10
        return error

    def adjust_potential(self, error):
        # Use the error to adjust the DMD pattern
        # Implement your logic here
        print(error)

    # Define a 2D Gaussian function
    def twoD_Gaussian(self, xy, amplitude, xo, yo, sigma_x, sigma_y, theta, offset):
        x, y = xy
        xo = float(xo)
        yo = float(yo)
        a = (np.cos(theta) ** 2) / (2 * sigma_x ** 2) + (np.sin(theta) ** 2) / (2 * sigma_y ** 2)
        b = -(np.sin(2 * theta)) / (4 * sigma_x ** 2) + (np.sin(2 * theta)) / (4 * sigma_y ** 2)
        c = (np.sin(theta) ** 2) / (2 * sigma_x ** 2) + (np.cos(theta) ** 2) / (2 * sigma_y ** 2)
        g = offset + amplitude * np.exp(- (a * ((x - xo) ** 2) + 2 * b * (x - xo) * (y - yo)
                                           + c * ((y - yo) ** 2)))
        return g.ravel()

    def get_coordinates_camera(self, current_image):
        im = np.asarray(current_image)
        h, w = im.shape
        flattened_data = im.ravel()

        x = np.linspace(0, w, w)
        y = np.linspace(0, h, h)
        x, y = np.meshgrid(x, y)

        # initial guess of parameters
        peaks, _ = find_peaks(flattened_data, distance=1000000, height=150)

        coords = []
        # Maybe here exception for checking if there are exactly 3 peaks
        for i in range(3):
            y_0, x_0 = np.unravel_index(peaks[i], im.shape)
            initial_guess = (flattened_data[peaks[i]], x_0, y_0, 10, 10, 0, 0)
            # find the optimal Gaussian parameters
            popt, pcov = opt.curve_fit(self.twoD_Gaussian, (x, y), flattened_data, p0=initial_guess)
            coords.append([popt[1], popt[2]])

        return np.array(coords).astype(np.float32)

    def calibrate_camera(self):
        cal_pattern, dmd_coords = patterns.calibration_pattern(self.dmd.height, self.dmd.width, 400)
        self.dmd.set_sequence(cal_pattern, duration=20)
        current_image = self.capture_image()
        camera_coords = self.get_coordinates_camera(current_image)
        #camera_coords = np.array([[789, 880], [1220, 1392], [1225, 399]])
        #dmd_image_coords = np.array([[340, 760], [740, 760], [340, 1160]])

        self.trans_matrix = cv2.getAffineTransform(dmd_coords, camera_coords)

        pass


    def run_feedback_loop(self):
        self.calibrate_camera()
        while True:
            # Capture current image
            current_image = self.capture_image()
            print("here I am after capturing image")

            # Calculate error
            error = self.calculate_error(current_image)

            # Adjust potential
            self.adjust_potential(error)

            # Break condition or sleep
            break
            # Implement your logic here
