import unittest
import numpy as np
from aston.trace import Trace
from aston.peak import Peak, PeakComponent


class TestBoxPeak(unittest.TestCase):
    def setUp(self):
        # box peak
        info = {}
        trace = Trace(np.ones(10), np.arange(10), name=1)
        baseline = Trace([0, 9], [0, 0], name=1)
        c = PeakComponent(info, trace, baseline)
        self.peak = Peak('box', components=c)

    def test_area(self):
        assert self.peak.area() == self.peak.area(1)


class TestGaussianPeak(TestBoxPeak):
    def setUp(self):
        # box peak
        info = {}
        v = [0.043, 0.067, 0.094, 0.117, 0.131,
             0.131, 0.117, 0.094, 0.067, 0.043]
        trace = Trace(v, np.arange(10), name=1)
        baseline = Trace([0, 9], [0, 0], name=1)
        c = PeakComponent(info, trace, baseline)
        self.peak = Peak('gaussian', components=c)
