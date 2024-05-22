import numpy as np
from dmd_control import DigitalMicroMirrorDevice


# Import your DMD control framework

class OpticalFeedbackLoop:
    def __init__(self, dmd_controller, camera):
        self.dmd = dmd_controller
        self.camera = camera
        self.target_image = None

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
    def gaussian_2d(xy, A, x0, y0, sigma_x, sigma_y):
        x, y = xy
        return A * np.exp(-((x - x0) ** 2 / (2 * sigma_x ** 2) + (y - y0) ** 2 / (2 * sigma_y ** 2)))

    def run_feedback_loop(self):
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
