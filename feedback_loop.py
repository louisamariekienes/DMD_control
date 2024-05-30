import time

import numpy as np


class OpticalFeedbackLoop:
    def __init__(self, dmd_controller, camera, trans_matrix):
        self.vocal = True
        self.dmd = dmd_controller
        self.camera = camera
        self.target_image = None
        self.trans_matrix = trans_matrix
        self.current_image = None
        self.target_image = None

    def set_target_image(self, target_image):
        self.target_image = target_image

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
        if self.vocal:
            print('in function adjust_potential')


    def run_feedback_loop(self ,target_image):
        self.set_target_image(target_image)
        while True:
            print(self.trans_matrix)
            # Capture current image
            current_image = self.camera.capture_image()
            if self.vocal:
                print("FBL after capturing image")
            #plt.imshow(current_image)
            #plt.show()
            # Calculate error
            error = self.calculate_error(current_image)

            # Adjust potential
            self.adjust_potential(error)

            # Break condition or sleep
            break
