import numpy as np


def area(data):
    csum = 0
    x, y = data[-1, :]
    for i in data:
        csum += i[0] * y - i[1] * x
        x, y = i
    return abs(csum / 2.)


def length(data, pwhm=False):
    if pwhm:
        #TODO: better way to pick these points
        pt1, pt2 = data[0], data[-1]

        m = (pt2[1] - pt1[1]) / (pt2[0] - pt1[0])
        avs = np.array([(pt[0], \
          (pt[1] - m * (pt[0] - pt1[0]) - pt1[1])) for pt in data])

        #calculate the height of half-max
        half_y = max(avs[:, 1]) / 2.0
        lw_x, hi_x = float('nan'), float('nan')
        #loop through all of the line segments
        for i in range(len(avs) - 1):
            #does this line segment intersect half-max?
            if (avs[i, 1] < half_y and avs[i + 1, 1] > half_y) or \
              (avs[i, 1] > half_y and avs[i + 1, 1] < half_y):
                m = (avs[i + 1, 1] - avs[i, 1]) \
                  / (avs[i + 1, 0] - avs[i, 0])
                b = (avs[i + 1, 0] * avs[i, 1] - \
                  avs[i, 0] * avs[i + 1, 1]) / \
                  (avs[i + 1, 0] - avs[i, 0])
                if np.isnan(lw_x) and np.isnan(hi_x):
                    lw_x, hi_x = (half_y - b) / m, (half_y - b) / m
                else:
                    lw_x, hi_x = min((half_y - b) / m, lw_x), \
                      max((half_y - b) / m, hi_x)
        return hi_x - lw_x
    else:
        data = np.array(data)
        return data[:, 0].max() - data[:, 0].min()


def height(data):
    data = np.array(data)
    return data[:, 1].max() - data[:, 1].min()


def time(data):
    if data[1, 0] < data[:, 0].max():
        return data[data[:, 1].argmax(), 0]
    else:  # inverted peak
        return data[data[:, 1].argmin(), 0]


def contains(data, x, y):
    #from: http://www.ariel.com.au/a/python-point-int-poly.html
    n = len(data)
    inside = False

    p1x, p1y = data[0]
    for i in range(n + 1):
        p2x, p2y = data[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) \
                          / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside

### PEAK MODELS ###


def gaussian(p, t):
    s = p[0]
    return 1.0 / (s * 2.506628) * np.exp(-0.5 * (t / s) ** 2)


def lorentzian(p, t):
    g = p[0]
    return 0.31831 * g / (t ** 2 + g ** 2)


def lognormal(p, t):
    s = p[0]
    #return 1.0/(t*2.506628)*np.exp(-0.5*(np.log(t)/s)**2)
    return np.array([1.0 / (i * 2.506628) * np.exp(-0.5 * \
      (np.log(i) / s) ** 2) if i > 0 else 0 for i in t])


def exp_mod_gaussian(p, t):
    #http://en.wikipedia.org/wiki/Exponentially_modified_Gaussian_distribution

    #FIXME: this
    #/home/roderick/Documents/2012/Aston/aston/Math/Peak.py:105: RuntimeWarning: invalid value encountered in double_scalars
    #  return (w ** 1.5) / (1.414214 * s) * exp_t * erf_t
    #/usr/lib/python2.7/site-packages/scipy/optimize/minpack.py:393: RuntimeWarning: Number of calls to function has reached maxfev = 1000.
    #  warnings.warn(errors[info][0], RuntimeWarning)
    #
    from scipy.special import erfc
    w = p[0]
    s = p[1]

    exp_t = np.exp((w ** 2 - 2 * s * t) / (2 * s ** 2))
    erf_t = erfc((w ** 2 - s * t) / (s * w))
    return (w ** 1.5) / (1.414214 * s) * exp_t * erf_t


def voigt(p, t):
    #http://en.wikipedia.org/wiki/Voigt_profile
    pass


def gamma(p, t):
    from scipy.special import gamma
    l = p[0]
    return  l ** t * np.exp(-l) / gamma(t + 1)


def pearsonVII(p, t):
    pass


def poisson(p, t):
    pass


def gram_charlier(p, t):
    pass


def edgeworth_cramer(p, t):
    pass


def giddings(p, t):
    pass


def HVL(p, t):
    pass


def weibull(p, t):
    pass


def fit_to(f, t, y):
    from scipy.optimize import leastsq

    if f is gaussian or f is lorentzian:
        guess_p = [(t[0] + t[-1]) / 2, max(y) - min(y), \
          0.5 * (t[-1] - t[0])]
    elif f is lognormal:
        guess_p = [t[0], max(y) - min(y), 10 * (t[-1] - t[0])]
    elif f is exp_mod_gaussian:
        guess_p = [(t[0] + t[-1]) / 2, max(y) - min(y), \
          0.5 * (t[-1] - t[0]), 0.2]

    errfunc = lambda p, x, y: p[1] * f(p[2:], x - p[0]) - y
    fit_p, _ = leastsq(errfunc, guess_p[:], args=(t, y))
    return fit_p


def bigaussian(p, t):
    s1 = p[0]
    s2 = p[1]
    #http://www.biomedcentral.com/1471-2105/11/559
    stp = np.sqrt(2 * np.pi)  # square root of two pi
    if t < 0:
        return np.exp(-t ** 2 / (2 * s1 ** 2)) / stp
    else:
        return np.exp(-t ** 2 / (2 * s2 ** 2)) / stp
