from ids_peak import ids_peak

import matplotlib.pyplot as plt
import threading
import patterns
from camera import Camera
from feedback_loop import OpticalFeedbackLoop
from dmd_control import DigitalMicroMirrorDevice


def main():
    # Initialize DMD
    dmd_controller = DigitalMicroMirrorDevice(dummy=True)

    camera = Camera()

    camera.start_acquisition()
    thread = threading.Thread(target=camera.wait_for_signal, args=())
    thread.start()
    #camera.init_software_trigger()

    feedback_loop = OpticalFeedbackLoop(dmd_controller, camera)

    # Define target image
    target_image = patterns.calibration_pattern(dmd_controller.height, dmd_controller.width, 400)
    #plt.imshow(target_image)
    #plt.show()

    #target_image = patterns.calibration_pattern(30, 30, 10)

    feedback_loop.set_target_image(target_image)

    feedback_loop.run_feedback_loop()
    print('Feedback loop done')
    camera.close()
    print('finished')
    thread.join()


if __name__ == '__main__':
    main()
