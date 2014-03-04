import itertools
import numpy as np
import matplotlib.pyplot as plt
from aston.features.Datafile import Datafile
from aston.peaks.PeakFinding import simple_peak_find, find_peaks
from aston.peaks.Integrators import drop_integrate, constant_bl_integrate, integrate_peaks

known_times = np.array([18.14, 21.06, 24.20, 27.45, 30.72, 33.88,
                        37.03, 40.10, 42.99, 45.42, 47.45, 49.30,
                        50.97, 52.45, 53.74, 55.98])
known_d13cs = np.array([-30.66, -31.16, -31.10, -33.17, -32.35, -29.10,
                        -32.87, -31.77, -33.34, -28.48, -33.03, -29.56,
                        -32.21, -30.07, -29.86, -29.47])


def dd_from_slope(st_slope, en_slope):
    dt = Datafile('./data/b3_alkanes.dxf')
    tss = dt.active_traces(all_tr=True)
    pf_opts = {'init_slope': 500, 'start_slope': 100, 'end_slope': 100, \
            'min_peak_height': 50, 'max_peak_width': 1.5}

    pf_opts['start_slope'] = st_slope
    pf_opts['end_slope'] = en_slope
    pts = find_peaks_iso(tss, simple_peak_find, pf_opts, mp=False)
    pks = integrate_peaks(tss, pts, drop_integrate, \
                          {}, isomode=True, mp=False)
    dt.children += pks

    for pk in pks:
        if pk.area(44) > 1000:
            pk.info['p-type'] = 'Isotope Standard'

    #import IPython; IPython.embed()

    tot_off = []
    for pk in pks:
        tdiff = known_times - float(pk.info['p-s-time'])
        if np.abs(tdiff).min() < 0.1:
            known_dv = known_d13cs[np.abs(tdiff).argmin()]
            tot_off.append(float(pk.d13C()) - known_dv)

    dt.children = []
    return np.average(tot_off), np.std(tot_off), len(tot_off)

nx, ny = 100, 100
st_slopes = np.linspace(1, 250, nx)
en_slopes = np.linspace(1, 250, ny)
slopes = np.meshgrid(st_slopes, en_slopes)
dd_off = np.empty(slopes[0].shape)
dd_std = np.empty(slopes[0].shape)
n_pks = np.empty(slopes[0].shape)

for x, y in itertools.product(range(nx), range(ny)):
    print(nx * x + y)
    off, std, n = dd_from_slope(st_slopes[x], en_slopes[y])
    dd_off[y, x] = off
    dd_std[y, x] = std
    n_pks[y, x] = n

plt.pcolor(slopes[0], slopes[1], dd_off, cmap='Spectral', vmin=4, vmax=5) #vmin=0.5, vmax=1
plt.colorbar(extend="both")
std_ctrs = plt.contour(slopes[0], slopes[1], dd_std, cmap='binary', levels=[3,4,5,6]) #levels=[0.2,0.4,0.6,0.8]
plt.clabel(std_ctrs)
plt.xlabel('Starting Slope (V/min)')
plt.ylabel('Ending Slope (V/min)')
plt.show()
