import time

import numpy as np
import cv2 as cv
import matplotlib.pyplot as plt
import threading

class OpticalFeedbackLoop:
    def __init__(self, dmd_controller, camera, trans_matrix):
        self.verbose = True
        self.dmd = dmd_controller
        self.camera = camera
        self.trans_matrix = trans_matrix

    def run_feedback_loop(self, target_image):

        # intensity threshold, defines final intansity of homogenous pattern
        i_th = 0.4
        target_image_gs = target_image * i_th
        dmd_image = floyd_steinberg(target_image_gs)

        i = 1
        cumsum_error_mtrx = np.zeros((self.dmd.height, self.dmd.width))

        while True:
            # Making the values right for DMD control
            # CHECK which direction is 0 and which 255 for dmd_image
            plt.imshow(dmd_image)
            plt.show()
            dmd_thread = threading.Thread(target=self.dmd.start_sequence, args=(dmd_image,), kwargs={'duration': 1})
            cam_thread = threading.Thread(target=self.camera.capture_image, kwargs={'save_image': True})

            dmd_thread.start()
            cam_thread.start()

            dmd_thread.join()
            cam_thread.join()

            if self.verbose:
                print("FBL after capturing image")

            # Calculate error matrix
            error_mtrx = self.calculate_error_mtrx(self.camera.current_image, target_image_gs)

            cumsum_error_mtrx += error_mtrx

            # Calculate RMS error
            rms_error = self.calculate_RMSerror(target_image_gs, error_mtrx)
            print("RMS error ([0, 50]):     ", rms_error)

            # Break condition or sleep
            rms_error_th = 0
            if rms_error <= rms_error_th:
                break

            # Adjust DMD image according to error matrix
            dmd_image = self.adjust_dmd_image(dmd_image, error_mtrx, cumsum_error_mtrx)

            i += 1
            if i > 5:
                break

        return dmd_image, self.camera.current_image

    def calculate_error_mtrx(self, current_image, target_image_gs):
        # Calculate error between current image and target image
        # Normiertes CCD image
        ccd_img = cv.warpAffine(current_image, self.trans_matrix, (self.dmd.width, self.dmd.height))

        # Implementation of error function
        # E_n = T - A * CCD_n
        error = np.where(target_image_gs != 0, (target_image_gs - ccd_img), 0)

        return error

    def calculate_RMSerror(self, target_image_gs, err_mtrx):
        h, w = target_image_gs.shape
        form_sum = 0
        on_pixel = 0
        for y in range(h):
            for x in range(w):
                if target_image_gs[y, x] != 0:
                    form_sum += (err_mtrx[y, x]/target_image_gs[y, x])**2
                    on_pixel += 1
        rms_error = np.sqrt(form_sum*(1/on_pixel))*100
        return rms_error

    def adjust_dmd_image(self, dmd_image, error_mtrx, cumsum_error_mtrx):
        # parameters for feedback loop

        kp1 = 0.5
        kp3 = 0
        ki = 0

        new_dmd_img = dmd_image + kp1 * error_mtrx + ki * cumsum_error_mtrx + kp3 * error_mtrx ** 3
        return new_dmd_img


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
            # precomputing the constants helps
            if x + 1 < w:
                image[y, x + 1] += error * 0.4375  # right, 7 / 16
            if (y + 1 < h) and (x + 1 < w):
                image[y + 1, x + 1] += error * 0.0625  # right, down, 1 / 16
            if y + 1 < h:
                image[y + 1, x] += error * 0.3125  # down, 5 / 16
            if (x - 1 >= 0) and (y + 1 < h):
                image[y + 1, x - 1] += error * 0.1875  # left, down, 3 / 16

    return image



