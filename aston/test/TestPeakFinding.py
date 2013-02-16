import numpy as np
from aston.TimeSeries import TimeSeries
from aston.Math.PeakModels import gaussian


def generate_chromatogram(n=5, twin=None):
    if twin is None:
        twin = (0, 60)
    t = np.linspace(twin[0], twin[1], 300)
    peak_locs = twin[1] * np.random.random(n)
    peak_ws = 0.2 + 0.8 * np.random.random(n)
    peak_hs = 0.2 + 0.8 * np.random.random(n)

    y = np.zeros(len(t))
    for peak_loc, peak_w, peak_h in zip(peak_locs, peak_ws, peak_hs):
        y += gaussian(t, x=peak_loc, w=peak_w, h=peak_h)
    y += np.random.normal(scale=0.01, size=len(t))
    return TimeSeries(y, t, ['X'])
