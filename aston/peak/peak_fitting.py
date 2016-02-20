import numpy as np
from scipy.optimize import leastsq, fmin, fmin_l_bfgs_b

# bounding code inspired by http://newville.github.com/lmfit-py/bounds.html
# which was inspired by leastsqbound, which was inspired by MINUIT


def _to_bound_p(params, bounds):
    new_v = {}
    for p in params:
        if p not in bounds:
            new_v[p] = params[p]
            continue
        b = bounds[p]
        if b[1] == np.inf and b[0] == -np.inf:
            # already in the correct support: ignore
            new_v[p] = params[p]
        elif b[1] == np.inf:
            new_v[p] = b[0] - 1. + np.sqrt(params[p] ** 2 + 1.)
        elif b[0] == -np.inf:
            new_v[p] = b[1] + 1. - np.sqrt(params[p] ** 2 + 1.)
        else:
            new_v[p] = b[0] + 0.5 * np.sin(params[p] + 1.) * (b[1] - b[0])
    return new_v


def _to_unbnd_p(params, bounds):
    new_v = {}
    for p in params:
        if p not in bounds:
            new_v[p] = params[p]
            continue
        b = bounds[p]
        if (b[1] == np.inf and b[0] == -np.inf):
            # already in the correct support: ignore
            new_v[p] = params[p]
        elif b[1] == np.inf:
            new_v[p] = np.sqrt((params[p] - b[0] + 1.) ** 2 - 1.)
        elif b[0] == -np.inf:
            new_v[p] = np.sqrt((b[1] - params[p] + 1.) ** 2 - 1.)
        else:
            new_v[p] = np.arcsin(2 * (params[p] - b[0]) / (b[1] - b[0]) - 1)
    return new_v


def guess_initc(ts, f, rts=[]):
    """
    ts - An AstonSeries that's being fitted with peaks
    f - The functional form of the peaks (e.g. gaussian)
    rts - peak maxima to fit; each number corresponds to one peak
    """
    def find_side(y, loc=None):
        if loc is None:
            loc = y.argmax()
        ddy = np.diff(np.diff(y))
        lft_loc, rgt_loc = loc - 2, loc + 1
        while rgt_loc >= 0 and rgt_loc < len(ddy):
            if ddy[rgt_loc] < ddy[rgt_loc - 1]:
                break
            rgt_loc += 1
        while lft_loc >= 0 and lft_loc < len(ddy):
            if ddy[lft_loc] < ddy[lft_loc + 1]:
                break
            lft_loc -= 1
        return lft_loc + 1, rgt_loc + 1

    # weight_mom = lambda m, a, w: \
    #   np.sum(w * (a - np.sum(w * a) / np.sum(w)) ** m) / np.sum(w)
    # sig = np.sqrt(weight_mom(2, ts.index, ts.values))  # sigma
    # peak_params['s'] = weight_mom(3, ts.index, ts.values) / sig ** 3
    # peak_params['e'] = weight_mom(4, ts.index, ts.values) / sig ** 4 - 3
    # TODO: better method of calculation of these?
    all_params = []
    for rt in rts:
        peak_params = {'x': rt}  # ts.index[ts.values.argmax()]
        top_idx = np.abs(ts.index - rt).argmin()
        side_idx = find_side(ts.values, top_idx)
        peak_params['h'] = ts.values[top_idx]
        # - min(ts.y[side_idx[0]], ts.y[side_idx[1]])
        peak_params['w'] = ts.index[side_idx[1]] - ts.index[side_idx[0]]
        peak_params['s'] = 1.1
        peak_params['e'] = 1.
        peak_params['a'] = 1.
        all_params.append(peak_params)
    return all_params


def fit(ts, fs=[], all_params=[], fit_vars=None,
        alg='leastsq', make_bounded=True):
    """
    Use a minimization algorithm to fit a AstonSeries with
    analytical functions.
    """
    if fit_vars is None:
        fit_vars = [f._peakargs for f in fs]
    initc = [min(ts.values)]
    for f, peak_params, to_fit in zip(fs, all_params, fit_vars):
        if 'v' in to_fit:
            to_fit.remove('v')

        if make_bounded and hasattr(f, '_pbounds'):
            new_v = _to_unbnd_p({i: peak_params[i] for i in to_fit},
                                f._pbounds)
            initc += [new_v[i] for i in to_fit]
        else:
            initc += [peak_params[i] for i in to_fit]

    def errfunc_lsq(fit_params, t, y, all_params):
        # first value in fit_params is baseline
        # fit_y = np.ones(len(t)) * fit_params[0]
        fit_y = np.zeros(len(t))
        param_i = 1
        for f, peak_params, to_fit in zip(fs, all_params, fit_vars):
            for k in to_fit:
                peak_params[k] = fit_params[param_i]
                param_i += 1
            if make_bounded and hasattr(f, '_pbounds'):
                fit_y += f(t, **_to_bound_p(peak_params, f._pbounds))
            else:
                fit_y += f(t, **peak_params)
        return fit_y - y

    def errfunc(p, t, y, all_params):
        return np.sum(errfunc_lsq(p, t, y, all_params) ** 2)

    if alg == 'simplex':
        fit_p, _ = fmin(errfunc, initc, args=(ts.index, ts.values,
                                              peak_params))
#    elif alg == 'anneal':
#        fit_p, _ = anneal(errfunc, initc, args=(ts.index, ts.values,
#                                                peak_params))
    elif alg == 'lbfgsb':
        # TODO: use bounds param
        fitp, _ = fmin_l_bfgs_b(errfunc, fit_p,
                                args=(ts.index, ts.values, peak_params),
                                approx_grad=True)
    elif alg == 'leastsq':
        fit_p, _ = leastsq(errfunc_lsq, initc, args=(ts.index, ts.values,
                                                     all_params))
    # else:
    #     r = minimize(errfunc, initc, \
    #                  args=(ts.index, ts.values, all_params), \
    #                  jac=False, gtol=1e-2)
    #     #if not r['success']:
    #     #    print('Fail:' + str(f))
    #     #    print(r)
    #     #if np.nan in r['x']:  # not r['success']?
    #     #    fit_p = initc
    #     #else:
    #     #    fit_p = r['x']

    fit_pl = fit_p.tolist()
    v = fit_pl.pop(0)  # noqa
    fitted_params = []
    for f, to_fit in zip(fs, fit_vars):
        fit_p_dict = {v: fit_pl.pop(0) for v in to_fit}
        # fit_p_dict['v'] = v
        if make_bounded and hasattr(f, '_pbounds'):
            fitted_params.append(_to_bound_p(fit_p_dict, f._pbounds))
        else:
            fitted_params.append(fit_p_dict)

    # calculate r^2 of the fit
    ss_err = errfunc(fit_p, ts.index, ts.values, fitted_params)
    ss_tot = np.sum((ts.values - np.mean(ts.values)) ** 2)
    r2 = 1 - ss_err / ss_tot
    res = {'r^2': r2}

    return fitted_params, res
