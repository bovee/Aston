# -*- coding: utf-8 -*-
import struct
import numpy as np
from aston import Datafile
from aston.TimeSeries import TimeSeries
from aston.FileFormats.Common import find_offset


class InficonHapsite(Datafile.Datafile):
    ext = 'HPS'
    mgc = '0403'

    def _cache_data(self):
        with open(self.rawdata, 'rb') as f:
            doff = find_offset(f, 4 * b'\xff' + 'HapsScan'.encode('ascii'))
            if doff is None:
                return
            f.seek(doff - 20)
            data_end = doff + struct.unpack('<I', f.read(4))[0] + 55

            f.seek(doff + 56)
            times, abns = [], []
            while f.tell() <= data_end:
                # record info looks like a standard format
                n, t, _, recs, _, _ = struct.unpack('<IiHHHH', f.read(16))
                times.append(t)
                # individual abundances for each ion
                abns.append(struct.unpack('<' + 'f' * recs, f.read(4 * recs)))

        times = np.array(times, dtype=float) / 60000
        nrecs, nmzs = len(abns), max(len(i) for i in abns)
        data = np.zeros((nrecs, nmzs))
        for i, r in enumerate(abns):
            data[i, 0:len(r)] = r
        self.data = TimeSeries(data, times, range(nmzs))
