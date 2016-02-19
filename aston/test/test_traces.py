import numpy as np
import base64
from aston.trace.trace import Trace, decompress


#TODO: reenable Trace merging someday, but with more intelligence?
#def test_and():
#    t = np.array([1, 2, 3, 4, 5])
#    a = Trace(np.array([10, 20, 30, 40, 50]), t, name='X')
#    b = Trace(np.array([11, 21, 31, 41, 51]), t, name='Y')
#    assert np.all(np.equal((a & b).values, np.array([10, 11])))


def test_add():
    t = np.array([1, 2, 3, 4, 5])
    a = Trace(np.array([10, 20, 30, 40, 50]), t, name='X')
    b = Trace(np.array([11, 21, 31, 41, 51]), t, name='X')
    c = a + b
    assert np.all(np.equal(c.values, np.array([21, 41, 61, 81, 101])))
    assert np.all(np.equal(c.index, np.array([1, 2, 3, 4, 5])))


def test_compress():
    a = Trace(np.array([10, 20, 30, 40, 50]), \
                    np.array([1, 2, 3, 4, 5]), name='X')
    zdata = 'eJxjZWBgEAHiaKUIpVgGhgZ7INsBiIC4' + \
            'AYgXADEIqEBpEyhtB6VdoLSnAwAZfgbw'
    assert base64.b64encode(a.compress()).decode('ascii') == zdata


def test_decompress():
    zdata = 'eJxjZWBgEAHiaKUIpVgGhgZ7INsBiIC4' + \
            'AYgXADEIqEBpEyhtB6VdoLSnAwAZfgbw'
    ts = decompress(base64.b64decode(zdata))
    assert ts.name == 'X'


#def test_tsfunc():
#    a = Trace(np.array([[0, 1, 2, 1, 0], [0, 0, 2, 0, 0]]).T, \
#                   np.array([1, 2, 3, 4, 5]), [1, 2])
#    grad = ts_func(np.gradient)
#    c = grad(a.trace(1)) / grad(Trace(a.times, a.times))
#    assert np.all(c.y == np.array([1., 1., 0., -1., -1.]))
