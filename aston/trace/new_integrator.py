import numpy as np
from aston.peak.peak_finding import simple_peak_find
from aston.peak.integrators import simple_integrate


def _get_windows(peak_list):
    """
    Given a list of peaks, bin them into windows.
    """
    win_list = []
    for t0, t1, hints in peak_list:
        p_w = (t0, t1)
        for w in win_list:
            if p_w[0] <= w[0][1] and p_w[1] >= w[0][0]:
                w[0] = (min(p_w[0], w[0][0]), max(p_w[1], w[0][1]))
                w[1].append((t0, t1, hints))
                break
        else:
            win_list.append([p_w, [(t0, t1, hints)]])
    return win_list


def integrate(s, peak_list=None, baseline=None, overlap='drop'):
    """

    """
    # for convenience, if no peak_list is provided create our own
    if peak_list is None:
        peak_list = simple_peak_find(s)

    peaks = []
    for _, pks in _get_windows(peak_list):
        temp_pks = []
        pks = sorted(pks, key=lambda p: p[0])
        if 'y0' in pks[0][2] and 'y1' in pks[-1][2]:
            y0, y1 = pks[0][2]['y0'], pks[-1][2]['y1']
        else:
            y0 = s.get_point('!', pks[0][0])
            y1 = s.get_point('!', pks[-1][1])
        ys = np.array([y0, y1])
        xs = np.array([pks[0][0], pks[-1][1]])

        # go through list of peaks to make sure there's no overlap
        for t0, t1, hints in pks:
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
                over_ts = s.trace('!', twin=(t0, overlap_pk[1]))
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
        peaks += simple_integrate(s, temp_pks)
    for p in peaks:
        p.info['p-create'] = p.info['p-create'].split(',')[0] + \
            ',drop_integrate'
    return peaks


def integrate_analytical(s, foundpeaks=None, baseline=None):
    pass
