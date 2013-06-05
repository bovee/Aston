import os.path as op
from collections import defaultdict
import numpy as np
from aston.peaks.Peak import Peak
#from aston.peaks.PeakModels import gaussian
from aston.timeseries.TimeSeries import TimeSeries


def read_amdis_list(db, filename):
    CMP_LVL = 2  # number of directory levels to compare
    #TODO: does this work for agilent files only?
    mapping = defaultdict(list)
    with open(filename, 'r') as f:
        cols = f.readline().split('\t')
        for line in f:
            filename = line.split('\t')[cols.index('FileName')]
            fn = op.splitext('/'.join(filename.split('\\')[-CMP_LVL:]))[0]
            # find if filtered filename overlaps with anything in the db
            for dt in db.children_of_type('file'):
                if fn in '/'.join(dt.rawdata.split(op.sep)):
                    break
            else:
                continue
            info = {}
            info['name'] = line.split('\t')[cols.index('Name')]
            info['p-s-time'] = line.split('\t')[cols.index('RT')]
            info['p-s-area'] = line.split('\t')[cols.index('Area')]
            ts = TimeSeries(np.array([np.nan]), np.array([np.nan]), [''])
            mapping[dt] += [Peak(info, ts)]
    with db:
        for dt in mapping:
            dt.children += mapping[dt]


def read_isodat_list(db, filename):
    with open(filename, 'r') as f:
        pass
