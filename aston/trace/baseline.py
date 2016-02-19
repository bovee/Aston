import numpy as np
from scipy.stats import gaussian_kde
from scipy.optimize import fmin, brentq
from aston.trace.trace import Trace
from aston.trace.math_traces import savitzkygolay


def base(s, slope_tol='5.0', off_tol='5.0'):
    ic = savitzkygolay(s, 5, 3)[0]
    slopes = np.diff(ic) / np.diff(s.index)
    wind = np.array([0.5, 0.5])
    offsets = np.convolve(ic, wind, mode='valid')
    offsets -= slopes * np.convolve(s.index, wind, mode='valid')

    sl_kern = gaussian_kde(slopes)
    base_slope = fmin(lambda x: -sl_kern(x), 0, disp=False)
    k_h = sl_kern(base_slope) * (1.0 - 10 ** -float(slope_tol))
    s1 = brentq(lambda x: sl_kern(x) - k_h, min(slopes), base_slope)
    s2 = brentq(lambda x: sl_kern(x) - k_h, base_slope, max(slopes))

    valid = np.logical_and(slopes > s1, slopes < s2)
    off_kern = gaussian_kde(offsets[valid])
    base_off = fmin(lambda x: -off_kern(x), 0, disp=False)
    k_h = off_kern(base_off) * (1.0 - 10 ** -float(off_tol))
    o1 = brentq(lambda x: off_kern(x) - k_h, min(offsets), base_off)
    o2 = brentq(lambda x: off_kern(x) - k_h, base_off, max(offsets))

    msk = np.logical_and(valid, offsets > o1)
    msk = np.logical_and(valid, offsets < o2)
    new_ic = np.interp(s.index, s.index[msk], ic[msk])
    return Trace(new_ic, s.index)


def base2(ic, t):
    # INSPIRED by Algorithm A12 from Zupan
    # 5 point pre-smoothing
    sc = np.convolve(np.ones(5) / 5.0, ic, mode='same')
    # get local minima
    mn = np.arange(len(ic))[np.r_[True, ((sc < np.roll(sc, 1)) & (sc < np.roll(sc, -1)))[1:-1], True]]  # noqa
    # don't allow baseline to have a slope greater than
    # 10x less than the steepest peak
    max_slope = np.max(np.gradient(ic)) / 10.0
    slope = max_slope
    pi = 0  # previous index
    oc = np.zeros(len(ic))
    for i in range(1, len(mn)):
        if slope < ((ic[mn[i]] - ic[mn[pi]]) /
                    (mn[i] - mn[pi])) and slope < max_slope:
            # add trend
            oc[mn[pi]:mn[i - 1]] = np.linspace(ic[mn[pi]], ic[mn[i - 1]],
                                               mn[i - 1] - mn[pi])
            pi = i - 1
        slope = (ic[mn[i]] - ic[mn[pi]]) / (mn[i] - mn[pi])
    print(mn[pi], mn[-1])
    oc[mn[pi]:mn[-1]] = np.linspace(ic[mn[pi]], ic[mn[-1]], mn[-1] - mn[pi])
    oc[-1] = oc[-2]  # FIXME: there's definitely a bug in here somewhere
