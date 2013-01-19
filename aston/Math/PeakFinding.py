import numpy as np
from aston.Math.Chromatograms import savitzkygolay


def simple_peak_find(ts):
    """
    Given a TimeSeries, return a list of tuples
    indicating when peaks start and stop and what
    their baseline is.
    (t1, y1, t2, y2)
    """
    START_SLOPE = 0.2
    END_SLOPE = 0.4
    MIN_PEAK_HEIGHT = 50
    PEAK_RESOLUTION = 0.93
    MAX_PEAK_WIDTH = 0.75

    def slid_win(itr, size=2):
        """Returns a sliding window of size size along itr."""
        itr = iter(itr)
        buf = []
        for _ in range(size):
            buf += [next(itr)]
        for l in itr:
            yield buf
            buf = buf[1:] + [l]
        yield buf

    #TODO: check these smoothing defaults
    t = ts.times
    dxdt = savitzkygolay(ts.y, 5, 3, deriv=1) / np.gradient(t)
    start_slopes = np.arange(len(dxdt))[dxdt > START_SLOPE]
    # get the first points of any "runs" as a peak start
    peak_st = [start_slopes[0]] + \
      [j for i, j in slid_win(start_slopes, 2) if j - i > 5]
    end_slopes = np.arange(len(dxdt))[dxdt < -END_SLOPE]
    # get the first points of any "runs" as a peak end
    peak_en = [end_slopes[-1]] + \
      [i for i, j in slid_win(end_slopes[::-1], 2) if i - j > 5]

    pass

def wavelet_peak_find(ts):
    pass
