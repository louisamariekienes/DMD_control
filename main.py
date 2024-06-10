from ids_peak import ids_peak

import matplotlib.pyplot as plt
import threading
import patterns
from camera import Camera
from feedback_loop import OpticalFeedbackLoop
from dmd_control import DigitalMicroMirrorDevice
import numpy as np


def main():
    # Initialize DMD
    dmd_controller = DigitalMicroMirrorDevice(dummy=False)

    camera = Camera()

    camera.set_exposure_time(3000)
    camera.init_software_trigger()
    camera.start_acquisition()

    camera_thread = threading.Thread(target=camera.wait_for_signal, args=())
    camera_thread.start()

    # Calibration of the CCD image to the DMD
    #trans_matrix = camera.calibrate_camera(dmd_controller)
    #print(trans_matrix)

    #trans_matrix = np.array([[2.99001059e-01, -2.76386613e-01, 8.44264258e+02], [2.75533658e-01, 2.99750983e-01, -6.45481647e+01]])
    trans_matrix = np.array([[2.99900894e-01, -2.76227593e-01, 8.57316854e+02], [2.76379554e-01,  2.99818977e-01, -5.26320542e+01]])
    # Define target image
    target_image = patterns.rect_pattern(dmd_controller.height, dmd_controller.width, 400)

    feedback_loop = OpticalFeedbackLoop(dmd_controller, camera, trans_matrix)

    dmd_image = feedback_loop.run_feedback_loop(target_image)
    print('Feedback loop done')
    camera.close()
    dmd_controller.close()
    print('finished')
    camera_thread.join()


if __name__ == '__main__':
    main()

