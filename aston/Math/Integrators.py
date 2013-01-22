import numpy as np
#import scipy.ndimage as nd
from scipy.optimize import leastsq  # , fmin, minimize
from aston.Features import Peak
from aston.TimeSeries import TimeSeries
from aston.Math.Peak import time


def update_peaks(peaks, dt, ion, ptype='Sample', created='manual'):
    for p in peaks:
        p.db, p.parent_id = dt.db, dt.db_id
        p.info['trace'] = ion
        p.info['p-create'] = created
        p.info['p-type'] = ptype


def simple_integrate(ts, peak_list):
    """
    Integrate each peak naively; without regard to overlap.
    """
    peaks = []
    for t0, t1, hints in peak_list:
        pk_ts = ts.trace('!', twin=(t0, t1))
        if 'y0' in hints and 'y1' in hints:
            d = np.vstack([hints['y0'], ts.data, hints['y1']])
            t = np.hstack([t0, ts.times, t1])
            pk_ts = TimeSeries(d, t, ts.ions)
        info = {'name': '{:.2f}-{:.2f}'.format(t0, t1)}
        pk = Peak(None, None, None, info, pk_ts)
        peaks.append(pk)
    return peaks


def _get_windows(peak_list):
    """
    Given a list of peaks, bin them into windows.
    """
    win_list = []
    for t0, t1, hints in peak_list:
        p_w = (t0, t1)
        for w in win_list:
            if p_w[0] <= w[0][1] and p_w[1] >= w[0][0]:
                w[0] = (min(p_w[0], w[0][0]), \
                        max(p_w[1], w[0][1]))
                w[1].append((t0, t1, hints))
                break
        else:
            win_list.append([p_w, [(t0, t1, hints)]])
    return win_list


def drop_integrate(ts, peak_list):
    """
    Resolves overlap by breaking at the minimum value.
    """
    peaks = []
    for _, pks in _get_windows(peak_list):
        temp_pks = []
        pks = sorted(pks, key=lambda p: p[0])
        # go through list of peaks to make sure there's no overlap
        for t0, t1, hints in pks:
            # if this peak totally overlaps with an existing one, don't add
            if sum(1 for p in temp_pks if t1 <= p[0]) > 0:
                continue
            overlap_pks = [p for p in temp_pks if t0 <= p[1]]
            if len(overlap_pks) > 0:
                # find the last of the overlapping peaks
                overlap_pk = max(overlap_pks, key=lambda p: p[0])
                # get the section of trace and find the lowest point
                over_ts = ts.trace('!', twin=(t0, overlap_pk[1]))
                min_t = over_ts.times[over_ts.y.arg_min()]

                # delete the existing overlaping peak
                for i, p in enumerate(temp_pks):
                    if p == overlap_pk:
                        del temp_pks[i]
                        break

                # if there are y-values, interpolate a new one
                if 'y0' in overlap_pk[2] and 'y1' in hints:
                    xs = np.array([overlap_pk[0], t1])
                    ys = np.array([overlap_pk[2]['y0'], hints['y1']])
                    y_val = np.interp(min_t, xs, ys)
                    overlap_pk[2]['y1'] = y_val
                    hints['y0'] = y_val

                # add the old and new peak in
                temp_pks.append((overlap_pk[0], min_t, overlap_pk[2]))
                temp_pks.append((min_t, t1, hints))
            else:
                temp_pks.append((t0, t1, hints))

        # none of our peaks should overlap, so we can just use
        # simple_integrate now
        peaks += simple_integrate(ts, temp_pks)
    return peaks


def leastsq_integrate(ts, peak_list):
    win_list = _get_windows(peak_list)

    def sim_chr(p, times):
        gauss = lambda t, h, w: h * np.exp(-t ** 2 / (2 * w ** 2))
        c = p[0] + times * p[1]
        for i in range(int((len(p) - 2) / 3)):
            t, h, w = p[2 + 3 * i:5 + 3 * i]
            c += gauss(times - t, h, w)
        return c

    errf = lambda p, y, t: sum(y - sim_chr(p, t))

    for w in win_list:
        tr = ts.trace(twin=w[0]).y
        #TODO: build proper starting parameters (including area)
        p0 = np.insert(np.array(w[1]), 0, [tr.y[0], 0])
        #p, r1, r2, r3, r4 = leastsq(errf, p0[:],
        #        args=(tr.y, tr.times), full_output=True, maxfev=10)

        # crashes: TypeError
        #p = minimize(errf, p0[:], method='nelder-mead',
        #        args=(tr.y, tr.times), options={'disp':True})
        #print(p, dir(p))

        #TODO: decompose p into proper peaks

        #plotter.plt.plot(tr.t, sim_chr(p0, tr.times), 'k-')
    #p, r1, r2, r3, r4 = leastsq(errf, p0[:],
    #        args=(x, times), full_output=True, maxfev=10)
    #print(r2['nfev'], r3, r4)
    #plotter.plt.plot(times, sim_chr(p, times), 'k-')


def statSlopeIntegrate(ts, **kwargs):
    x = ts.y
    t = ts.time()
    pks = []

    dx = np.gradient(x)
    dx2 = np.gradient(dx)

    adx = np.average(dx)
    adx2 = np.average(dx2)
    l_i = -2

    #old loop checked for concavity too; prob. not necessary
    #for i in np.arange(len(t))[dx>adx+np.std(dx[abs(dx2)<adx2+np.std(dx2)])]:

    #loop through all of the points that have a slope
    #outside of one std. dev. from average
    for i in np.arange(len(t))[dx > adx + np.std(dx)]:
        if i - l_i == 1:
            l_i = i
            continue

        #track backwards to find where this peak started
        pt1 = ()
        for j in range(i - 1, 0, -1):
            if dx[j] < adx or dx2[j] < adx2:
                pt1 = (t[j], x[j])
                break

        #track forwards to find where it ends
        pt2 = ()
        neg = 0
        for j in range(i, len(t)):
            if dx[j] < adx:
                neg += 1
            if neg > 3 and dx[j] > adx:  # and x[j]<ax:
                pt2 = (t[j], x[j])
                break

        #create a peak and add it to the peak list
        if pt1 != () and pt2 != ():
            pk_ts = ts.trace('!', twin=(pt1[0], pt2[0]))
            info = {'name': '{:.2f}-{:.2f}'.format(pt1[0], pt2[0])}
            pk = Peak(None, None, None, info, pk_ts)
            pks.append(pk)
        l_i = i
    return pks


def merge_ions(pks):
    cleaned_pks = []
    sort_pks = sorted(pks, key=lambda pk: time(pk.as_poly()))
    cur_t = np.nan
    for pk in sort_pks:
        if np.abs(cur_t - time(pk.as_poly())) < 0.01:
            c_pk = cleaned_pks[-1]
            if c_pk.data.ions[0] != pk.data.ions[0]:
                c_pk.rawdata = c_pk.rawdata & pk.rawdata
                if 's-mzs' in c_pk.info:
                    del c_pk.info['s-mzs']
            else:
                cleaned_pks.append(pk)
        else:
            cleaned_pks.append(pk)
        cur_t = time(pk.as_poly())

    return cleaned_pks
