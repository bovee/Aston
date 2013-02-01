import numpy as np
import scipy.signal._peak_finding as spf
#from aston.Math.Chromatograms import savitzkygolay
#from aston.Math.Chromatograms import movingaverage


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
            pk2 = len(ts.y) - 1
        else:
            pk2 = pk + pos_dist_to_end.min()

        # make sure that peak is short enough
        if t[pk2] - t[pk] > max_peak_width:
            pk2 = pk + np.abs(t[pk:] - t[pk] - max_peak_width).argmin()

        pk_hgt = max(ts.y[pk:pk2]) - min(ts.y[pk:pk2])
        if pk_hgt > min_peak_height:
            peak_list.append((t[pk], t[pk2], {}))
    return peak_list


def wavelet_peak_find(ts, min_snr=1., assume_sig=4.):
    t = ts.time()

    widths = np.linspace(1, 100, 200)
    cwtm = spf.cwt(ts.y, spf.ricker, widths)
    ridges = spf._identify_ridge_lines(cwtm, widths / 2.0, 2)
    filt_ridges = spf._filter_ridge_lines(cwtm, ridges, \
      min_length=cwtm.shape[0] / 8.0, min_snr=min_snr)

    ## the next code is just to visualize how this works
    #import matplotlib.pyplot as plt
    #plt.imshow(cwtm)  # extent=(widths[0], widths[-1], times[0], times[-1]))
    #for l in ridges:
    #    plt.plot(l[1], l[0], 'k-')
    #for l in filt_ridges:
    #    plt.plot(l[1], l[0], 'r-')
    ##plt.plot(peaks_t, peaks_w, 'k*')  # not working
    #plt.show()

    # loop through the ridges and find the point of maximum
    # intensity on the ridge and save its characteristics
    peak_list = []
    for i, l in enumerate(filt_ridges):
        pl = np.argmax([cwtm[j, k] for j, k in zip(l[0], l[1])])
        peak_w = widths[l[0][pl]] * 0.5 * (t[1] - t[0])
        peak_amp = cwtm[l[0][pl], l[1][pl]] / (widths[l[0]][pl] ** 0.5)
        peak_t = t[l[1][pl]]
        t0, t1 = peak_t - assume_sig * peak_w, peak_t + assume_sig * peak_w
        peak_list.append((t0, t1, {'x': peak_t, 'h': peak_amp, \
                                   'w': peak_w}))
    return peak_list


def stat_slope_peak_find(ts):
    #TODO: this isn't working the best right now
    t = ts.time()

    dx = np.gradient(ts.y)
    dx2 = np.gradient(dx)

    adx = np.average(dx)
    adx2 = np.average(dx2)
    l_i = -2

    #old loop checked for concavity too; prob. not necessary
    #for i in np.arange(len(t))[dx>adx+np.std(dx[abs(dx2)<adx2+np.std(dx2)])]:

    peak_list = []
    #loop through all of the points that have a slope
    #outside of one std. dev. from average
    for i in np.arange(len(t))[dx > adx + np.std(dx)]:
        if i - l_i == 1:
            l_i = i
            continue

        #track backwards to find where this peak started
        pt0 = None
        for j in range(i - 1, 0, -1):
            if dx[j] < adx or dx2[j] < adx2:
                pt0 = t[j]
                break

        #track forwards to find where it ends
        pt1 = None
        neg = 0
        for j in range(i, len(t)):
            if dx[j] < adx:
                neg += 1
            if neg > 3 and dx[j] > adx:  # and x[j]<ax:
                pt1 = t[j]
                break

        if pt0 is not None and pt1 is not None:
            peak_list += [(pt0, pt1, {})]

    return peak_list


def event_peak_find(ts, events):
    #TODO: don't just integrate the entire space
    # from point to point. integrate from
    # baseline point to other baseline point
    return align_events(ts, events)


def align_events(ts, evts):
    # assume ts is constantly spaced
    t = ts.times

    #convert list of initial times into impulses
    #that will correlate with spikes in the
    #derivative (such as at the beginning of a peak)
    pulse_y = np.zeros(len(t))
    for st_t in [p[0] for p in evts]:
        pulse_y[np.argmin(np.abs(t - st_t))] = 1.
    cor = np.correlate(pulse_y, np.gradient(ts.y), mode='same')

    #apply weighting to cor to make "far" correlations less likely
    cor[:len(t) // 2] *= np.logspace(0., 1., len(t) // 2)
    cor[len(t) // 2:] *= np.logspace(1., 0., len(t) - len(t) // 2)

    shift = (len(t) // 2 - cor.argmax()) * (t[1] - t[0])
    #TODO: track back slightly to catch start of peak, not maximum
    # slope of peak?
    new_evts = [(t0 + shift, t1 + shift, {}) for t0, t1, _ in evts]
    return new_evts
