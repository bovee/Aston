"""
Functions which mathematically manipulate TimeSeries.
"""
import struct
import zlib
import numpy as np
import scipy.ndimage
from aston.trace import Chromatogram, Trace


def series_from_str(val, times, name=''):
    # TODO: generate this without needing the times? just the time length
    # we can store time-series data as a list of timepoints
    # in certain info fields and query it here
    def is_num(x):
        # stupid function to determine if something is a number
        try:
            float(x)
            return True
        except ValueError:
            return False

    if ',' in val:
        # turn the time list into a dictionary
        tpts = dict([tpt.split(':') for tpt in val.split(',')])
        # get the valid times out
        valid_x = [v for v in tpts if is_num(v)]
        # generate arrays from them
        x = np.array([float(v) for v in valid_x])
        y = np.array([float(tpts[v]) for v in valid_x])
        srt_ind = np.argsort(x)
        if 'S' in tpts:
            # there's a "S"tart value defined
            d = np.interp(times, x[srt_ind], y[srt_ind], float(tpts['S']))
        else:
            d = np.interp(times, x[srt_ind], y[srt_ind])
    elif is_num(val):
        d = np.ones(times.shape) * float(val)
    else:
        d = np.ones(times.shape) * np.nan
    return Trace(d, times, name=name)


def fft(ts):
    """
    Perform a fast-fourier transform on a Trace
    """
    t_step = ts.index[1] - ts.index[0]
    oc = np.abs(np.fft.fftshift(np.fft.fft(ts.values))) / len(ts.values)
    t = np.fft.fftshift(np.fft.fftfreq(len(oc), d=t_step))
    return Trace(oc, t)


def ifft(ic, t):
    raise NotImplementedError
#    ic = np.fft.ifft(np.fft.fftshift(ic * len(ic)))# / len(ic)


def noisefilter(arr, bandwidth=0.2):
    # adapted from http://glowingpython.blogspot.com/
    # 2011/08/fourier-transforms-and-image-filtering.html
    i = np.fft.fftshift(np.fft.fft(arr))  # entering to frequency domain
    # fftshift moves zero-frequency component to the center of the array
    p = np.zeros(len(i), dtype=complex)
    c1 = len(i) / 2  # spectrum center
    r = float(bandwidth)  # percent of signal to save
    r = int((r * len(i)) / 2)  # convert to coverage of the array
    for i in range(c1 - r, c1 + r):
        p[i] = i[i]  # frequency cutting
    return np.real(np.fft.ifft(np.fft.ifftshift(p)))


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
    b = [[k ** i for i in order_range]
         for k in range(-half_wind, half_wind + 1)]
    m = np.linalg.pinv(b)[int(deriv)]
    return scipy.ndimage.convolve1d(arr, m, axis=0, mode='reflect')


def loads(ast_str):
    """
    Create a Trace from a suitably compressed string.
    """
    data = zlib.decompress(ast_str)
    li = struct.unpack('<L', data[0:4])[0]
    lt = struct.unpack('<L', data[4:8])[0]
    n = data[8:8 + li].decode('utf-8')
    t = np.fromstring(data[8 + li:8 + li + lt])
    d = np.fromstring(data[8 + li + lt:])

    return Trace(d, t, name=n)


def dumps(asts):
    """
    Create a compressed string from an Trace.
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
        # TODO: should vectorize to apply over all columns?
        return Chromatogram(f(df.values, *args), df.index, df.columns)
    return wrap_func
