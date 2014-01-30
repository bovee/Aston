
"""
Functions which mathematically manipulate TimeSeries.
"""
import struct
import zlib
import numpy as np
import scipy.ndimage
from aston.trace.Trace import AstonSeries, AstonFrame


def fft(ts):
    """
    Perform a fast-fourier transform on a AstonSeries
    """
    t_step = ts.index[1] - ts.index[0]
    oc = np.abs(np.fft.fftshift(np.fft.fft(ts.values))) / len(ts.values)
    t = np.fft.fftshift(np.fft.fftfreq(len(oc), d=t_step))
    return AstonSeries(oc, t)


def ifft(ic, t):
#    ic = np.fft.ifft(np.fft.fftshift(ic * len(ic)))# / len(ic)
    raise NotImplementedError


def noisefilter_(arr, bandwidth=0.2):
    #adapted from http://glowingpython.blogspot.com/
    #2011/08/fourier-transforms-and-image-filtering.html
    I = np.fft.fftshift(np.fft.fft(arr))  # entering to frequency domain
    # fftshift moves zero-frequency component to the center of the array
    P = np.zeros(len(I), dtype=complex)
    c1 = len(I) / 2  # spectrum center
    r = float(bandwidth)  # percent of signal to save
    r = int((r * len(I)) / 2)  # convert to coverage of the array
    for i in range(c1 - r, c1 + r):
        P[i] = I[i]  # frequency cutting
    return np.real(np.fft.ifft(np.fft.ifftshift(P)))


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


def loads(ast_str):
    """
    Create a AstonSeries from a suitably compressed string.
    """
    data = zlib.decompress(ast_str)
    li = struct.unpack('<L', data[0:4])[0]
    lt = struct.unpack('<L', data[4:8])[0]
    n = data[8:8 + li].decode('utf-8')
    t = np.fromstring(data[8 + li:8 + li + lt])
    d = np.fromstring(data[8 + li + lt:])

    return AstonSeries(d, t, name=n)


def dumps(asts):
    """
    Create a compressed string from an AstonSeries.
    """
    d = asts.values.tostring()
    t = asts.index.values.astype(float).tostring()
    lt = struct.pack('<L', len(t))
    i = asts.name.encode('utf-8')
    li = struct.pack('<L', len(i))
    try:  # python 2
        return buffer(zlib.compress(li + lt + i + t + d))
    except NameError:  # python 3
        return zlib.compress(li + lt + i + t + d)


def ts_func(f):
    """
    This wraps a function that would normally only accept an array
    and allows it to operate on a DataFrame. Useful for applying
    numpy functions to DataFrames.
    """
    def wrap_func(df, *args):
        #TODO: should vectorize to apply over all columns?
        return AstonFrame(f(df.values, *args), df.index, df.columns)
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
