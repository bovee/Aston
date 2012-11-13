import struct
import os.path as op
import numpy as np
from aston import Datafile
from aston.TimeSeries import TimeSeries

class WatersAutospec(Datafile.Datafile):
    """
    Reads *.IDX and *.DAT files from a Waters Autospec.
    """

    ext = 'IDX'
    mgc = None

    def __init__(self, *args, **kwargs):
        super(WatersAutospec, self).__init__(*args, **kwargs)

    def _total_trace(self, twin=None):
        fidx = open(self.rawdata, 'rb')
        tme, tic = [], []
        while True:
            try:
                d = struct.unpack('<IIffhhh', fidx.read(22))
                # I: offset in *.DAT file of data chunk
                # I: number of data points in data chunk (bytes / 4)
                # f: TIC of data point
                # f: time of data point
                # h:
                # h: 10, 20, 21, 30, 31, 40, or 41?
                # h: 80, A0, C0, E0
            except struct.error:
                break
            tme.append(d[3])
            tic.append(d[2])
        fidx.close()
        return TimeSeries(np.array(tic), np.array(tme), ['TIC'])

    def _cache_data(self):
        fidx = open(self.rawdata, 'rb')
        fdat = open(op.splitext(self.rawdata)[0] + '.DAT', 'rb')
        pass
        fdat.close()
        fidx.close()
        self.data = TimeSeries()

    def _update_info_from_file(self):
        pass
