import numpy as np

import scipy.ndimage
from scipy.stats import gaussian_kde
from scipy.optimize import fmin, brentq


def fft(ic, t):
    oc = np.abs(np.fft.fftshift(np.fft.fft(ic))) / len(ic)
    t = np.fft.fftshift(np.fft.fftfreq(len(oc), d=t[1] - t[0]))
#elif fxn == 'ifft':
#    ic = np.fft.ifft(np.fft.fftshift(ic * len(ic)))# / len(ic)
    return oc, t


def noisefilter(ic, t, bandwidth):
    #adapted from http://glowingpython.blogspot.com/
    #2011/08/fourier-transforms-and-image-filtering.html
    I = np.fft.fftshift(np.fft.fft(ic))  # entering to frequency domain
    # fftshift moves zero-frequency component to the center of the array
    P = np.zeros(len(I), dtype=complex)
    c1 = len(I) / 2  # spectrum center
    r = float(bandwidth)  # percent of signal to save
    r = int((r * len(I)) / 2)  # convert to coverage of the array
    for i in range(c1 - r, c1 + r):
        P[i] = I[i]  # frequency cutting
    oc = np.real(np.fft.ifft(np.fft.ifftshift(P)))


def base(ic, t, slope_tol='5.0', off_tol='5.0'):
    ic = savitzkygolay(ic, t, 5, 3)[0]
    slopes = np.diff(ic) / np.diff(t)
    wind = np.array([0.5, 0.5])
    offsets = np.convolve(ic, wind, mode='valid') - \
      slopes * np.convolve(t, wind, mode='valid')

    sl_kern = gaussian_kde(slopes)
    base_slope = fmin(lambda x: -sl_kern(x), 0, disp=False)
    k_h = sl_kern(base_slope) * (1.0 - 10 ** -float(slope_tol))
    s1 = brentq(lambda x: sl_kern(x) - k_h, \
      min(slopes), base_slope)
    s2 = brentq(lambda x: sl_kern(x) - k_h, \
      base_slope, max(slopes))

    valid = np.logical_and(slopes > s1, slopes < s2)
    off_kern = gaussian_kde(offsets[valid])
    base_off = fmin(lambda x: -off_kern(x), 0, disp=False)
    k_h = off_kern(base_off) * (1.0 - 10 ** -float(off_tol))
    o1 = brentq(lambda x: off_kern(x) - k_h, \
      min(offsets), base_off)
    o2 = brentq(lambda x: off_kern(x) - k_h, \
      base_off, max(offsets))

    msk = np.logical_and(valid, offsets > o1)
    msk = np.logical_and(valid, offsets < o2)
    new_ic = np.interp(t, t[msk], ic[msk])
    return new_ic, t


def base2(ic, t):
    #INSPIRED by Algorithm A12 from Zupan
    #5 point pre-smoothing
    sc = np.convolve(np.ones(5) / 5.0, ic, mode='same')
    #get local minima
    mn = np.arange(len(ic))[np.r_[True, ((sc < np.roll(sc, 1)) &
      (sc < np.roll(sc, -1)))[1:-1], True]]
    #don't allow baseline to have a slope greater than
    #10x less than the steepest peak
    max_slope = np.max(np.gradient(ic)) / 10.0
    slope = max_slope
    pi = 0  # previous index
    oc = np.zeros(len(ic))
    for i in range(1, len(mn)):
        if slope < (ic[mn[i]] - ic[mn[pi]]) / (mn[i] - mn[pi]) and \
          slope < max_slope:
            #add trend
            oc[mn[pi]:mn[i - 1]] = \
              np.linspace(ic[mn[pi]], ic[mn[i - 1]], mn[i - 1] - mn[pi])
            pi = i - 1
        slope = (ic[mn[i]] - ic[mn[pi]]) / (mn[i] - mn[pi])
    print(mn[pi], mn[-1])
    oc[mn[pi]:mn[-1]] = \
      np.linspace(ic[mn[pi]], ic[mn[-1]], mn[-1] - mn[pi])
    oc[-1] = oc[-2]  # FIXME: there's definitely a bug in here somewhere


def CODA(ts, window, level):
    """
    CODA processing from Windig, Phalp, & Payne 1996 Anal Chem
    """
    # pull out the data
    try:
        d = ts.data.toarray()
    else:
        d = ts.data

    # smooth the data and standardize it
    smooth_data = movingaverage(d, ts.times, window)[0]
    stand_data = (smooth_data - smooth_data.mean()) / smooth_data.std()

    #scale the data to have unit length
    scale_data = d / np.sqrt(np.sum(d ** 2, axis=0))

    # calculate the "mass chromatographic quality" (MCQ) index
    mcq = np.sum(stand_data * scale_data, axis=0) / np.sqrt(d.shape[0] - 1)

    # filter out ions with an mcq below level
    good_ions = [i for i, q in zip(ts.ions, mcq) if q >= level]
    return good_ions


def movingaverage(ic, t, window):
    m = np.ones(int(window)) / int(window)
    return _smooth(ic, m), t


def savitzkygolay(ic, t, window, order):
    # adapted from http://www.scipy.org/Cookbook/SavitzkyGolay
    # but uses ndimage.convolve now, so we don't have to
    # do the padding ourselves
    half_wind = (int(window) - 1) // 2
    order_range = range(int(order) + 1)
    # precompute coefficients
    b = [[k ** i for i in order_range] \
          for k in range(-half_wind, half_wind + 1)]
    m = np.linalg.pinv(b)[0]
    return _smooth(ic, m), t


def _smooth(ic, m):
    return scipy.ndimage.convolve1d(ic, m, axis=0, mode='reflect')


# we don't need to reinvent the wheel, so we can straight up use some
# of numpy's default functions and pass our array directly in
# this function wraps
def ts_func(f):
    def wrap_func(ic, t):
        return f(ic), t
    return wrap_func
#def ts_func(f):
#    def wrap_func(ts):
#        return TimeSeries(f(ts.y), ts.times)
#    return wrap_func

fxns = {'fft': fft,
        'noise': noisefilter,
        'abs': ts_func(np.abs),
        'sin': ts_func(np.sin),
        'cos': ts_func(np.cos),
        'tan': ts_func(np.tan),
        'derivative': ts_func(np.gradient),
        'd': ts_func(np.gradient),
        'base': base,
        'movingaverage': movingaverage,
        'savitskygolay': savitzkygolay,
        }
