import sys
import os
from os.path import exists
import copy
import numpy as np
from scipy.signal import find_peaks
import cv2
import threading
import patterns
import time
import scipy.optimize as opt
import cv2 as cv

from ids_peak import ids_peak
from ids_peak_ipl import ids_peak_ipl
from ids_peak import ids_peak_ipl_extension

import matplotlib.pyplot as plt

TARGET_PIXEL_FORMAT = ids_peak_ipl.PixelFormatName_Mono8


class Camera:

    def __init__(self):
        ids_peak.Library.Initialize()
        self.device_manager = ids_peak.DeviceManager.Instance()

        self.vocal = False
        self.ipl_image = None
        self.current_image = None
        self.save_image = False
        self._device = None
        self._datastream = None
        self.acquisition_running = False
        self.node_map = None
        self.make_image = False
        self._buffer_list = []

        self.killed = False

        self._get_device()
        self._image_converter = ids_peak_ipl.ImageConverter()


    def __del__(self):
        self.close()

    def _get_device(self):
        # Update device manager to make sure every available device is listed
        self.device_manager.Update()
        if self.device_manager.Devices().empty():
            print("No device found. Exiting Program.")
            sys.exit(1)
        selected_device = None

        # Initialize first device found if only one is available
        if len(self.device_manager.Devices()) == 1:
            selected_device = 0
        else:
            # List all available devices
            for i, device in enumerate(self.device_manager.Devices()):
                # Display device information
                print(
                    f"{str(i)}:  {device.ModelName()} ("
                    f"{device.ParentInterface().DisplayName()} ; "
                    f"{device.ParentInterface().ParentSystem().DisplayName()} v."
                    f"{device.ParentInterface().ParentSystem().version()})")
            while True:
                try:
                    # Let the user decide which device to open
                    selected_device = int(input("Select device to open: "))
                    if selected_device < len(self.device_manager.Devices()):
                        break
                    else:
                        print("Invalid ID.")
                except ValueError:
                    print("Please enter a correct id.")
                    continue

        # Opens the selected device in control mode
        self._device = self.device_manager.Devices()[selected_device].OpenDevice(
            ids_peak.DeviceAccessType_Control)
        # Get device's control nodes
        self.node_map = self._device.RemoteDevice().NodeMaps()[0]

        # Load the default settings
        self.node_map.FindNode("UserSetSelector").SetCurrentEntry("Default")
        self.node_map.FindNode("UserSetLoad").Execute()
        self.node_map.FindNode("UserSetLoad").WaitUntilDone()
        if self.vocal:
            print("Finished opening device!")

    def _init_data_stream(self):
        # Open device's datastream
        self._datastream = self._device.DataStreams()[0].OpenDataStream()
        # Allocate image buffer for image acquisition
        self.revoke_and_allocate_buffer()

    def conversion_supported(self, source_pixel_format: int) -> bool:
        """
        Check if the image_converter supports the conversion of the
        `source_pixel_format` to our `TARGET_PIXEL_FORMAT`
        """
        return any(
            TARGET_PIXEL_FORMAT == supported_pixel_format
            for supported_pixel_format in
            self._image_converter.SupportedOutputPixelFormatNames(
                source_pixel_format))

    def init_software_trigger(self):
        allEntries = self.node_map.FindNode("TriggerSelector").Entries()
        availableEntries = []
        for entry in allEntries:
            if (entry.AccessStatus() != ids_peak.NodeAccessStatus_NotAvailable
                    and entry.AccessStatus() != ids_peak.NodeAccessStatus_NotImplemented):
                availableEntries.append(entry.SymbolicValue())

        if len(availableEntries) == 0:
            raise Exception("Software Trigger not supported")
        elif "ExposureStart" not in availableEntries:
            self.node_map.FindNode("TriggerSelector").SetCurrentEntry(
                availableEntries[0])
        else:
            self.node_map.FindNode(
                "TriggerSelector").SetCurrentEntry("ExposureStart")
        self.node_map.FindNode("TriggerMode").SetCurrentEntry("On")
        self.node_map.FindNode("TriggerSource").SetCurrentEntry("Software")

    def close(self):
        self.stop_acquisition()

        # If datastream has been opened, revoke and deallocate all buffers
        if self._datastream is not None:
            try:
                for buffer in self._datastream.AnnouncedBuffers():
                    self._datastream.RevokeBuffer(buffer)
            except Exception as e:
                print(f"Exception (close): {str(e)}")

        self.killed = True

    def start_acquisition(self):
        if self._device is None:
            return False
        if self.acquisition_running is True:
            return True

        if self._datastream is None:
            self._init_data_stream()

        for buffer in self._buffer_list:
            self._datastream.QueueBuffer(buffer)
        try:
            # Lock parameters that should not be accessed during acquisition
            self.node_map.FindNode("TLParamsLocked").SetValue(1)

            image_width = self.node_map.FindNode("Width").Value()
            image_height = self.node_map.FindNode("Height").Value()
            input_pixel_format = ids_peak_ipl.PixelFormat(
                self.node_map.FindNode("PixelFormat").CurrentEntry().Value())

            # Pre-allocate conversion buffers to speed up first image conversion
            # while the acquisition is running
            # NOTE: Re-create the image converter, so old conversion buffers
            #       get freed
            self._image_converter = ids_peak_ipl.ImageConverter()
            self._image_converter.PreAllocateConversion(
                input_pixel_format, TARGET_PIXEL_FORMAT,
                image_width, image_height)

            self._datastream.StartAcquisition()
            self.node_map.FindNode("AcquisitionStart").Execute()
            self.node_map.FindNode("AcquisitionStart").WaitUntilDone()
            self.acquisition_running = True
            if self.vocal:
                print("Acquisition started!")
        except Exception as e:
            print(f"Exception (start acquisition): {str(e)}")
            return False
        return True

    def stop_acquisition(self):
        if self._device is None:
            return
        if self.acquisition_running is False:
            return
        try:
            self.node_map.FindNode("AcquisitionStop").Execute()

            self._datastream.StopAcquisition(
                ids_peak.AcquisitionStopMode_Default)
            # Discard all buffers from the acquisition engine
            # They remain in the announced buffer pool
            self._datastream.Flush(
                ids_peak.DataStreamFlushMode_DiscardAll)

            self.acquisition_running = False

            # Unlock parameters
            self.node_map.FindNode("TLParamsLocked").SetValue(0)
            if self.vocal:
                print('Acquisition stopped')
        except Exception as e:
            print(str(e))

    def software_trigger(self):
        if self.vocal:
            print("Executing software trigger")
        self.node_map.FindNode("TriggerSoftware").Execute()
        self.node_map.FindNode("TriggerSoftware").WaitUntilDone()
        if self.vocal:
            print("Finished.")

    def _valid_name(self, path: str, ext: str):
        num = 0

        def build_string():
            return f"{path}_{num}{ext}"

        while exists(build_string()):
            num += 1
        return build_string()

    def revoke_and_allocate_buffer(self):
        if self._datastream is None:
            return

        try:
            # Check if buffers are already allocated
            if self._datastream is not None:
                # Remove buffers from the announced pool
                for buffer in self._datastream.AnnouncedBuffers():
                    self._datastream.RevokeBuffer(buffer)
                self._buffer_list = []

            payload_size = self.node_map.FindNode("PayloadSize").Value()
            buffer_amount = self._datastream.NumBuffersAnnouncedMinRequired()

            for _ in range(buffer_amount):
                buffer = self._datastream.AllocAndAnnounceBuffer(payload_size)
                self._buffer_list.append(buffer)
            if self.vocal:
                print("Allocated buffers!")
        except Exception as e:
           print("error")

    def change_pixel_format(self, pixel_format: str):
        try:
            self.node_map.FindNode("PixelFormat").SetCurrentEntry(pixel_format)
            self.revoke_and_allocate_buffer()
        except Exception as e:
            print(f"Cannot change pixelformat: {str(e)}")

    def send_image(self):
        cwd = os.getcwd() + '\\figures'

        buffer = self._datastream.WaitForFinishedBuffer(1000)
        if self.vocal:
            print("Buffered image!")

        # Get image from buffer (shallow copy)
        self.ipl_image = ids_peak_ipl_extension.BufferToImage(buffer)


        # This creates a deep copy of the image, so the buffer is free to be used again
        # NOTE: Use `ImageConverter`, since the `ConvertTo` function re-allocates
        #       the converison buffers on every call
        converted_ipl_image = self._image_converter.Convert(self.ipl_image, TARGET_PIXEL_FORMAT)

        # Get raw image data from converted image and construct a QImage from it
        self.current_image = copy.copy(converted_ipl_image.get_numpy_2D())

        if self.save_image:
            ids_peak_ipl.ImageWriter.WriteAsPNG(
                self._valid_name(cwd + "/image", ".png"), converted_ipl_image)
            self.save_image = False
            if self.vocal:
                print("Saved!")

        self._datastream.QueueBuffer(buffer)

    def wait_for_signal(self):
        while not self.killed:
            try:
                if self.make_image is True:
                    # Call software trigger to load image
                    self.software_trigger()
                    # Get image and save it as file, if that option is enabled
                    self.send_image()
                    self.make_image = False
            except Exception as e:
                self.make_image = False

    def set_exposure_time(self, exposuretime):
        try:
            self.node_map.FindNode("ExposureTime").SetValue(exposuretime)
        except ids_peak.Exception:
            print(f"Could not set exposure time!")

    def capture_image(self, save_image=False):
        time.sleep(0.5)
        self.save_image = save_image
        # Capture image from the camera
        self.make_image = True
        # wait until image has been made
        while self.make_image:
            pass
        if self.vocal:
            print("image captured")

        # Define a 2D Gaussian function
    def twoD_Gaussian(self, xy, amplitude, xo, yo, sigma_x, sigma_y, theta, offset):
        x, y = xy
        xo = float(xo)
        yo = float(yo)
        a = (np.cos(theta) ** 2) / (2 * sigma_x ** 2) + (np.sin(theta) ** 2) / (2 * sigma_y ** 2)
        b = -(np.sin(2 * theta)) / (4 * sigma_x ** 2) + (np.sin(2 * theta)) / (4 * sigma_y ** 2)
        c = (np.sin(theta) ** 2) / (2 * sigma_x ** 2) + (np.cos(theta) ** 2) / (2 * sigma_y ** 2)
        g = offset + amplitude * np.exp(- (a * ((x - xo) ** 2) + 2 * b * (x - xo) * (y - yo)
                                           + c * ((y - yo) ** 2)))
        return g.ravel()

    def get_cal_coords(self, current_image):
        h, w = current_image.shape
        flattened_data = current_image.ravel()

        x = np.linspace(0, w, w)
        y = np.linspace(0, h, h)
        x, y = np.meshgrid(x, y)

        # initial guess of parameters
        peaks, _ = find_peaks(flattened_data, distance=1000000, height=100)
        #print(peaks)

        #plt.plot(flattened_data)
        #plt.plot(peaks, flattened_data[peaks], 'x')
        #plt.show()

        coords = []
        popt_array = []

        # Maybe here exception for checking if there are exactly 3 peaks
        for i in range(3):
            print(i, ' gaussian fit')
            y_0, x_0 = np.unravel_index(peaks[i], current_image.shape)
            initial_guess = (flattened_data[peaks[i]], x_0, y_0, 10, 10, 0, 0)
            # find the optimal Gaussian parameters
            popt, pcov = opt.curve_fit(self.twoD_Gaussian, (x, y), flattened_data, p0=initial_guess)
            coords.append([popt[1], popt[2]])
            popt_array.append(popt)

        data_fitted1 = self.twoD_Gaussian((x, y), *popt_array[0])
        data_fitted2 = self.twoD_Gaussian((x, y), *popt_array[1])
        data_fitted3 = self.twoD_Gaussian((x, y), *popt_array[2])
        '''
        fig, ax = plt.subplots(1, 1)
        # ax.hold(True) For older versions. This has now been deprecated and later removed
        ax.imshow(flattened_data.reshape(current_image.shape), origin='lower', extent=(x.min(), x.max(), y.min(), y.max()))
        ax.contour(x, y, data_fitted1.reshape(current_image.shape), 8, colors='w')
        ax.contour(x, y, data_fitted2.reshape(current_image.shape), 8, colors='w')
        ax.contour(x, y, data_fitted3.reshape(current_image.shape), 8, colors='w')
        plt.show()
        '''
        np.savetxt("temp/data_fitted1.csv", data_fitted1.reshape(current_image.shape), delimiter=",")
        np.savetxt("temp/data_fitted2.csv", data_fitted2.reshape(current_image.shape), delimiter=",")
        np.savetxt("temp/data_fitted3.csv", data_fitted3.reshape(current_image.shape), delimiter=",")

        return np.array([coords[2], coords[0], coords[1]]).astype(np.float32)

    def calibrate_camera(self, dmd):
        if self.vocal:
            print('\n\nstart calibration')

        cal_pattern, dmd_coords = patterns.calibration_pattern(dmd.height, dmd.width, 400)
        test_img10 = abs((cal_pattern-1)*255)

        dmd_thread = threading.Thread(target=dmd.start_sequence, args=(test_img10,), kwargs={'duration': 5})
        cam_thread = threading.Thread(target=self.capture_image)

        dmd_thread.start()
        cam_thread.start()

        dmd_thread.join()
        cam_thread.join()

        camera_coords = self.get_cal_coords(self.current_image)

        if self.vocal:
            print('Executing affine transformation')
        trans_matrix = cv2.getAffineTransform(camera_coords, np.flip(dmd_coords, axis=None))

        fig, ([ax1, ax2, ax3]) = plt.subplots(1, 3, figsize=(10, 5))
        ax1.imshow(cal_pattern)
        ax1.set_xlabel('pixels')
        ax1.set_ylabel('pixels')
        ax2.imshow(self.current_image)
        ax2.set_xlabel('pixels')
        ax2.set_ylabel('pixels')
        trans_image = cv.warpAffine(self.current_image, trans_matrix, (dmd.width, dmd.height))
        ax3.imshow(trans_image)
        ax3.set_xlabel('pixels')
        ax3.set_ylabel('pixels')
        plt.show()
        plt.savefig('calibration.png')

        np.savetxt("temp/cal_pattern.csv", cal_pattern, delimiter=",")
        np.savetxt("temp/ccd_image.csv", self.current_image, delimiter=",")
        np.savetxt("temp/trans_image.csv", trans_image, delimiter=",")

        return trans_matrix

