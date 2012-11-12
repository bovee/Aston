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
        fdat = open(op.splitext(self.rawdata)[0] + '.DAT', 'rb')
        tme, tic = [], []
        while True:
            try:
                d = struct.unpack('<IIffhhh', fidx.read(22))
            except struct.error:
                break
            tme.append(d[3])
            tic.append(d[2])
        fdat.close()
        fidx.close()
        return TimeSeries(np.array(tic), np.array(tme), ['TIC'])

    def _update_info_from_file(self):
        pass
