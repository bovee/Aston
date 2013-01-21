import numpy as np
from aston.Math.Chromatograms import savitzkygolay


def simple_peak_find(ts, start_slope=0.2, end_slope=0.4, \
                     min_peak_height=50, max_peak_width=0.75):
    """
    Given a TimeSeries, return a list of tuples
    indicating when peaks start and stop and what
    their baseline is.
    (t1, t2, hints)
    """
    #START_SLOPE = 0.2
    #END_SLOPE = 0.4
    #MIN_PEAK_HEIGHT = 50
    ##PEAK_RESOLUTION = 0.93
    #MAX_PEAK_WIDTH = 0.75

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
    dxdt = -savitzkygolay(ts, 5, 3, deriv=1).y / np.gradient(t)

    hi_slopes = np.arange(len(dxdt))[dxdt > start_slope]
    # get the first points of any "runs" as a peak start
    peak_sts = [hi_slopes[0]] + \
      [j for i, j in slid_win(hi_slopes, 2) if j - i > 5]
    print(t[hi_slopes[:50]])
    print(t[peak_sts][:5])
    lo_slopes = np.arange(len(dxdt))[dxdt < -end_slope]
    # get the last points of any "runs" as a peak end
    peak_ens = [lo_slopes[-1]] + \
      [i for i, j in slid_win(lo_slopes[::-1], 2) if i - j > 5]

    peaks = []

    for pk in peak_sts:
        dist_to_end = np.array(peak_ens) - pk
        pos_dist_to_end = dist_to_end[dist_to_end > 0]
        # if no end point is found, the end point
        # is the end of the timeseries
        if len(pos_dist_to_end) == 0:
            pk2 = len(ts.y)
        else:
            pk2 = pk + pos_dist_to_end.min()

        # make sure that peak is short enough
        if t[pk2] - t[pk] > max_peak_width:
            pk2 = pk + np.abs(t[pk:] - max_peak_width).argmin()

        pk_hgt = max(ts.y[pk:pk2]) - min(ts.y[pk:pk2])
        if pk_hgt > min_peak_height:
            peaks.append((t[pk], t[pk2], {}))
    return peaks


def wavelet_peak_find(ts):
    pass
