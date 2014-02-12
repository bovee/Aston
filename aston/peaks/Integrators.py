import multiprocessing
import functools
import numpy as np
from aston.peaks.Peak import Peak
from aston.trace.Trace import AstonSeries
from aston.peaks.Math import time
from aston.peaks.PeakModels import peak_models
from aston.peaks.PeakFitting import guess_initc, fit


def simple_integrate(ts, peak_list, base_ts=None, intname='simple'):
    """
    Integrate each peak naively; without regard to overlap.

    This is used as the terminal step by most of the other integrators.
    """
    peaks = []
    for hints in peak_list:
        t0, t1 = hints['t0'], hints['t1']
        hints['int'] = intname
        pk_ts = ts.twin((t0, t1))
        if base_ts is None:
            # make a two point baseline
            base = AstonSeries([hints.get('y0', pk_ts[0]), \
                                hints.get('y1', pk_ts[-1])], \
                               [t0, t1], name=ts.name)
        else:
            base = base_ts.twin((t0, t1))
        peaks.append(Peak(hints, pk_ts, base, \
                          name='{:.2f}-{:.2f}'.format(t0, t1)))
    return peaks


def _get_windows(peak_list):
    """
    Given a list of peaks, bin them into windows.
    """
    win_list = []
    for hints in peak_list:
        p_w = hints['t0'], hints['t1']
        for w in win_list:
            if p_w[0] <= w[0][1] and p_w[1] >= w[0][0]:
                w[0] = (min(p_w[0], w[0][0]), \
                        max(p_w[1], w[0][1]))
                w[1].append([hints])
                break
        else:
            win_list.append([p_w, [hints]])
    return win_list


def constant_bl_integrate(ts, peak_list):
    temp_pks = []
    for hints in peak_list:
        min_y = np.min(ts.twin((hints['t0'], hints['t1'])).values)
        prop = hints.copy()
        prop['y0'], prop['y1'] = min_y, min_y
        temp_pks.append(prop)
    peaks = simple_integrate(ts, temp_pks, intname='constant_bl')
    return peaks


def drop_integrate(ts, peak_list):
    """
    Resolves overlap by breaking at the minimum value.
    """
    peaks = []
    for _, pks in _get_windows(peak_list):
        temp_pks = []
        pks = sorted(pks, key=lambda p: p['t0'])
        if 'y0' in pks[0] and 'y1' in pks[-1]:
            y0, y1 = pks[0]['y0'], pks[-1]['y1']
        else:
            y0 = ts.get_point('!', pks[0]['t0'])
            y1 = ts.get_point('!', pks[-1]['t1'])
        ys = np.array([y0, y1])
        xs = np.array([pks[0]['t0'], pks[-1]['t1']])

        # go through list of peaks to make sure there's no overlap
        for hints in pks:
            t0, t1 = hints['t0'], hints['t1']

            # figure out the y values (using a linear baseline)
            hints['y0'] = np.interp(t0, xs, ys)
            hints['y1'] = np.interp(t1, xs, ys)

            # if this peak totally overlaps with an existing one, don't add
            if sum(1 for p in temp_pks if t1 <= p[1]) > 0:
                continue
            overlap_pks = [p for p in temp_pks if t0 <= p[1]]
            if len(overlap_pks) > 0:
                # find the last of the overlapping peaks
                overlap_pk = max(overlap_pks, key=lambda p: p[0])
                # get the section of trace and find the lowest point
                over_ts = ts.trace('!', twin=(t0, overlap_pk[1]))
                min_t = over_ts.times[over_ts.y.argmin()]

                # delete the existing overlaping peak
                for i, p in enumerate(temp_pks):
                    if p == overlap_pk:
                        del temp_pks[i]
                        break

                # interpolate a new y value
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
        peaks += simple_integrate(ts, temp_pks, intname='drop')
    return peaks


