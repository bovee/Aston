import os.path as op
from aston.peaks.Peak import Peak
#from aston.peaks.PeakModels import gaussian
from aston.timeseries.TimeSeries import TimeSeries


def read_amdis_list(db, filename):
    CMP_LVL = 2
    #works for agilent files?
    with open(filename, 'r') as f:
        cols = f.readline().split('\t')
        for line in f:
            filename = line.split('\t')[cols.index('FileName')]
            fn = op.splitext('/'.join(filename.split('\\')[-CMP_LVL:]))[0]
            for dt in db.children_of_type('file'):
                if fn in '/'.join(dt.split(op.sep)):
                    break
            else:
                continue
            info = {}
            info['name'] = line.split('\t')[cols.index('Name')]
            info['p-s-time'] = line.split('\t')[cols.index('RT')]
            info['p-s-area'] = line.split('\t')[cols.index('Area')]
            ts = TimeSeries()
            dt.children += Peak(info, ts)


def read_isodat_list(db, filename):
    pass
