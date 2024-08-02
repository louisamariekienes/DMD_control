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
    calibration = False
    perform_fbl = True
    dmd_controller = DigitalMicroMirrorDevice(dummy=False)

    camera = Camera()

    camera.set_exposure_time(1450)
    camera.init_software_trigger()
    camera.start_acquisition()

    camera_thread = threading.Thread(target=camera.wait_for_signal, args=())
    camera_thread.start()

    # Calibration of the CCD image to the DMD
    if calibration:
        trans_matrix = camera.calibrate_camera(dmd_controller)
        print(trans_matrix)
    else:
        trans_matrix = np.array([[3.12093830e-01, -2.64751600e-01,  8.26052258e+02], [2.65910267e-01, 3.11401757e-01, -1.00719890e+02]])

    if perform_fbl:
        # Define target image
        target_image = patterns.rect_pattern(dmd_controller.height, dmd_controller.width, 400)

        feedback_loop = OpticalFeedbackLoop(dmd_controller, camera, trans_matrix)

        dmd_image = feedback_loop.run_feedback_loop(target_image)
        print('Feedback loop done')

    camera.close()
    dmd_controller.close()
    print('Finished')
    camera_thread.join()


if __name__ == '__main__':
    main()

