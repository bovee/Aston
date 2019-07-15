import numpy as np
from scipy.optimize import leastsq
from aston.trace import Trace
from aston.spectra.isotopes import delta13c_santrock


def ratio_f(pks, r2=45, r1=44):
    # pull out the time and ratio information
    isopks = [pk for pk in pks if pk.info.get('p-type') == 'isostd']
    x = [pk.time() for pk in isopks if pk.area(mz=r1) > 0]
    y = [pk.area(mz=r2) / pk.area(mz=r1)
         for pk in isopks if pk.area(mz=r1) > 0]

    if len(y) < 1:
        return None

    # initial condition for fitting
    p0 = [y[0], 0]

    # function to fit
    def errfunc(p, x, y):
        return p[0] + p[1] * x - y

    # try fitting; if it doesn't work, just use first ratio peak
    try:
        p, succ = leastsq(errfunc, p0, args=(np.array(x), np.array(y)))
    except Exception:
        p = p0

    # construct a function from the fitted data
    def sim_y(t):
        if isinstance(t, (list, tuple, np.ndarray)):
            return np.array(errfunc(p, t, np.zeros(len(t))))
        else:
            return np.array(errfunc(p, t, 0))
    return sim_y


def ratio_series(ts, pks, r2, r1):
    sim_y = ratio_f(pks, r2, r1)
    return Trace(sim_y(ts.index), ts.index,
                 name='{:.1f}/{:.1f}'.format(r2, r1))


def calc_carbon_isotopes(pks, d13cstd, ks='Craig', d18ostd=23.5):
    # get functions to tell us what the ratios of the standards
    # should be over the course of the run
    r45 = ratio_f(pks, r2=45, r1=44)
    r46 = ratio_f(pks, r2=46, r1=44)

    if r45 is None or r46 is None:
        for pk in pks:
            del pk.info['p-d13c']
        return

    for pk in pks:
        # determine the peak areas for our peak and an interpolated standard
        r45sam = pk.area(45) / pk.area(44)
        r46sam = pk.area(46) / pk.area(44)
        r45std = r45(pk.time())
        r46std = r46(pk.time())
        # determine the d13c value and assign it to the peaks info dict
        d13c = delta13c_santrock(r45sam, r46sam, d13cstd,
                                 r45std, r46std, ks, d18ostd)
        pk.info['p-d13c'] = d13c
