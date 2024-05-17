# author: Louisa Marie Kienesberger

from dmd.ALP4 import *
import time
import patterns


class DigitalMicroMirrorDevice:
    def __init__(self, dummy):
        if dummy:
            self._dummy = True
            self._dim = (self._height, self._width) = (1920, 1080)
            print("Dummy DMD activated.")
        else:
            # Load the Vialux.dll
            self._DMD = ALP4(version='4.3', libDir='C:/Users/laborbenutzer/Desktop/Louisa/DMD_control/dmd')
            # Initialize the device
            self._DMD.Initialize()

            # Binary amplitude image (0 or 1)
            bitDepth = 1
            self._dim = (self._height, self._width) = (self._DMD.nSizeY, self._DMD.nSizeX)

    def start_sequence(self, sequence, bitDepth):
        nbImg, imgData = sequence
        # Allocate the onboard memory for the image sequence
        if self._dummy:
            width, height = 1920, 1080
            img = patterns.rect_pattern(height, width, 100)
        else:
            self._DMD.SeqAlloc(nbImg=nbImg, bitDepth=bitDepth)

            # Send the image sequence as a 1D list/array/numpy array
            # DMD.SeqPut(imgData=imgSeq)
            self._DMD.SeqPut(imgData=sequence)

            # EIGENE FUNKTION
            # Set image rate to 50/1 Hz
            self._DMD.SetTiming(pictureTime=20000)        # 20000 for 50 Hz, 1 for 1Hz

            # Run the sequence in an infinite loop
            self._DMD.Run()

            time.sleep(300)

            # Stop the sequence display
            self._DMD.Halt()
            # Free the sequence from the onboard memory
            self._DMD.FreeSeq()
            # De-allocate the device
            self._DMD.Free()
            pass

    def set_sequence(self, pattern, size):
        img = patterns.rect_pattern(self._height, self._width, 200)
        nbImg = 1
        return nbImg, img

    @property
    def height(self):
        return self._height

    @property
    def width(self):
        return self._width
