import time

import numpy as np
import cv2 as cv
import matplotlib.pyplot as plt
import threading

class OpticalFeedbackLoop:
    def __init__(self, dmd_controller, camera, trans_matrix):
        self.vocal = True
        self.dmd = dmd_controller
        self.camera = camera
        self.target_image = None
        self.trans_matrix = trans_matrix
        self.current_image = None
        self.nom_current_image = None
        self.target_image = None
        self.dmd_image = None


    def run_feedback_loop(self, target_image):
        self.set_target_image(target_image)
        self.dmd_image = abs((self.target_image-1)*255)
        i = 1
        cumsum_error_mtrx = np.zeros((self.dmd.height, self.dmd.width))


        # Taking a backgorund image for substraction - Doesn't show any effect, so not used
        # dmd_thread = threading.Thread(target=self.dmd.start_sequence,
        #                              args=(np.ones([self.dmd.height, self.dmd.width]) * 255,),
        #                              kwargs={'duration': 1})
        # cam_thread = threading.Thread(target=self.camera.capture_image, kwargs={'save_image': True})

        # dmd_thread.start()
        # cam_thread.start()

        # dmd_thread.join()
        # cam_thread.join()

        # bg_image = self.camera.current_image


        while True:
            dmd_thread = threading.Thread(target=self.dmd.start_sequence, args=(self.dmd_image,), kwargs={'duration': 1})
            cam_thread = threading.Thread(target=self.camera.capture_image, kwargs={'save_image': True})

            dmd_thread.start()
            cam_thread.start()

            dmd_thread.join()
            cam_thread.join()

            if self.vocal:
                print("FBL after capturing image")

            # Calculate error matrix
            error_mtrx = self.calculate_error_mtrx(self.camera.current_image)

            cumsum_error_mtrx += error_mtrx

            # Calculate RMS error
            rms_error = self.calculate_RMSerror()

            print("RMS error     ", rms_error)

            # Adjust DMD image according to errormatrix
            self.adjust_dmd_image(error_mtrx, cumsum_error_mtrx)

            # Break condition or sleep
            i += 1

            if i > 5:
                break
        return self.dmd_image


    def set_target_image(self, target_image):
        self.target_image = target_image

    def calculate_error_mtrx(self, current_image):
        # Calculate error between current image and target image
        if self.target_image is None:
            print("Error: Target image is not set")
            return None

        # Normiertes CCD image
        ccd_img = cv.warpAffine(current_image, self.trans_matrix, (self.dmd.width, self.dmd.height))
        ccd_img_nobg = np.where(self.target_image == 0, self.target_image, ccd_img)

        self.nom_current_image = ccd_img_nobg/255

        # Implementation of error function
        # E_n = T - A * CCD_n
        error = 1 - (self.target_image - self.nom_current_image)
        # error = self.target_image - self.nom_current_image

        return error

    def calculate_RMSerror(self):
        h, w = self.target_image.shape
        sum = 0
        for y in range(h):
            for x in range(w):
                if self.target_image[y, x] == 1 and self.nom_current_image[y, x] != 0:
                    sum += ((self.target_image[y, x] - self.nom_current_image[y, x]) / self.nom_current_image[y, x])**2
        rms_error = np.sqrt(sum*(1/(self.dmd.width*self.dmd.height)))*100
        return rms_error


    def floyd_steinberg(self, image):
        # image: np.array of shape (height, width), dtype=float, 0.0-1.0
        # works in-place!
        #plt.imshow(image)
        #plt.show()
        h, w = image.shape
        for y in range(h):
            for x in range(w):
                if self.target_image[y, x] == 1:
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
                else:
                    image[y, x] = 0
        return image

    def adjust_dmd_image(self, error_mtrx, cumsum_error_mtrx):
        kp1 = -0.3
        ki = -10e-5

        new_dmd_img = self.target_image + kp1 * error_mtrx # + ki * cumsum_error_mtrx
        new_dmd_img_bin = self.floyd_steinberg(new_dmd_img)

        fig, ([ax1, ax2, ax3]) = plt.subplots(1, 3, figsize=(10, 5))
        ax1.imshow(np.where(self.dmd_image == 255, 0, 1))
        ax1.set_title('Current DMD image')
        ax2.imshow(self.nom_current_image)
        ax2.set_title('Current CCD image')
        ax3.imshow(error_mtrx)
        ax3.set_title('error_matrix')
        plt.show()

        self.dmd_image = np.where(new_dmd_img_bin == 1, 0, 255)