def leastsq_integrate(ts, peak_list, f='gaussian'):
    #FIXME: transition from t0, t1, params to params (containing 't0'/'t1'
    # lookup the peak model function to use for fitting
    f = {f.__name__: f for f in peak_models}[f]

    peaks = []
    for w, peak_list in _get_windows(peak_list):
        tr = ts.trace(twin=w)
        # if there's location info, we can use this for
        # our inital params
        if 'x' in peak_list[0][2]:
            #TODO: should fill in other values?
            #TODO: should do something with y0 and y1?
            initc = [i[2] for i in peak_list]
        else:
            #TODO: should find peak maxima for rts?
            rts = [0.5 * (i[0] + i[1]) for i in peak_list]
            initc = guess_initc(tr, f, rts)
        params, _ = fit(tr, [f] * len(initc), initc)
        for p in params:
            pk_ts = AstonSeries(f(tr.times, **p), tr.times)
            info = {'name': '{:.2f}'.format(p['x'])}
            info['p-create'] = peak_list[0][2].get('pf', '') + \
                    ',' + 'leastsq_integrate'
            pk = Peak(info, pk_ts)
            peaks.append(pk)
    return peaks


def periodic_integrate(ts, peak_list, offset=0., period=1.):
    #TODO: should be a peak finder, not an integrator?
    movwin = lambda a, l:  np.lib.stride_tricks.as_strided(a, \
                 (a.shape[0] - l + 1, l), a.itemsize * np.ones(2))
    new_peak_list = []
    for hints in peak_list:
        t0, t1 = hints['t0'], hints['t1']

        # time the first whole "period" starts
        tpi = offset + period * ((t0 - offset) // period + 1)
        if tpi > t1:
            # the entire peak is within one "period"
            new_peak_list.append([t0, t1, hints])
            continue
        tp = np.hstack([[t0], np.arange(tpi, t1, period)])
        if tp[-1] != t1:
            # add the last point to the list
            tp = np.hstack([tp, [t1]])
        for tp0, tp1 in movwin(tp, 2):
            new_hints = {'pf': hints.get('pf', '')}
            if 'y0' in hints and 'y1' in hints:
                # calculate the new baseline for this peak
                xs, ys = [t0, t1], [hints['y0'], hints['y1']]
                new_hints['y0'] = np.interp(tp0, xs, ys)
                new_hints['y1'] = np.interp(tp1, xs, ys)
            new_peak_list.append([tp0, tp1, new_hints])

    peaks = simple_integrate(ts, new_peak_list)
    for p in peaks:
        p.info['p-create'] = p.info['p-create'].split(',')[0] + \
                ',periodic_integrate'
    return peaks


def merge_ions(pks):
    cleaned_pks = []
    sort_pks = sorted(pks, key=lambda pk: time(pk.as_poly()))
    cur_t = np.nan
    for pk in sort_pks:
        if np.abs(cur_t - time(pk.as_poly())) < 0.01:
            c_pk = cleaned_pks[-1]
            if not c_pk.data.has_ion(pk.data.ions[0]):
                c_pk.set_baseline(pk.data.ions[0], pk.baseline())
                c_pk.rawdata = c_pk.rawdata & pk.rawdata
                if 's-mzs' in c_pk.info:
                    del c_pk.info['s-mzs']
            else:
                cleaned_pks.append(pk)
        else:
            cleaned_pks.append(pk)
        cur_t = time(pk.as_poly())
    return cleaned_pks


def _integrate_mpwrap(ts_and_pks, integrate, fopts):
    """
    Take a zipped timeseries and peaks found in it
    and integrate it to return peaks.
    """
    ts, tpks = ts_and_pks
    pks = integrate(ts, tpks, **fopts)
    for p in pks:
        p.hints['mz'] = str(ts.name)
    return pks


def integrate_peaks(tss, peaks_found, int_f, f_opts={}, \
                    isomode=False, mp=False):
    f = functools.partial(_integrate_mpwrap, integrate=int_f, fopts=f_opts)
    if mp:
        po = multiprocessing.Pool()
        all_pks = po.map(f, zip(tss, peaks_found))
        po.close()
        po.join()
    else:
        all_pks = list(map(f, zip(tss, peaks_found)))

    # merge peaks from all_pks together
    if isomode:
        mrg_pks = []
        for sub_pks in zip(*all_pks):
            c_pk = sub_pks[0]
            for pk in sub_pks[1:]:
                ion = pk.data.ions[0]
                c_pk.set_baseline(ion, pk.baseline(ion))
                c_pk.rawdata = c_pk.rawdata & pk.rawdata
            mrg_pks.append(c_pk)
    else:
        mrg_pks = merge_ions([pk for pks in all_pks for pk in pks])
    return mrg_pks
