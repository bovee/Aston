import numpy as np
import scipy.ndimage as nd
import scipy.signal._peak_finding as spf
from scipy.optimize import leastsq, fmin, minimize
from aston.Features import Peak
from aston.TimeSeries import TimeSeries
from aston.Math.Peak import time


def waveletIntegrate(ts, plotter=None, **kwargs):
    x = ts.y
    t = ts.time()

    widths = np.linspace(1, 100, 200)
    cwtm = spf.cwt(x, spf.ricker, widths)
    ridges = spf._identify_ridge_lines(cwtm, widths / 2.0, 2)
    filt_ridges = spf._filter_ridge_lines(cwtm, ridges, \
      min_length=cwtm.shape[0] / 8.0, min_snr=1)

    #import matplotlib.pyplot as plt
    #plt.imshow(cwtm)  # extent=(widths[0], widths[-1], times[0], times[-1]))
    #for l in ridges:
    #    plt.plot(l[1], l[0], 'k-')
    #for l in filt_ridges:
    #    plt.plot(l[1], l[0], 'r-')
    ##plt.plot(peaks_t, peaks_w, 'k*')
    #plt.show()

    # loop through the ridges and find the point of maximum
    # intensity on the ridge and save its characteristics
    peak = np.empty((len(filt_ridges), 3))
    for i, l in enumerate(filt_ridges):
        pl = np.argmax([cwtm[j, k] for j, k in zip(l[0], l[1])])
        peak_w = widths[l[0][pl]] * 0.5 * (t[1] - t[0])
        peak_amp = cwtm[l[0][pl], l[1][pl]] / (widths[l[0]][pl] ** 0.5)
        peak_t = t[l[1][pl]]
        peak[i] = np.array([peak_t, peak_amp, peak_w])

    gauss = lambda t, h, w: h * np.exp(-t ** 2 / (2 * w ** 2))
    peak_list = []
    for p in peak:
        twin = (p[0] - 4 * p[2], p[0] + 4 * p[2])
        pt = ts.trace('!', twin=twin).time()
        px = gauss(pt - p[0], p[1], p[2])
        pk_ts = TimeSeries(px, pt, ts.ions)
        info = {'name': '{:.2f}-{:.2f}'.format(*twin)}
        pk = Peak(None, None, None, info, pk_ts)
        peak_list.append(pk)

    return peak_list

    win_list = []
    for p in peak:
        p_w = (p[0] - 5 * p[2], p[0] + 5 * p[2])
        for w in win_list:
            if p_w[0] < w[0][1] and p_w[1] > w[0][0]:
                w[0] = (min(p_w[0], w[0][0]), \
                        max(p_w[1], w[0][1]))
                w[1].append(p)
                break
        else:
            win_list.append([p_w, [p]])

    def sim_chr(p, times):
        gauss = lambda t, h, w: h * np.exp(-t ** 2 / (2 * w ** 2))
        c = p[0] + times * p[1]
        for i in range(int((len(p) - 2) / 3)):
            t, h, w = p[2 + 3 * i:5 + 3 * i]
            c += gauss(times - t, h, w)
        return c

    errf = lambda p, y, t: sum(y - sim_chr(p, t))

    for w in win_list:
        tr = ts.trace(twin=w[0]).y
        p0 = np.insert(np.array(w[1]), 0, [tr.y[0], 0])
        #p, r1, r2, r3, r4 = leastsq(errf, p0[:], args=(tr.y, tr.times), full_output=True, maxfev=10)

        # crashes: TypeError
        #p = minimize(errf, p0[:], method='nelder-mead', args=(tr.y, tr.times), options={'disp':True})
        #print(p, dir(p))

        #TODO: decompose p into proper peaks

        plotter.plt.plot(tr.t, sim_chr(p0, tr.times), 'k-')

    #p, r1, r2, r3, r4 = leastsq(errf, p0[:], args=(x, times), full_output=True, maxfev=10)
    #print(r2['nfev'], r3, r4)
    #plotter.plt.plot(times, sim_chr(p, times), 'k-')


def statSlopeIntegrate(ts, **kwargs):
    x = ts.y
    t = ts.time()
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
            pk_ts = ts.trace('!', twin=(pt1[0], pt2[0]))
            info = {'name': '{:.2f}-{:.2f}'.format(pt1[0], pt2[0])}
            pk = Peak(None, None, None, info, pk_ts)
            pks.append(pk)
        l_i = i
    return pks


def merge_ions(pks):
    cleaned_pks = []
    for pk in pks:
        for c_pk in cleaned_pks:
            if np.abs(time(c_pk.as_poly()) - time(pk.as_poly())) < 0.01 \
              and c_pk.data.ions[0] != pk.data.ions[0]:
                c_pk.rawdata = c_pk.rawdata & pk.rawdata
                if 's-mzs' in c_pk.info:
                    del c_pk.info['s-mzs']
                break
        else:
            cleaned_pks.append(pk)
    return cleaned_pks
