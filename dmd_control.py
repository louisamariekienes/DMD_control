# author: Louisa Marie Kienesberger

from dmd.x64.ALP4 import *
import time
import patterns


class DigitalMicroMirrorDevice:
    def __init__(self):
        self.verbose = False
        # Load the Vialux.dll
        # needs to be changed, for now absolute path to the x64 folder
        self._DMD = ALP4(version='4.3', libDir='C:\\Users\\laborbenutzer\\Desktop\\Louisa\\DMD_control\\dmd')
        # Initialize the device
        self._DMD.Initialize()

        self._dim = (self._height, self._width) = (self._DMD.nSizeY, self._DMD.nSizeX)
        self.pattern = None
        self.nbImg = 1     # number of images, not 1 for dynamic patterns

    def start_sequence(self, sequence, nbImg=1, bitDepth=1, pictureTime=2000, duration=60):
        if self.verbose:
            print('DMD - start sequence')

        # Allocate the onboard memory for the image sequence
        self._DMD.SeqAlloc(nbImg=nbImg, bitDepth=bitDepth)

        # Send the image sequence as a 1D list/array/numpy array
        # DMD.SeqPut(imgData=imgSeq)
        self._DMD.SeqPut(imgData=sequence)

        # EIGENE FUNKTION
        # Set image rate to 50/1 Hz
        self._DMD.SetTiming(pictureTime=pictureTime)        # 20000 for 50 Hz, 1 for 1Hz

        # Run the sequence in an infinite loop
        self._DMD.Run()

        time.sleep(duration)

        # Stop the sequence display
        self._DMD.Halt()
        # Free the sequence from the onboard memory
        self._DMD.FreeSeq()

    def set_pattern(self, pattern, nbImg):
        self.pattern = pattern
        self.nbImg = nbImg

    @property
    def height(self):
        return self._height

    @property
    def width(self):
        return self._width

    def close(self):
        # De-allocate the device
        self._DMD.Free()
