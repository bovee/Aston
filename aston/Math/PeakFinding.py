import numpy as np
import scipy.signal._peak_finding as spf
from aston.Math.Chromatograms import savitzkygolay
from aston.Math.Chromatograms import movingaverage


def simple_peak_find(ts, start_slope=500, end_slope=200, \
                     min_peak_height=50, max_peak_width=1.5):
    """
    Given a TimeSeries, return a list of tuples
    indicating when peaks start and stop and what
    their baseline is.
    (t1, t2, hints)
    """
    #TODO: Isodat uses a PEAK_RESOLUTION, but we don't?
    #PEAK_RESOLUTION = 0.93

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
    #dxdt = np.gradient(movingaverage(ts, 5).y) / np.gradient(t)
    #dxdt = -savitzkygolay(ts, 5, 3, deriv=1).y / np.gradient(t)
    dxdt = np.gradient(ts.y) / np.gradient(t)

    hi_slopes = np.arange(len(dxdt))[dxdt > start_slope]
    # get the first points of any "runs" as a peak start
    peak_sts = [hi_slopes[0]] + \
      [j for i, j in slid_win(hi_slopes, 2) if j - i > 10]
    lo_slopes = np.arange(len(dxdt))[dxdt < -end_slope]
    # get the last points of any "runs" as a peak end
    peak_ens = [j for i, j in slid_win(lo_slopes[::-1], 2) \
                if i - j > 10] + [lo_slopes[-1]]
    #avals = np.arange(len(t))[np.abs(t - 3.5) < 0.5]
    #print([i for i in lo_slopes if i in avals])
    #print([(t[i], i) for i in peak_ens if i in avals])

    peak_list = []

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
            pk2 = pk + np.abs(t[pk:] - t[pk] - max_peak_width).argmin()

        pk_hgt = max(ts.y[pk:pk2]) - min(ts.y[pk:pk2])
        if pk_hgt > min_peak_height:
            peak_list.append((t[pk], t[pk2], {}))
    return peak_list


def wavelet_peak_find(ts):
    t = ts.time()

    widths = np.linspace(1, 100, 200)
    cwtm = spf.cwt(ts.y, spf.ricker, widths)
    ridges = spf._identify_ridge_lines(cwtm, widths / 2.0, 2)
    filt_ridges = spf._filter_ridge_lines(cwtm, ridges, \
      min_length=cwtm.shape[0] / 8.0, min_snr=1)

    #import matplotlib.pyplot as plt
    #plt.imshow(cwtm)  # extent=(widths[0], widths[-1], times[0], times[-1]))
    #for l in ridges:
    #    plt.plot(l[1], l[0], 'k-')
    #for l in filt_ridges:
    #    plt.plot(l[1], l[0], 'r-')
    ##plt.plot(peaks_t, peaks_w, 'k*')
    #plt.show()

    # loop through the ridges and find the point of maximum
    # intensity on the ridge and save its characteristics
    peak_list = []
    for i, l in enumerate(filt_ridges):
        pl = np.argmax([cwtm[j, k] for j, k in zip(l[0], l[1])])
        peak_w = widths[l[0][pl]] * 0.5 * (t[1] - t[0])
        peak_amp = cwtm[l[0][pl], l[1][pl]] / (widths[l[0]][pl] ** 0.5)
        peak_t = t[l[1][pl]]
        t0, t1 = peak_t - 3 * peak_w, peak_t + 3 * peak_w
        peak_list.append((t0, t1, {'area': peak_amp}))

    return peak_list
