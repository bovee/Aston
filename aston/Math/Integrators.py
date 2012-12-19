import numpy as np
import scipy.ndimage as nd
import scipy.signal._peak_finding as spf
from scipy.optimize import leastsq, fmin
from aston.Features import Peak


def waveletIntegrate(dt, ion=None, plotter=None):
    #TODO: make this an integration option
    x = dt.trace(ion).y
    times = dt.trace(ion).times

    widths = np.linspace(1, 100, 200)
    cwtm = spf.cwt(x, spf.ricker, widths)
    ridges = spf._identify_ridge_lines(cwtm, widths / 4.0, 1)
    filt_ridges = spf._filter_ridge_lines(cwtm, ridges, min_snr=3)

    #peaks_w, peaks_t, peaks_amp = [], [], []
    p0 = [0, 0]
    for l in filt_ridges:
        pl = np.argmax([cwtm[x, y] for x, y in zip(l[0], l[1])])
        peak_amp = cwtm[l[0][pl], l[1][pl]]
        peak_w = widths[l[0][pl]] * 0.5 * (times[1] - times[0])
        peak_t = times[l[1][pl]]
        p0 += [peak_t, peak_amp, peak_w]

    def gauss(t, h, w):
        return h * np.exp(-t ** 2 / (2 * w ** 2))

    def sim_chr(p, times):
        c = p[0] + times * p[1]
        for i in range(int((len(p) - 2) / 3)):
            t, h, w = p[2 + 3 * i:5 + 3 * i]
            c += gauss(times - t, h, w)
        return c

    def errf(p, y, t):
        return sim_chr(p, t) - y

    p, r1, r2, r3, r4 = leastsq(errf, p0[:], args=(x, times), full_output=True, maxfev=10)
    print(r2['nfev'], r3, r4)
    plotter.plt.plot(times, x - sim_chr(p0, times), 'r-')
    plotter.plt.plot(times, x - sim_chr(p, times), 'k-')


    #import matplotlib.pyplot as plt
    #plt.imshow(cwtm, extent=(t[0], t[-1], widths[0], widths[-1]))
    #for l in filt_ridges:
    #    plt.plot(l[1], l[0])
    #plt.plot(peaks_t, peaks_w, 'k*')
    #plt.show()



def statSlopeIntegrate(dt, ion=None):
    t = dt.time()
    x = dt.trace(ion).data.T[0]
    pks = []

    dx = np.gradient(x)
    dx2 = np.gradient(dx)

    adx = np.average(dx)
    adx2 = np.average(dx2)
    l_i = -2

    #old loop checked for concavity too; prob. not necessary
    #for i in np.arange(len(t))[dx>adx+np.std(dx[abs(dx2)<adx2+np.std(dx2)])]:

    #loop through all of the points that have a slope
    #outside of one std. dev. from average
    for i in np.arange(len(t))[dx > adx + np.std(dx)]:
        if i - l_i == 1:
            l_i = i
            continue

        #track backwards to find where this peak started
        pt1 = ()
        for j in range(i - 1, 0, -1):
            if dx[j] < adx or dx2[j] < adx2:
                pt1 = (t[j], x[j])
                break

        #track forwards to find where it ends
        pt2 = ()
        neg = 0
        for j in range(i, len(t)):
            if dx[j] < adx:
                neg += 1
            if neg > 3 and dx[j] > adx:  # and x[j]<ax:
                pt2 = (t[j], x[j])
                break

        #create a peak and add it to the peak list
        if pt1 != () and pt2 != ():
            ts = dt.trace(ion, twin=(pt1[0], pt2[0]))
            info = {'p-type': 'Sample', 'p-created': 'integrator', \
                    'p-int': 'statslope'}
            info['name'] = '{:.2f}-{:.2f}'.format(pt1[0], pt2[0])
            info['traces'] = ion
            pk = Peak(dt.db, None, dt.db_id, info, ts)
            pks.append(pk)
        l_i = i
    return pks

def mergeIons(pks):
    for pk in pks:
        pass
