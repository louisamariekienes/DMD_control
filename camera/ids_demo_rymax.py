from ids_peak import ids_peak
from ids_peak import ids_peak_ipl_extension
from ids_peak_ipl import ids_peak_ipl

import numpy as np
from six import iteritems
from cia.helper import log
from cia.cameras.template import CameraTemplate
from cia.cameras.template import MetadataHandling
import copy

# default to 2x2 binning and a rather short exposure time
example_config = {
    "AcquisitionFrameRate": 20,
    "ExposureTime": 100,
    "AcquisitionFrameCount": 1,
    "AcquisitionMode": "MultiFrame",
    "TriggerMode": "On",
    "TriggerSource": "Software",
    "TriggerSelector": "ExposureStart",
    "TriggerActivation": "RisingEdge",
    "Width": 1296,
    "Height": 972,
    "OffsetX": 0,
    "OffsetY": 0,
    "BinningSelector": "Sensor",
    "BinningHorizontal": 2,
    "BinningHorizontalMode": "Sum",
    "BinningVertical": 2,
    "BinningVerticalMode": "Sum"
},


class IdsPeak(CameraTemplate, MetadataHandling):
    """
    """

    # image buffer and metadata

    def __init__(self, name, cam_id=None, width=2592, height=1944, default_configuration=None, remote=None, **kwargs):
        log.info("open IDs camera")

        # initialize library
        ids_peak.Library.Initialize()

        # create a device manager object
        device_manager = ids_peak.DeviceManager.Instance()

        # try:
        # update the device manager
        device_manager.Update()

        cam_index = -1
        if cam_id is None:
            cam_index = 0
        else:
            for i, device_descriptor in enumerate(device_manager.Devices()):
                log.debug(f"checking {device_descriptor.DisplayName()}")
                if device_descriptor.SerialNumber() == cam_id:
                    cam_index = i
                    break

        # exit program if no device was found
        if device_manager.Devices().empty() or cam_index < 0:
            log.error("Device not found. Exiting Program.")
            raise FileNotFoundError

        # list all available devices
        device = device_manager.Devices()[cam_index]
        log.info(f"Using device {device.ModelName()} ({device.ParentInterface().DisplayName()}; {device.SerialNumber()}"
                 f" v.{device.ParentInterface().ParentSystem().Version()})")

        # open selected device
        self._camera = device.OpenDevice(ids_peak.DeviceAccessType_Control)
        log.info("camera opened")

        # get the remote device node map
        self.nodemap_remote_device = self._camera.RemoteDevice().NodeMaps()[0]

        # print camera information
        log.info(f"Model Name: { self._get_property('DeviceModelName')}")
        log.info(f"User ID: {self._get_property('DeviceUserID')}")
        log.info(f"Sensor Name: {self._get_property('SensorName')}")
        log.info(f"Max. resolution (w x h): {self._get_property('WidthMax')} x {self._get_property('HeightMax')}")

        self._init_datastreams()

        # To prepare for untriggered continuous image acquisition, load the default user set if available and
        # wait until execution is finished
        try:
            self.nodemap_remote_device.FindNode("UserSetSelector").SetCurrentEntry("Default")
            self.nodemap_remote_device.FindNode("UserSetLoad").Execute()
            self.nodemap_remote_device.FindNode("UserSetLoad").WaitUntilDone()
        except ids_peak.Exception:
            # Userset is not available
            pass

        CameraTemplate.__init__(self, name=name, width=width, height=height, **kwargs)

        default_configuration = {} if default_configuration is None else default_configuration
        self.frame_count = 1
        self.configuration = default_configuration

        # set default value for the timeout
        if 'timeout' not in self.configuration:
            self.configuration['timeout'] = 5000

        self.name = name

    def _get_property(self, name):
        if self.nodemap_remote_device is not None:
            try:
                if "CurrentEntry" in dir(self.nodemap_remote_device.FindNode(name)):
                    return self.nodemap_remote_device.FindNode(name).CurrentEntry().SymbolicValue()
                else:
                    return self.nodemap_remote_device.FindNode(name).Value()
            except Exception as e:
                log.debug(f"Error retrieving {name}: {e}")
                return "unknown"

    def _set_property(self, name, value):
        if self.nodemap_remote_device is not None:
            try:
                if "SetCurrentEntry" in dir(self.nodemap_remote_device.FindNode(name)):
                    self.nodemap_remote_device.FindNode(name).SetCurrentEntry(value)
                else:
                    self.nodemap_remote_device.FindNode(name).SetValue(value)
                return True
            except Exception as e:
                log.debug(f"Error setting {name}: {e}")
                return False

    def _run_function(self, name, blocking=False):
        try:
            self.nodemap_remote_device.FindNode(name).Execute()
            if blocking:
                self.nodemap_remote_device.FindNode(name).WaitUntilDone()
            return True
        except Exception as e:
            log.debug(f"Error running {name}: {e}")
            return False

    def _init_datastreams(self):

        # Open standard data stream
        datastreams = self._camera.DataStreams()
        if datastreams.empty():
            self._camera = None
            return False

        self._datastream = datastreams[0].OpenDataStream()

        # Get the payload size for correct buffer allocation
        payload_size = self._get_property("PayloadSize")

        # Get minimum number of buffers that must be announced
        buffer_count_max = self._datastream.NumBuffersAnnouncedMinRequired()

        # Allocate and announce image buffers and queue them
        for i in range(buffer_count_max):
            buffer = self._datastream.AllocAndAnnounceBuffer(payload_size)
            self._datastream.QueueBuffer(buffer)

        return True

    def _configure(self):
        """
        configures the camera before taking images,
        using self.configuration and self.identifier

         :returns: (bool) True if configuration is possible
        """

        log.spam("configure camera")

        config = self._configuration.copy()

        # Unlock Parameters
        self._set_property("TLParamsLocked", 0)

        for key, value in sorted(iteritems(config)):
            log.debug(f"Setting {key} to {value}-> {self._set_property(key, value)}")

        self.frame_count = int(self._get_property("AcquisitionFrameCount"))

        return True

    def _exposure(self):
        """
        perform the exposure and download the images,
        using self._configuration, self._identifier, self._metadata
        this method is executed in a _thread,
        exceptions may be used to trigger error signals
        """
        log.debug("Start exposure")
        identifier = self._identifier
        metadata = self._metadata.copy()
        identifier = identifier if identifier is not None else self.generate_identifier()

        log.debug(f'Acquisition started: {self.frame_count} pictures')

        pics = []

        # Lock Parameters
        self._set_property("TLParamsLocked", 1)

        # Start Acquisition
        self._datastream.StartAcquisition()
        self._run_function("AcquisitionStart", blocking=True)

        self.exposureTriggered.emit()

        for n in range(0, self.frame_count):
            log.spam('Start waiting')
            log.spam(self.configuration)

            # Get buffer from device's datastream
            try:
                if self._get_property("TriggerSource") == "Software":
                    self._run_function("TriggerSoftware", blocking=True)

                buffer = self._datastream.WaitForFinishedBuffer(self.configuration["timeout"])

                log.spam('Got data')

                ipl_image = ids_peak_ipl_extension.BufferToImage(buffer)
                converted_ipl_image = ipl_image.ConvertTo(ids_peak_ipl.PixelFormatName_Mono12)

                # Get raw image data from converted image and construct a QImage from it
                image = copy.copy(converted_ipl_image.get_numpy_2D_16())

                # Queue buffer so that it can be used again
                self._datastream.QueueBuffer(buffer)

                pics.append(image)

            except ids_peak.TimeoutException:
                log.warning("Image polling timeout")

        self._run_function("AcquisitionStop", blocking=True)
        self._datastream.StopAcquisition(ids_peak.AcquisitionStopMode_Default)

        if pics == []:
            log.warning("No image to publish")
        else:
            log.spam("Publish image")

            self.newImage.emit(np.int64(identifier), np.array(pics), metadata)

            self.exposureStopped.emit()
            log.spam('Exposure stopped')

    def _reset(self):
        """
        resets the camera to a known working state,
        possibly stopping an exposure
        """
        log.spam("reset camera")
        self._abort()

    def _close(self):
        """
        cleanup hardware and other resources when releasing the camera
        """
        log.spam("close camera")
        self._abort()
        if self._datastream.NumBuffersStarted() > 0:
            self._datastream.KillWait()
        self._datastream.Flush(ids_peak.DataStreamFlushMode_DiscardAll)
        self._camera = None
        ids_peak.Library.Close()

    def _abort(self):
        """
        stop an exposure without completing the imaging sequence
        """
        log.spam("abort")
        self._run_function("AcquisitionStop", blocking=False)

        # Stop and flush datastream

        if self._datastream.IsGrabbing():
            self._datastream.StopAcquisition(ids_peak.AcquisitionStopMode_Default)
