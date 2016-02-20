# -*- coding: utf-8 -*-
"""
Functions which model peaks and decorator to allow those functions
to be translated and scaled and have the bounds of their parameters
respected.

Unless otherwise noted, the formulation of how each function is
written is taken from DiMarco & Bombi 2001 J Chrom A

Example:
    t = np.linspace(-10,10,200)
    peak = gaussian(t, x=2, w=2)
    fitted_peak = lorentzian(t, **fit_to(lorentzian, t, l))
    plt.plot(t, peak, 'k-', t, fitted_peak, 'r-')
    plt.show()
"""
import inspect
from functools import wraps
import numpy as np
from numpy import exp, sqrt, abs, log
from scipy.special import erfc, i1, gamma


# These functions allow us to use commonsense notation
# in labelling parameter bounds. The sqrt is to allow
# the bounded parameter to be multiplied without fear of it
# rounding outside the bounds.
def openhi(i):
    return np.nextafter(i, -1)


def openlow(i):
    return i + np.sqrt(np.nextafter(i, 1) - i)


def bounds(**kwargs):
    """
    Using this function as a decorator allow us to label which
    parameters of a function shouldn't have their values allowed
    to fall outside of a specific range.
    """
    def wrap(f):
        f._pbounds = kwargs
        return f
    return wrap


def peak_model(f):
    """
    Given a function that models a peak, add scale and location arguments to

    For all functions, v is vertical offset, h is height
    x is horizontal offset (1st moment), w is width (2nd moment),
    s is skewness (3rd moment), e is excess (4th moment)
    """
    @wraps(f)
    def wrapped_f(t, **kw):
        # load kwargs with default values
        # do this here instead of in the def because we want to parse
        # all of kwargs later to copy values to pass into f
        def_vals = {'v': 0.0, 'h': 1.0, 'x': 0.0, 'w': 1.0, 's': 1.1, 'e': 1.0}
        for v in def_vals:
            if v not in kw:
                kw[v] = def_vals[v]

        # this copies all of the defaults into what the peak function needs
        anames, _, _, _ = inspect.getargspec(f)
        fkw = dict([(arg, kw[arg]) for arg in anames if arg in kw])

        # some functions use location or width parameters explicitly
        # if not, adjust the timeseries accordingly
        ta = t
        if 'x' not in anames:
            ta = ta - kw['x']
        if 'w' not in anames:
            ta = ta / kw['w']

        # finally call the function
        mod = f(ta, **fkw)
        # recalcualte, making the peak maximize at x
        mod = f(ta + ta[mod.argmax()], **fkw)
        return kw['v'] + kw['h'] / max(mod) * mod

    args = set(['v', 'h', 'x', 'w'])
    anames, _, _, _ = inspect.getargspec(f)
    wrapped_f._peakargs = list(args.union([a for a in anames
                                           if a not in ('t', 'r')]))
    return wrapped_f


@peak_model
def bigaussian(t, w, s):
    # for an example of use: http://www.biomedcentral.com/1471-2105/11/559
    # Di Marco & Bombi use formulation with w1 & w2, but it
    # looks better to use formulation with w and s
    w1, w2 = w * exp(-s) / (1 + exp(-s)), w / (1 + exp(-s))
    y = np.empty(len(t))
    y[t < 0] = exp(-t[t < 0] ** 2 / (2 * w1 ** 2)) / sqrt(2 * np.pi)
    y[t >= 0] = exp(-t[t >= 0] ** 2 / (2 * w2 ** 2)) / sqrt(2 * np.pi)
    return y


@peak_model
def box(t):
    y = np.zeros(len(t))
    y[np.logical_and(t > -0.5, t < 0.5)] = 1.0
    return y


@bounds(w=(openlow(0.), np.inf), s=(1., np.inf))
@peak_model
def exp_mod_gaussian(t, w, s):
    # http://en.wikipedia.org/wiki/Exponentially_modified_Gaussian_distribution
    exp_t = exp((w ** 2 - 2 * s * t) / (2 * s ** 2))
    erf_t = erfc((w ** 2 - s * t) / (s * w))
    return (w ** 1.5) / (1.414214 * s) * exp_t * erf_t


@peak_model
def extreme_value(t):
    return exp(-exp(-t) - t + 1)


@bounds(w=(openlow(0.), np.inf), s=(1., np.inf))
@peak_model
def gamma_dist(t, w, s):
    # from Wikipedia: not the same as Di Marco & Bombi's formulation
    # s > 1
    y = np.zeros(len(t))
    y[t > 0] = t[t > 0] ** (s - 1) * exp(-t[t > 0] / w) / (w ** s * gamma(s))
    return y


@peak_model
def gaussian(t):
    """
    Gaussian
    """
    return exp(-0.5 * t ** 2)


