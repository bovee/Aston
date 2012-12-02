import numpy as np
import base64
from aston.TimeSeries import TimeSeries
from aston.TimeSeries import decompress_to_ts

def test_and():
    t = np.array([1, 2, 3, 4, 5])
    a = TimeSeries(np.array([10, 20, 30, 40, 50]), t, ['X'])
    b = TimeSeries(np.array([11, 21, 31, 41, 51]), t, ['Y'])
    assert np.all(np.equal((a & b).data[0], np.array([10, 11])))


def test_add():
    t = np.array([1, 2, 3, 4, 5])
    a = TimeSeries(np.array([10, 20, 30, 40, 50]), t, ['X'])
    b = TimeSeries(np.array([11, 21, 31, 41, 51]), t, ['X'])
    c = a + b
    assert np.all(np.equal(c.data.T[0], np.array([21, 41, 61, 81, 101])))
    assert np.all(np.equal(c.times, np.array([1, 2, 3, 4, 5])))


def test_compress():
    #TODO: this fails for mysterious reasons
    t = np.array([1, 2, 3, 4, 5])
    a = TimeSeries(np.array([10, 20, 30, 40, 50]), t, ['X'])
    zdata = 'eJxjZWBg0ADiaKUIpVgGMPhgD6EZHCAUB5QWgNIiU' + \
      'FoFSptAaTso7QKlPR0AOdIGQA=='
    print(base64.b64encode(a.compress()).decode('ascii'))
    print(zdata)
    assert base64.b64encode(a.compress()).decode('ascii') == zdata


def test_decompress():
    zdata = 'eJxjZWBg0ADiaKUIpVgGMPhgD6EZHCAUB5QWgNIiU' + \
      'FoFSptAaTso7QKlPR0AOdIGQA=='
    ts = decompress_to_ts(base64.b64decode(zdata))
    assert ts.ions == ['X']
