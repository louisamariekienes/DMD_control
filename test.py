from ids_peak import ids_peak

import patterns
from camera import Camera
from feedback_loop import OpticalFeedbackLoop
from dmd_control import DigitalMicroMirrorDevice


def main():
    # Initialize DMD
    dmd_controller = DigitalMicroMirrorDevice(dummy=True)

    camera = Camera()

    camera.start_acquisition()

    feedback_loop = OpticalFeedbackLoop(dmd_controller, camera)

    # Define target image
    target_image = patterns.calibration_pattern(dmd_controller.height, dmd_controller.width, 400)


    feedback_loop.set_target_image(target_image)

    feedback_loop.run_feedback_loop()

    camera.stop_acquisition()


if __name__ == '__main__':
    main()
