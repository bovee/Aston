import numpy as np
from scipy.optimize import leastsq
from aston.trace.Trace import AstonSeries
from aston.spectra.Isotopes import delta13C_Santrock


def calc_ratio_trace(pks, r2=45, r1=44, t=None):
    # pull out the time and ratio information
    isopks = [pk for pk in pks if pk.info.get('p-type') == 'isostd']
    x = [pk.time() for pk in isopks if pk.area(mz=r2) > 0]
    y = [pk.area(mz=r1) / pk.area(mz=r2) for pk in pks if pk.area(mz=r2) > 0]

    # initial condition for fitting
    p0 = [y[0], 0]

    # function to fit
    errfunc = lambda p, x, y: p[0] + p[1] * x - y

    # try fitting; if it doesn't work, just use first ratio peak
    try:
        p, succ = leastsq(errfunc, p0, args=(np.array(x), np.array(y)))
    except:
        p = p0

    # construct a AstonSeries from the fitted data
    if t is None:
        t = np.array(x)
    sim_y = np.array(errfunc(p, t, np.zeros(len(t))))
    return AstonSeries(sim_y, t, \
                       name='{:.1f}/{:.1f}'.format(r2, r1))


def calc_carbon_isotopes(pks, d13cstd, ks='Craig', d18ostd=23.5):
    # get the standard ratio traces
    r45 = calc_ratio_trace(pks, r2=45, r1=44)
    r46 = calc_ratio_trace(pks, r2=46, r1=44)
    for pk in pks:
        # determine the peak areas for our peak and an interpolated standard
        r45sam, r46sam = pk.area(45) / pk.area(44), pk.area(46) / pk.area(44)

        #TODO: need to feed a more complete time series in here
        # or this will just return the nearest standard, not an
        # interpolated one
        r45std = r45.get_point(pk.time())
        r46std = r46.get_point(pk.time())

        d13c = delta13C_Santrock(r45sam, r46sam, d13cstd, \
                                 r45std, r46std, ks, d18ostd)
        pk.info['p-d13c'] = d13c
