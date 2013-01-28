import numpy as np
from scipy.optimize import leastsq, fmin, anneal, fmin_l_bfgs_b

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
            new_v[p] = np.arcsin(2 * (params[p] - b[0]) \
                                    / (b[1] - b[0]) - 1)
    return new_v


def fit_to(f, t, y, fit_vars=None, alg='leastsq', make_bounded=False):
    """
    Use a minimization algorithm to fit a TimeSeries with an
    analytical function.

    """
    #TODO: allow user to pass in initial guesses too?
    #TODO: better method of calculation of these?
    weight_mom = lambda m, a, w: \
            np.sum(w * (a - np.sum(w * a) / np.sum(w)) ** m) / np.sum(w)
    peak_params = {'v': min(y), 'h': max(y) - min(y)}
    sig = np.sqrt(weight_mom(2, t, y))  # sigma
    peak_params['x'] = t[y.argmax()]
    peak_params['w'] = sig ** 2
    peak_params['s'] = weight_mom(3, t, y) / sig ** 3
    peak_params['e'] = weight_mom(4, t, y) / sig ** 4 - 3
    peak_params['a'] = 1.

    if fit_vars is None:
        fit_vars = f._peakargs

    if make_bounded and hasattr(f, '_pbounds'):
        new_v = _to_unbnd_p({i: peak_params[i] for i in fit_vars}, f._pbounds)
        initc = [new_v[i] for i in fit_vars]
    else:
        initc = [peak_params[i] for i in fit_vars]

    def errfunc(p, t, y, peak_params):
        for k, v in zip(fit_vars, p):
            peak_params[k] = v
        if make_bounded and hasattr(f, '_pbounds'):
            return f(t, **_to_bound_p(peak_params, f._pbounds)) - y
        else:
            return f(t, **peak_params) - y

    def errfunc_1(p, t, y, peak_params):
        dif = errfunc(p, t, y, peak_params)
        return np.sum(dif ** 2)

    if alg == 'simplex':
        fit_p, _ = fmin(errfunc_1, initc, args=(t, y, peak_params))
    elif alg == 'anneal':
        fit_p, _ = anneal(errfunc_1, initc, args=(t, y, peak_params))
    elif alg == 'lbfgsb':
        #TODO: use bounds param
        fitp, _ = fmin_l_bfgs_b(errfunc_1, fit_p, args=(t, y, peak_params), \
                                approx_grad=True)
    elif alg == 'leastsq':
        fit_p, _ = leastsq(errfunc, initc, args=(t, y, peak_params))
    fit_p_dict = dict(zip(fit_vars, fit_p))

    if make_bounded and hasattr(f, '_pbounds'):
        fit_p_dict = _to_bound_p(fit_p_dict, f._pbounds)
    return fit_p_dict


def fit_multiple(f, t, y):
    pass
