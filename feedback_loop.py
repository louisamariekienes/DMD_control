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
        self.dmd_image = self.target_image
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
            # Making the values right for DMD control
            dmd_pattern = abs((self.dmd_image-1) * 255)
            plt.imshow(dmd_pattern)
            plt.show()
            dmd_thread = threading.Thread(target=self.dmd.start_sequence, args=(dmd_pattern,), kwargs={'duration': 1})
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

        self.nom_current_image = ccd_img_nobg/np.max(ccd_img_nobg)
        print("nom_current_image", np.min(self.nom_current_image), np.max(self.nom_current_image))
        # Implementation of error function
        # E_n = T - A * CCD_n
        #error = 1 - (self.target_image - self.nom_current_image)
        factor = 0.5
        error = np.where(self.target_image == 1, (self.target_image*factor - self.nom_current_image), 0)

        return error

    def calculate_RMSerror(self):
        h, w = self.target_image.shape
        sum = 0
        on_pixel = 0
        for y in range(h):
            for x in range(w):
                if self.target_image[y, x] == 1 and self.nom_current_image[y, x] != 0:
                    sum += ((self.target_image[y, x] - self.nom_current_image[y, x])/self.target_image[y, x])**2
                    on_pixel += 1
        rms_error = np.sqrt(sum*(1/on_pixel))*100
        return rms_error

    def floyd_steinberg(self, image):
        # image: np.array of shape (height, width), dtype=float, 0.0-1.0
        # works in-place!
        print("FSA; min", np.min(image), " max ", np.max(image))
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
        kp1 = 0.5
        ki = 10e-2

        new_dmd_img = self.dmd_image + kp1 * error_mtrx + ki * cumsum_error_mtrx
        new_dmd_img_nom = (new_dmd_img-np.min(new_dmd_img))/(np.max(new_dmd_img)-np.min(new_dmd_img))
        new_dmd_img_bin1 = np.round(new_dmd_img_nom)
        new_dmd_img_bin2 = abs(self.floyd_steinberg(new_dmd_img_nom))

        plot = True
        if plot:
            fig, ([ax1, ax2], [ax3, ax4]) = plt.subplots(2, 2, figsize=(8, 5))
            #ax1.imshow(np.where(self.dmd_image == 255, 0, 1))
            ax1.imshow(self.dmd_image)
            ax1.set_title('Current DMD image')
            ax2.imshow(self.nom_current_image)
            ax2.set_title('Current CCD image')
            ax4.imshow(error_mtrx)
            ax4.set_title('error_matrix')

            self.dmd_image = np.where(self.target_image == 1, 1 - new_dmd_img_bin, 0)
            ax3.imshow(self.dmd_image)
            ax3.set_title('Next DMD image')
            plt.show()





