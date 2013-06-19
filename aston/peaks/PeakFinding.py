import multiprocessing
import functools
import numpy as np
#from aston.Math.Chromatograms import savitzkygolay
from aston.timeseries.Math import movingaverage


def simple_peak_find(ts, init_slope=500, start_slope=500, end_slope=200, \
                     min_peak_height=50, max_peak_width=1.5):
    """
    Given a TimeSeries, return a list of tuples
    indicating when peaks start and stop and what
    their baseline is.
    (t1, t2, hints)
    """
    point_gap = 10

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
    smooth_y = movingaverage(ts, 9).y
    dxdt = np.gradient(smooth_y) / np.gradient(t)
    #dxdt = -savitzkygolay(ts, 5, 3, deriv=1).y / np.gradient(t)

    init_slopes = np.arange(len(dxdt))[dxdt > init_slope]
    if len(init_slopes) == 0:
        return []
    # get the first points of any "runs" as a peak start
    # runs can have a gap of up to 10 points in them
    peak_sts = [init_slopes[0]] + \
      [j for i, j in slid_win(init_slopes, 2) if j - i > 10]
    peak_sts.sort()

    en_slopes = np.arange(len(dxdt))[dxdt < -end_slope]
    if len(en_slopes) == 0:
        return []
    # filter out any lone points farther than 10 away from their neighbors
    en_slopes = [en_slopes[0]] + [i[1] for i in slid_win(en_slopes, 3) \
                 if i[1] - i[0] < point_gap or \
                 i[2] - i[1] < point_gap] + [en_slopes[-1]]
    # get the last points of any "runs" as a peak end
    peak_ens = [j for i, j in slid_win(en_slopes[::-1], 2) \
                if i - j > point_gap] + [en_slopes[-1]]
    peak_ens.sort()
    #avals = np.arange(len(t))[np.abs(t - 0.675) < 0.25]
    #print([i for i in en_slopes if i in avals])
    #print([(t[i], i) for i in peak_ens if i in avals])

    peak_list = []
    pk2 = 0
    for pk in peak_sts:
        # don't allow overlapping peaks
        if pk < pk2:
            continue

        # track backwards to find the true start
        while dxdt[pk] > start_slope and pk > 0:
            pk -= 1

        # now find where the peak ends
        dist_to_end = np.array(peak_ens) - pk
        pos_end = pk + dist_to_end[dist_to_end > 0]
        for pk2 in pos_end:
            if (ts.y[pk2] - ts.y[pk]) / (t[pk2] - t[pk]) > start_slope:
                # if the baseline beneath the peak is too large, let's
                # keep going to the next dip
                peak_list.append((t[pk], t[pk2], {}))
                pk = pk2
            elif t[pk2] - t[pk] > max_peak_width:
                # make sure that peak is short enough
                pk2 = pk + np.abs(t[pk:] - t[pk] - \
                                  max_peak_width).argmin()
                break
            else:
                break
        else:
            # if no end point is found, the end point
            # is the end of the timeseries
            pk2 = len(ts.y) - 1

        if pk == pk2:
            continue
        pk_hgt = max(ts.y[pk:pk2]) - min(ts.y[pk:pk2])
        if pk_hgt < min_peak_height:
            continue
        peak_list.append((t[pk], t[pk2], {}))
    return peak_list


def wavelet_peak_find(ts, min_snr=1., assume_sig=4., min_length=8.0,
                      max_dist=4.0, gap_thresh=2.0):
    # this import is here to let scipy 0.9.0 at least
    # load this module
    import scipy.signal._peak_finding as spf
    t = ts.time()

    widths = np.linspace(1, 100, 200)
    cwtm = spf.cwt(ts.y, spf.ricker, widths)
    ridges = spf._identify_ridge_lines(cwtm, widths / max_dist, gap_thresh)
    filt_ridges = spf._filter_ridge_lines(cwtm, ridges, \
      min_length=cwtm.shape[0] / min_length, min_snr=min_snr)

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


def event_peak_find(ts, events, adjust_times=False):
    if adjust_times:
        # for the following, we need to assume ts is constantly spaced
        t = ts.times

        #convert list of events into impulses that will correlate
        #with spikes in the derivative (such as peak beginning & ends)
        pulse_y = np.zeros(len(t))
        for st_t, en_t, hints in events:
            pulse_y[np.argmin(np.abs(t - st_t))] = 1.
            pulse_y[np.argmin(np.abs(t - en_t))] = -1.
        cor = np.correlate(pulse_y, np.gradient(ts.y), mode='same')

        #apply weighting to cor to make "far" correlations less likely
        cor[:len(t) // 2] *= np.logspace(0., 1., len(t) // 2)
        cor[len(t) // 2:] *= np.logspace(1., 0., len(t) - len(t) // 2)

        shift = (len(t) // 2 - cor.argmax()) * (t[1] - t[0])
        new_evts = [(t0 + shift, t1 + shift, {}) for t0, t1, _ in events]
        return new_evts
    else:
        return events


def peak_find_mpwrap(ts, peak_find, fopts, dt=None):
    if peak_find == event_peak_find and dt is not None:
        # event_peak_find also needs a list of events
        evts = []
        if dt is not None:
            for n in ('fia', 'fxn', 'refgas'):
                evts += dt.events(n)
            tpks = peak_find(ts, evts, **fopts)
        else:
            tpks = []
    else:
        tpks = peak_find(ts, **fopts)
    for pk in tpks:
        pk[2]['pf'] = peak_find.__name__
    return tpks


def find_peaks(tss, pf_f, f_opts={}, dt=None, isomode=False, mp=False):
    if isomode:
        peaks_found = [peak_find_mpwrap(tss[0], pf_f, f_opts, dt)]
        for ts in tss[1:]:
            tpks = []
            for p in peaks_found[0]:
                old_pk_ts = tss[0].twin((p[0], p[1]))
                old_t = old_pk_ts.times[old_pk_ts.y.argmax()]
                new_pk_ts = ts.twin((p[0], p[1]))
                off = new_pk_ts.times[new_pk_ts.y.argmax()] - old_t
                new_p = (p[0] + off, p[1] + off, p[2])
                tpks.append(new_p)
            peaks_found.append(tpks)
    elif mp and pf_f != event_peak_find:
        # event_peak_find needs the datafile, which can't be pickled
        # and hence can't be passed into any multiprocessing code
        f = functools.partial(peak_find_mpwrap, peak_find=pf_f, \
                            fopts=f_opts)
        po = multiprocessing.Pool()
        peaks_found = po.map(f, tss)
    else:
        f = functools.partial(peak_find_mpwrap, peak_find=pf_f, \
                            fopts=f_opts, dt=dt)
        peaks_found = list(map(f, tss))
    return peaks_found
