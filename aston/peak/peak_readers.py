import re
import os.path as op
from collections import defaultdict
import numpy as np
from scipy.optimize import leastsq
from aston.peak import Peak
from aston.peak.peak_models import gaussian
from aston.trace import Chromatogram


def read_amdis_list(db, filename):

    def get_val(line, cols, key):
        return line.split('\t')[cols.index(key)]

    cmp_lvl = 2  # number of directory levels to compare
    # TODO: does this work for agilent files only?
    mapping = defaultdict(list)
    with open(filename, 'r') as f:
        cols = f.readline().split('\t')
        for line in f:
            filename = get_val(line, cols, 'FileName')
            fn = op.splitext('/'.join(filename.split('\\')[-cmp_lvl:]))[0]
            # find if filtered filename overlaps with anything in the db
            for dt in db.children_of_type('file'):
                if fn in '/'.join(dt.rawdata.split(op.sep)):
                    break
            else:
                continue
            info = {}
            info['name'] = get_val(line, cols, 'Name')
            info['p-s-time'] = get_val(line, cols, 'RT')
            info['p-s-area'] = get_val(line, cols, 'Area')
            ts = Chromatogram(np.array([np.nan]), np.array([np.nan]), [''])
            mapping[dt] += [Peak(info, ts)]
    with db:
        for dt in mapping:
            dt.children += mapping[dt]


def read_peaks(db, filename, ftype='isodat'):
    if ftype is None:
        with open(filename, 'r') as f:
            header = f.readline()
            if 'd 13C/12C[per mil]vs. VPDB' in header:
                ftype = 'isodat'
            else:
                ftype = 'amdis'
    if ftype == 'amdis':
        delim = '\t'
        cvtr = {'name': 'name',
                'p-s-time': 'rt',
                'p-s-area': 'area'}
    elif ftype == 'isodat':
        delim = ','
        cvtr = {'name': 'peak nr.',
                'p-s-time': 'rt[s]',
                'p-s-area': 'area all[vs]',
                'p-s-width': 'width[s]',
                'p-s-d13c': 'd 13c/12c[per mil]vs. vpdb',
                'p-s-d18o': 'd 18o/16o[per mil]vs. vsmow'}
    headers = None
    mapping = defaultdict(list)
    ref_pk_info = {}

    def get_val(line, cols, key):
        return line.split(delim)[cols.index(key)]

    with open(filename, 'r') as f:
        for line in f:
            if bool(re.match('filename' + delim,
                             line, re.I)) or headers is None:
                headers = line.lower().split(',')
                continue
            fn = get_val(line, headers, 'filename')
            if ftype == 'amdis':
                # AMDIS has '.FIN' sufffixes and other stuff, so
                # munge Filename to get it into right format
                cmp_lvl = 2
                fn = op.splitext('/'.join(fn.split('\\')[-cmp_lvl:]))[0]
            # find if filtered filename overlaps with anything in the db
            for dt in db.children_of_type('file'):
                if fn in '/'.join(dt.rawdata.split(op.sep)):
                    break
            else:
                continue
            info = {}
            # load all the predefined fields
            for k in cvtr:
                info[k] = get_val(line, headers, cvtr[k])

            # create peak shapes for plotting
            if ftype == 'isodat':
                rt = float(info['p-s-time']) / 60.
                width = float(info['p-s-width']) / 60.
                t = np.linspace(rt - width, rt + width)
                data = []
                for ion in ['44', '45', '46']:
                    area = float(get_val(line, headers,
                                         'rarea ' + ion + '[mvs]')) / 60.
                    # bgd = float(get_val(line, headers, \
                    #                       'bgd ' + ion + '[mv]'))
                    height = float(get_val(line, headers,
                                           'ampl. ' + ion + '[mv]'))
                    # save the height at 44 into the info for linearity
                    if ion == '44':
                        info['p-s-ampl44'] = height
                    # 0.8 is a empirical number to make things look better
                    data.append(gaussian(t, x=rt, w=0.5 * area / height,
                                         h=height))
                # save info if this is the main ref gas peak
                if info['name'].endswith('*'):
                    ref_pk_info[dt] = info
                ts = Chromatogram(np.array(data).T, t, [44, 45, 46])
            else:
                ts = Chromatogram(np.array([np.nan]), np.array([np.nan]), [''])
            mapping[dt] += [Peak(info, ts)]
    # do drift correction
    if ftype == 'isodat':
        for dt in mapping:
            ref_pks = []
            hgt44 = ref_pk_info[dt]['p-s-ampl44']
            d18o = float(ref_pk_info[dt]['p-s-d18o'])
            d13c = float(ref_pk_info[dt]['p-s-d13c'])
            for pk in mapping[dt]:
                # if the d18o and height are similar, it's a ref peak
                if abs(pk.info['p-s-ampl44'] - hgt44) < 10. and \
                   abs(float(pk.info['p-s-d18o']) - d18o) < 2.:
                    ref_pks.append(pk)

            # get out the dd13C values and times for the ref gas peaks
            d13cs = [float(pk.info['p-s-d13c']) for pk in ref_pks]
            dd13cs = np.array(d13cs) - d13c
            rts = [float(pk.info['p-s-time']) for pk in ref_pks]

            # try to fit a linear model through all of them
            p0 = [d13cs[0], 0]

            def errfunc(p, x, y):
                return p[0] + p[1] * x - y

            try:
                p, succ = leastsq(errfunc, p0, args=(np.array(rts), dd13cs))
            except Exception:
                p = p0
            # apply the linear model to get the dd13C linearity correction
            # for a given time and add it to the value of this peak
            for pk in mapping[dt]:
                pk.info['p-s-d13c'] = str(-errfunc(p,
                                                   float(pk.info['p-s-time']),
                                                   float(pk.info['p-s-d13c'])))

    # save everything
    with db:
        for dt in mapping:
            dt.children += mapping[dt]
