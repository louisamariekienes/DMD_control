# author: Louisa Marie Kienesberger

# Press Umschalt+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

import numpy as np
from ALP4 import *
import time


def main():
    # Use a breakpoint in the code line below to debug your script.
    print('Hi Louisa')  # Press Strg+F8 to toggle the breakpoint.

    # Load the Vialux .dll
    DMD = ALP4(version='4.3')
    # Initialize the device
    DMD.Initialize()

    # Binary amplitude image (0 or 1)
    bitDepth = 1
    imgBlack = np.zeros([DMD.nSizeY, DMD.nSizeX])
    imgWhite = np.ones([DMD.nSizeY, DMD.nSizeX]) * (2 ** 8 - 1)
    imgSeq = np.concatenate([imgBlack.ravel(), imgWhite.ravel()])

    # Allocate the onboard memory for the image sequence
    DMD.SeqAlloc(nbImg=2, bitDepth=bitDepth)
    # Send the image sequence as a 1D list/array/numpy array
    DMD.SeqPut(imgData=imgSeq)
    # Set image rate to 50/1 Hz
    DMD.SetTiming(pictureTime=2000)        # 20000 for 50 Hz, 1 for 1Hz

    # Run the sequence in an infinite loop
    DMD.Run()

    time.sleep(10)

    # Stop the sequence display
    DMD.Halt()
    # Free the sequence from the onboard memory
    DMD.FreeSeq()
    # De-allocate the device
    DMD.Free()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()
