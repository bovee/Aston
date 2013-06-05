import struct
import os.path as op
import numpy as np
from aston.features import Datafile
from aston.timeseries.TimeSeries import TimeSeries

class WatersAutospec(Datafile.Datafile):
    """
    Reads *.IDX and *.DAT files from a Waters Autospec.
    Will need to be extended to other Waters files?
    """

    ext = 'IDX'
    mgc = None

    #def _total_trace(self, twin=None):
    #    fidx = open(self.rawdata, 'rb')
    #    tme, tic = [], []
    #    while True:
    #        try:
    #            d = struct.unpack('<IHHffhhh', fidx.read(22))
    #            # I: offset in *.DAT file of data chunk
    #            # H: number of data points in data chunk (bytes / 4)
    #            # H:
    #            # f: TIC of data point
    #            # f: time of data point
    #            # h:
    #            # h: 10, 20, 21, 30, 31, 40, or 41?
    #            # h: 80, A0, C0, E0
    #        except struct.error:
    #            break
    #        tme.append(d[4])
    #        tic.append(d[3])
    #    fidx.close()
    #    return TimeSeries(np.array(tic), np.array(tme), ['TIC']).trace(twin=twin)

    def _cache_data(self):
        fidx = open(self.rawdata, 'rb')
        fdat = open(op.splitext(self.rawdata)[0] + '.DAT', 'rb')

        ions = set([])
        while True:
            fdat.seek(fdat.tell() + 2)
            try:
                i = struct.unpack('<H', fdat.read(2))[0]
            except struct.error:
                break
            ions.add(i)
        ions = sorted(ions)

        data = []
        tme = []
        while True:
            try:
                idx = struct.unpack('<IHHffhhh', fidx.read(22))
                tme.append(idx[4])
                fdat.seek(idx[0])
                new_line = np.zeros(len(ions))
                d = struct.unpack('<' + int(idx[1] / 4) * 'HH', \
                fdat.read(idx[1]))
                for i, v in zip(d[1::2], d[0::2]):
                    new_line[ions.index(i)] = v
                data.append(new_line)
            except struct.error:
                break
        fdat.close()
        fidx.close()
        self.data = TimeSeries(np.array(data), np.array(tme), ions)

    def _update_info_from_file(self):
        pass
