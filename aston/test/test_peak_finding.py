import numpy as np
from aston.trace import Trace
from aston.peak.peak_models import gaussian
from aston.peak.peak_finding import (simple_peak_find, wavelet_peak_find,
                                     stat_slope_peak_find, event_peak_find)


def generate_chromatogram(n=5, twin=None):
    """
    Generates a trace with n gaussian peaks distributed through it.
    """
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
    return Trace(y, t, ['X'])


def generate_gaussian():
    t = np.linspace(0, 60, 300)
    y = gaussian(t, x=30, w=2, h=1)
    return Trace(y, t, ['X'])


def test_simple_peak_find():
    trace = generate_gaussian()
    peaks = simple_peak_find(trace, init_slope=0.2, start_slope=0.2,
                             end_slope=0.2, min_peak_height=0.01)
    # TODO: better asserts
    assert len(peaks) > 0


def test_wavelet_peak_find():
    trace = generate_gaussian()
    peaks = wavelet_peak_find(trace)

    assert len(peaks) == 1
    peak = peaks[0]
    assert peak['h'] > 0.5 and peak['h'] < 1
    assert peak['t0'] < 30
    assert peak['t1'] > 30
    assert peak['x'] > 29.8 and peak['x'] < 30.2


def test_stat_slope_peak_find():
    trace = generate_gaussian()
    peaks = stat_slope_peak_find(trace)
    # FIXME & fix stat_slope?
    assert type(peaks) is list


def test_event_peak_find():
    trace = generate_gaussian()
    events = [{'t0': 25, 't1': 35}]

    # check passthrough
    peaks = event_peak_find(trace, events, adjust_times=False)
    assert peaks == events

    # check adjusted
    peaks = event_peak_find(trace, events, adjust_times=True)
    assert len(peaks) == 1
    assert peaks[0]['t0'] > 20 and peaks[0]['t0'] < 30
    assert peaks[0]['t1'] > 30 and peaks[0]['t1'] < 40
