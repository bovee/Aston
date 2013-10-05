
"""
Functions which mathematically manipulate TimeSeries.
"""

import numpy as np
import scipy.ndimage
from pandas import Series, DataFrame


def fft(ts):
    """
    Perform a fast-fourier transform on a TimeSeries
    """
    t_step = ts.index[1] - ts.index[0]
    oc = np.abs(np.fft.fftshift(np.fft.fft(ts.values))) / len(ts.values)
    t = np.fft.fftshift(np.fft.fftfreq(len(oc), d=t_step))
    return Series(oc, t)
#elif fxn == 'ifft':
#    ic = np.fft.ifft(np.fft.fftshift(ic * len(ic)))# / len(ic)


def ifft(ic, t):
    raise NotImplementedError


def noisefilter_(y, bandwidth=0.2):
    #adapted from http://glowingpython.blogspot.com/
    #2011/08/fourier-transforms-and-image-filtering.html
    I = np.fft.fftshift(np.fft.fft(y))  # entering to frequency domain
    # fftshift moves zero-frequency component to the center of the array
    P = np.zeros(len(I), dtype=complex)
    c1 = len(I) / 2  # spectrum center
    r = float(bandwidth)  # percent of signal to save
    r = int((r * len(I)) / 2)  # convert to coverage of the array
    for i in range(c1 - r, c1 + r):
        P[i] = I[i]  # frequency cutting
    return np.real(np.fft.ifft(np.fft.ifftshift(P)))


def CODA(df, window, level):
    """
    CODA processing from Windig, Phalp, & Payne 1996 Anal Chem
    """
    # pull out the data
    d = df.values

    # smooth the data and standardize it
    smooth_data = movingaverage(d, df.index, window)[0]
    stand_data = (smooth_data - smooth_data.mean()) / smooth_data.std()

    #scale the data to have unit length
    scale_data = d / np.sqrt(np.sum(d ** 2, axis=0))

    # calculate the "mass chromatographic quality" (MCQ) index
    mcq = np.sum(stand_data * scale_data, axis=0) / np.sqrt(d.shape[0] - 1)

    # filter out ions with an mcq below level
    good_ions = [i for i, q in zip(df.columns, mcq) if q >= level]
    return good_ions


def movingaverage(arr, window):
    """
    Calculates the moving average ("rolling mean") of an array
    of a certain window size.
    """
    m = np.ones(int(window)) / int(window)
    return scipy.ndimage.convolve1d(arr, m, axis=0, mode='reflect')


def savitzkygolay(arr, window, order, deriv=0):
    # adapted from http://www.scipy.org/Cookbook/SavitzkyGolay
    # but uses ndimage.convolve now, so we don't have to
    # do the padding ourselves
    half_wind = (int(window) - 1) // 2
    order_range = range(int(order) + 1)
    # precompute coefficients
    b = [[k ** i for i in order_range] \
          for k in range(-half_wind, half_wind + 1)]
    m = np.linalg.pinv(b)[int(deriv)]
    return scipy.ndimage.convolve1d(arr, m, axis=0, mode='reflect')


def ts_func(f):
    """
    This wraps a function that would normally only accept an array
    and allows it to operate on a DataFrame. Useful for applying
    numpy functions to DataFrames.
    """
    def wrap_func(df, *args):
        #TODO: should vectorize to apply over all columns?
        return DataFrame(f(df.values, *args), df.index, df.columns)
    return wrap_func


noisefilter = ts_func(noisefilter_)
abs = ts_func(np.abs)
sin = ts_func(np.sin)
cos = ts_func(np.cos)
tan = ts_func(np.tan)
derivative = ts_func(np.gradient)
fxns = {'fft': fft,
        'noise': ts_func(noisefilter_),
        'abs': ts_func(np.abs),
        'sin': ts_func(np.sin),
        'cos': ts_func(np.cos),
        'tan': ts_func(np.tan),
        'derivative': ts_func(np.gradient),
        'd': ts_func(np.gradient),
        'movingaverage': movingaverage,
        'savitzkygolay': savitzkygolay,
        }
