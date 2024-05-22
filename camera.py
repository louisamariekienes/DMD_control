import sys
import os
from os.path import exists
import copy

from ids_peak import ids_peak
from ids_peak_ipl import ids_peak_ipl
from ids_peak import ids_peak_ipl_extension

TARGET_PIXEL_FORMAT = ids_peak_ipl.PixelFormatName_BGRa8


class Camera:

    def __init__(self):
        ids_peak.Library.Initialize()
        self.device_manager = ids_peak.DeviceManager.Instance()

        self.ipl_image = None
        self.current_image = None
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
            print('Acquisition stopped')
        except Exception as e:
            print(str(e))

    def software_trigger(self):
        print("Executing software trigger...")
        self.node_map.FindNode("TriggerSoftware").Execute()
        self.node_map.FindNode("TriggerSoftware").WaitUntilDone()
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
        cwd = os.getcwd()

        buffer = self._datastream.WaitForFinishedBuffer(1000)
        print("Buffered image!")

        # Get image from buffer (shallow copy)
        self.ipl_image = ids_peak_ipl_extension.BufferToImage(buffer)


        # This creates a deep copy of the image, so the buffer is free to be used again
        # NOTE: Use `ImageConverter`, since the `ConvertTo` function re-allocates
        #       the converison buffers on every call
        converted_ipl_image = self._image_converter.Convert(
            self.ipl_image, TARGET_PIXEL_FORMAT)

        # Get raw image data from converted image and construct a QImage from it
        self.current_image = copy.copy(converted_ipl_image.get_numpy_2D_16())
        print(self.current_image.shape)
        print(self.current_image[1500])
        #plt.imshow(self.current_image)
        #plt.show()

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
