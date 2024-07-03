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
    trans_matrix = camera.calibrate_camera(dmd_controller)
    print(trans_matrix)

    #trans_matrix = np.array([[ 3.05333170e-01, -2.79312256e-01,  8.41659153e+02], [ 2.75798595e-01,  3.03630462e-01, -7.89321620e+01]])
    # Define target image
    #target_image = patterns.rect_pattern(dmd_controller.height, dmd_controller.width, 400)
    #target_image = patterns.ring_pattern(dmd_controller.height, dmd_controller.width, 200, 40)
    #target_image = patterns.speckle_disorder(dmd_controller.height, dmd_controller.width, 10, 0.5)

    #feedback_loop = OpticalFeedbackLoop(dmd_controller, camera, trans_matrix)

    #dmd_image = feedback_loop.run_feedback_loop(target_image)
    #print('Feedback loop done')

    # Just send an image

    camera.close()
    dmd_controller.close()
    print('finished')
    camera_thread.join()


if __name__ == '__main__':
    main()