@bounds(w=(openlow(0.), np.inf), x=(openlow(0.), np.inf))
@peak_model
def giddings(t, w, x):
    print(w, x)
    # w != 0
    y = np.zeros(len(t))
    y[t > 0] = (1. / w) * sqrt(x / t[t > 0]) * exp((t[t > 0] + x) / -w)
    # TODO: "overflow encountered in i1"
    # y[t > 0] *= i1(2. * sqrt(x * t[t > 0]) / w)
    # trying to keep the shape, but not allow such high numbers?
    y[t > 0] *= i1(np.linspace(2, 10, sum(t > 0)))
    return y


@bounds(w=(openlow(0.1), np.inf), s=(openlow(0.), np.inf))
@peak_model
def haarhoffvanderlinde(t, w, s):
    # s here = s * z in Di Marco & Bombi
    # w, s != 0
    y = w * exp(-0.5 * (t / w) ** 2) / (s * sqrt(2 * np.pi))
    print(s, w)
    y /= 1. / (exp(s / w ** 2) - 1.) + 0.5 * erfc(t / (w * sqrt(2)))
    return y


@bounds(w=(openlow(0.), np.inf), s=(openlow(1.), np.inf))
@peak_model
def lognormal(t, w, s, r=2.):
    # r is the ratio between h and the height at
    # which s is computed: normally 2.
    y = np.zeros(len(t))
    # TODO: if log(s) rounds to 0, big problems here
    lt = -log(r) / log(s) ** 2
    # try to adjust timing so peak stays centered at 0
    ta = t + (w - 1) / (1.12383 * s - 0.780647)
    y[ta > 0] = exp(lt * log(ta[ta > 0] / w * (s ** 2 - 1) / s) ** 2)
    return y


@peak_model
def lorentzian(t, a):
    # from Wikipedia: not the same as Di Marco & Bombi's formulation
    # return 1. / (1. + 4. * t ** 2)
    return a / (np.pi * (a ** 2 + t ** 2))


@peak_model
def papai_pap(t, s, e):
    # s is skewness, e is excess
    y = np.zeros(len(t))
    ft = t[t > 0]
    y[t > 0] = 1 + (s / 6.) * (ft ** 2 - 3. * ft)
    y[t > 0] -= (e / 24.) * (ft ** 4 - 6 * ft ** 2 + 3)
    y[t > 0] *= exp(-0.5 * ft)
    return y


@peak_model
def parabola(t):
    y = np.zeros(len(t))
    mask = np.logical_and(t > -1, t < 1)
    y[mask] = 1 - t[mask] ** 2
    return y


@bounds(a=(openlow(0.), np.inf))
@peak_model
def pearson_vii(t, a):
    return (1 + 4 * t ** 2 * (2 ** (1 / a) - 1)) ** -a


@peak_model
def poisson(t, a):
    # a > 1
    y = np.zeros(len(t))
    y[t > 0] = exp((1 - a) * (t[t > 0] - log(t[t > 0]) - 1))
    return y


@bounds(s=(openlow(0.), np.inf))
@peak_model
def studentt(t, s):
    # s != 0
    return (1 + (t ** 2) / s) ** (-0.5 * (s + 1))


@peak_model
def triangle(t):
    y = np.zeros(len(t))
    mask = np.logical_and(t > -0.5, t < 0.5)
    y[mask] = 1 - abs(t[mask]) / 0.5
    return y


@bounds(a=(openlow(1.), np.inf))
@peak_model
def weibull3(t, a):
    # TODO: doesn't work?
    y = np.zeros(len(t))
    at = (a - 1.) / a
    tt = t[t > 0] + ((a - 1.) / a) ** (1. / a)
    y[t > 0] = at ** at * tt ** (a - 1.) * exp(-tt ** a + at)
    return y

#  FUNCTIONS TO DO
# def chesler_cram_a(t, a, b, c, d):
# def chesler_cram_b(t, a, b, c, d, e):
# def cumulative(t, w, a):
# def f_variance(t, s1, s2):
# def gladney_dowden_a(t, w, s):
# def gladney_dowden_b(t, w, a, b):
# def haldna_phi(t, w, s):
# def intermediate(t, a, b):
# def li_a(t, w):
# def li_b(t, w, a1, a2, b1, b2):
# def losev(t, w1, w2, a):
# def nonlinearchromatography(t, x, w, s):
#     # also r & v?
# def pearsonIV(t, w, s1, s2):
# def pearsonIVa(t, w, s):
# def pearsonIVb(t, w, s):
# def pseudovoight1(t, a):
# def pseudovoight2(t, s, a):
# def pulse(t, a):
#
#
# def gram_charlier(t, w, *n):
#     # TODO: implement this; Berberan-Santos '07 has
#     # ways to calculate cumulant values
#     raise NotImplementedError
#
#
# def edgeworth_cramer(t, *n):
#     # y = exp(-0.5 * t ** 2)
#     raise NotImplementedError


peak_models = [bigaussian, box, exp_mod_gaussian, extreme_value, gamma_dist,
               gaussian, giddings, haarhoffvanderlinde, lognormal, lorentzian,
               papai_pap, parabola, pearson_vii, poisson, studentt, triangle,
               weibull3]
