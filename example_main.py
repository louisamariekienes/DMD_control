# author: Louisa Marie Kienesberger

# Press Umschalt+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

from dmd.x64.ALP4 import *
import time
import patterns

import matplotlib.pyplot as plt


def main():
    # Use a breakpoint in the code line below to debug your script.
    print('Hi Louisa')  # Press Strg+F8 to toggle the breakpoint.

    # Load the Vialux.dll
    DMD = ALP4(version='4.3', libDir='C:\\Users\\laborbenutzer\\Desktop\\Louisa\\DMD_control\\dmd')
    #DMD = ALP4(version='4.3', libDir='C:\Program Files\ALP-4.3/ALP-4.3 API')

    # Initialize the device
    DMD.Initialize()

    # Binary amplitude image (0 or 1)
    bitDepth = 1
    height, width = DMD.nSizeY, DMD.nSizeX
    print("height= ", height, "\nwidth= ", width)

    imgBlack = np.zeros([DMD.nSizeY, DMD.nSizeX])
    imgWhite = np.ones([DMD.nSizeY, DMD.nSizeX]) * (2 ** 8 - 1)

    test_img2 = abs(patterns.rect_pattern(height, width, 400)-1)*255
    #test_img5, var = patterns.calibration_pattern(height, width, 400)
    #test_img10 = abs(test_img5-(2**8-1))

    plt.imshow(test_img2)
    plt.show()

    img_list = []
    for i in range(10):
        img = abs(patterns.rect_pattern(height, width, i*20)-(2**8-1))
        img_list.append(img)

    imgSeq = np.concatenate(img_list)

    # Allocate the onboard memory for the image sequence
    DMD.SeqAlloc(nbImg=1, bitDepth=bitDepth)
    # Send the image sequence as a 1D list/array/numpy array
    # DMD.SeqPut(imgData=imgSeq)
    DMD.SeqPut(imgData=test_img2)
    # Set image rate to 50/1 Hz
    #DMD.SetTiming(pictureTime=20000)        # 20000 for 50 Hz, 1 for 1Hz

    # Run the sequence in an infinite loop
    DMD.Run()

    time.sleep(300)

    # Stop the sequence display
    DMD.Halt()
    # Free the sequence from the onboard memory
    DMD.FreeSeq()
    # De-allocate the device
    DMD.Free()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()
