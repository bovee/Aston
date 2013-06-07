import re
import os.path as op
from collections import defaultdict
import numpy as np
from aston.peaks.Peak import Peak
from aston.peaks.PeakModels import gaussian
from aston.timeseries.TimeSeries import TimeSeries


def read_amdis_list(db, filename):
    get_val = lambda line, cols, key: line.split('\t')[cols.index(key)]
    CMP_LVL = 2  # number of directory levels to compare
    #TODO: does this work for agilent files only?
    mapping = defaultdict(list)
    with open(filename, 'r') as f:
        cols = f.readline().split('\t')
        for line in f:
            filename = get_val(line, cols, 'FileName')
            fn = op.splitext('/'.join(filename.split('\\')[-CMP_LVL:]))[0]
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
            ts = TimeSeries(np.array([np.nan]), np.array([np.nan]), [''])
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
                'p-s-d13c': 'd 13c/12c[per mil]vs. vpdb'}
    headers = None
    mapping = defaultdict(list)
    get_val = lambda line, cols, key: line.split(delim)[cols.index(key)]
    with open(filename, 'r') as f:
        for line in f:
            if bool(re.match('filename' + delim, line, re.I)) \
              or headers is None:
                headers = line.lower().split(',')
                continue
            fn = get_val(line, headers, 'filename')
            if ftype == 'amdis':
                # AMDIS has '.FIN' sufffixes and other stuff, so
                # munge Filename to get it into right format
                CMP_LVL = 2
                fn = op.splitext('/'.join(fn.split('\\')[-CMP_LVL:]))[0]
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
                    area = float(get_val(line, headers, \
                                         'rarea ' + ion + '[mvs]')) / 60.
                    #bgd = float(get_val(line, headers, \
                    #                       'bgd ' + ion + '[mv]'))
                    height = float(get_val(line, headers, \
                                           'ampl. ' + ion + '[mv]'))
                    # 0.8 is a empirical number to make things look better
                    data.append(gaussian(t, x=rt, w=0.5 * area / height, \
                                         h=height))
                ts = TimeSeries(np.array(data).T, t, [44, 45, 46])
            else:
                ts = TimeSeries(np.array([np.nan]), np.array([np.nan]), [''])
            mapping[dt] += [Peak(info, ts)]
    with db:
        for dt in mapping:
            dt.children += mapping[dt]
