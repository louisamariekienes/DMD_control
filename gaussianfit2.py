import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import scipy.optimize as opt

def twoD_Gaussian(amp0, x0, y0, amp1=13721, x1=356, y1=247, amp2=14753, x2=291,  y2=339, sigma=40):

    x0 = float(x0)
    y0 = float(y0)
    x1 = float(x1)
    y1 = float(y1)
    x2 = float(x2)
    y2 = float(y2)

    return lambda x, y:  (amp0*np.exp(-(((x0-x)/sigma)**2+((y0-y)/sigma)**2)/2))+(
                             amp1*np.exp(-(((x1-x)/sigma)**2+((y1-y)/sigma)**2)/2))+(
                             amp2*np.exp(-(((x2-x)/sigma)**2+((y2-y)/sigma)**2)/2))

def twoD_GaussianCF(xy, amp0, x0, y0, amp1=230, amp2=200, x1=1220, y1=378, x2=1200,  y2=1400, sigma_x=12, sigma_y=12):

    x0 = float(x0)
    y0 = float(y0)
    x1 = float(x1)
    y1 = float(y1)
    x2 = float(x2)
    y2 = float(y2)

    g = (amp0*np.exp(-(((x0-x)/sigma_x)**2+((y0-y)/sigma_y)**2)/2))+(
        amp1*np.exp(-(((x1-x)/sigma_x)**2+((y1-y)/sigma_y)**2)/2))+(
        amp2*np.exp(-(((x2-x)/sigma_x)**2+((y2-y)/sigma_y)**2)/2))

    return g.ravel()


# Load the image (replace 'my_image.png' with your actual image path)
png_filepath = 'figures/image_3.png'
png_pil_img = Image.open(png_filepath).convert('L')
image_array = np.asarray(png_pil_img).astype('float')

print(np.max(image_array), np.min(image_array))
plt.imshow(image_array)
plt.show()


w, h = np.shape(image_array)
x, y = np.mgrid[0:h, 0:w]
xy = (x, y)

N_points = 3
display_width = 80

#initial_guess_sum = (Amp[0], px[0], py[0], Amp[1], px[1], py[1], Amp[2], px[2], py[2])

popt, pcov = opt.curve_fit(twoD_GaussianCF, xy, np.ravel(image_array)) #, p0=initial_guess_sum)

data_fitted = twoD_Gaussian(*popt)(x, y)

peaks = [(popt[1], popt[2]), (popt[5], popt[6]), (popt[7], popt[8])]

'''
fig = plt.figure(figsize=(10, 10))
ax = fig.add_subplot(111, aspect="equal")
cb = ax.imshow(p, cmap=plt.cm.jet, origin='bottom',
    extent=(x.min(), x.max(), y.min(), y.max()))
ax.contour(x, y, data_fitted.reshape(x.shape[0], y.shape[1]), 20, colors='w')

ax.set_xlim(np.int(RC[0])-135, np.int(RC[0])+135)
ax.set_ylim(np.int(RC[1])+135, np.int(RC[1])-135)

for k in range(0,N_points):
    plt.plot(peaks[k][0],peaks[k][1],'bo',markersize=7)
plt.show()
'''