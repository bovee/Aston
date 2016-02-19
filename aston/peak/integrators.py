import multiprocessing
import functools
import numpy as np
from aston.trace.trace import Trace
from aston.peak.peak import Peak, PeakComponent
from aston.peak.peak_models import peak_models
from aston.peak.peak_fitting import guess_initc, fit


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
            base = Trace([hints.get('y0', pk_ts[0]),
                          hints.get('y1', pk_ts[-1])],
                         [t0, t1], name=ts.name)
        else:
            base = base_ts.twin((t0, t1))
        peaks.append(PeakComponent(hints, pk_ts, base))
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
                w[0] = (min(p_w[0], w[0][0]), max(p_w[1], w[0][1]))
                w[1].append(hints)
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
            y0 = ts.get_point(pks[0]['t0'])
            y1 = ts.get_point(pks[-1]['t1'])
        ys = np.array([y0, y1])
        xs = np.array([pks[0]['t0'], pks[-1]['t1']])

        # go through list of peaks to make sure there's no overlap
        for hints in pks:
            t0, t1 = hints['t0'], hints['t1']

            # figure out the y values (using a linear baseline)
            hints['y0'] = np.interp(t0, xs, ys)
            hints['y1'] = np.interp(t1, xs, ys)

            # if this peak totally overlaps with an existing one, don't add
            if sum(1 for p in temp_pks if t1 <= p['t1']) > 0:
                continue
            overlap_pks = [p for p in temp_pks if t0 <= p['t1']]
            if len(overlap_pks) > 0:
                # find the last of the overlapping peaks
                overlap_pk = max(overlap_pks, key=lambda p: p['t0'])
                # get the section of trace and find the lowest point
                over_ts = ts.twin((t0, overlap_pk['t1']))
                min_t = over_ts.index[over_ts.values.argmin()]

                # delete the existing overlaping peak
                for i, p in enumerate(temp_pks):
                    if p == overlap_pk:
                        del temp_pks[i]
                        break

                # interpolate a new y value
                y_val = np.interp(min_t, xs, ys)
                overlap_pk['y1'] = y_val
                hints['y0'] = y_val

                # add the old and new peak in
                overlap_pk['t1'] = min_t
                temp_pks.append(overlap_pk)
                hints['t0'], hints['t1'] = min_t, t1
                temp_pks.append(hints)
            else:
                hints['t0'], hints['t1'] = t0, t1
                temp_pks.append(hints)

        # none of our peaks should overlap, so we can just use
        # simple_integrate now
        peaks += simple_integrate(ts, temp_pks, intname='drop')
    return peaks


def leastsq_integrate(ts, peak_list, f='gaussian'):
    # FIXME: transition from t0, t1, params to params (containing 't0'/'t1'
    # lookup the peak model function to use for fitting
    f = {f.__name__: f for f in peak_models}[f]

    peaks = []
    for w, peak_list in _get_windows(peak_list):
        tr = ts.trace(twin=w)
        # if there's location info, we can use this for
        # our inital params
        if 'x' in peak_list[0][2]:
            # TODO: should fill in other values?
            # TODO: should do something with y0 and y1?
            initc = [i[2] for i in peak_list]
        else:
            # TODO: should find peak maxima for rts?
            rts = [0.5 * (i[0] + i[1]) for i in peak_list]
            initc = guess_initc(tr, f, rts)
        params, _ = fit(tr, [f] * len(initc), initc)
        for p in params:
            pk_ts = Trace(f(tr.times, **p), tr.times)
            info = {'name': '{:.2f}'.format(p['x'])}
            info['p-create'] = '{},leastsq_integrate'.format(
                peak_list[0][2].get('pf', '')
            )
            pk = PeakComponent(info, pk_ts)
            peaks.append(pk)
    return peaks


def periodic_integrate(ts, peak_list, offset=0., period=1.):
    # TODO: should be a peak finder, not an integrator?
    def movwin(a, l):
        return np.lib.stride_tricks.as_strided(a, (a.shape[0] - l + 1, l),
                                               a.itemsize * np.ones(2))
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
        p.info['p-create'] = '{},periodic_integrate'.format(
            p.info['p-create'].split(',')[0]
        )
    return peaks


def _peakcomp_to_name(pkc):
    return '{:.3f}-{:.3f}'.format(pkc.info['t0'], pkc.info['t1'])


def merge_peaks_by_time(pks_list, time_diff=0.01):
    sort_pks = sorted([pk for pks in pks_list for pk in pks],
                      key=lambda pk: pk.time())

    # add the first component in as a peak
    pkc = sort_pks[0]
    pk = Peak(name=_peakcomp_to_name(pkc), components=[pkc])
    mrg_pks = [pk]

    for pkc in sort_pks[1:]:
        c_pk = mrg_pks[-1]
        if np.abs(c_pk.components[0].time() - pkc.time()) < time_diff and \
           pkc._trace.name not in {c._trace.name for c in c_pk.components}:
            c_pk.components.append(pkc)
        else:
            pk = Peak(name=_peakcomp_to_name(pkc), components=[pkc])
            mrg_pks.append(pk)
    return mrg_pks


def merge_peaks_by_order(pks_list):
    """

    All lists of peaks need to be the same length.
    """
    mrg_pks = []
    for sub_pks in zip(*pks_list):
        pk = Peak(name=_peakcomp_to_name(sub_pks[0]), components=sub_pks)
        mrg_pks.append(pk)
    return mrg_pks


def _integrate_mpwrap(ts_and_pks, integrate, fopts):
    """
    Take a zipped timeseries and peaks found in it
    and integrate it to return peaks. Used to allow
    multiprocessing support.
    """
    ts, tpks = ts_and_pks
    pks = integrate(ts, tpks, **fopts)
    # for p in pks:
    #     p.info['mz'] = str(ts.name)
    return pks


def integrate_peaks(tss, peaks_found, int_f, f_opts={},
                    as_first=False, mp=False):
    f = functools.partial(_integrate_mpwrap, integrate=int_f, fopts=f_opts)
    if mp:
        po = multiprocessing.Pool()
        all_pks = po.map(f, zip(tss, peaks_found))
        po.close()
        po.join()
    else:
        all_pks = list(map(f, zip(tss, peaks_found)))

    # merge peaks from all_pks together
    if as_first:
        mrg_pks = merge_peaks_by_order(all_pks)
    else:
        mrg_pks = merge_peaks_by_time(all_pks)
    return mrg_pks
