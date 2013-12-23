import numpy as np
import struct
from pandas import Series
from aston.tracefile.AgilentCommon import AgilentCS


class AgilentFID(AgilentCS):
    # TODO: preliminary support, math is probably not correct
    """
    Reads a Agilent FID *.ch file.
    """
    ext = 'CH'
    mgc = '0238'

    @property
    def data(self):
        f = open(self.filename, 'rb')

        f.seek(0x11A)
        start_time = struct.unpack('>f', f.read(4))[0] / 60000.
        #end_time 0x11E '>i'

        #FIXME: why is there this del_ab code here?
        #f.seek(0x284)
        #del_ab = struct.unpack('>d', f.read(8))[0]
        data = []

        f.seek(0x400)
        delt = 0
        while True:
            try:
                inp = struct.unpack('>h', f.read(2))[0]
            except struct.error:
                break

            if inp == 32767:
                inp = struct.unpack('>i', f.read(4))[0]
                inp2 = struct.unpack('>H', f.read(2))[0]
                delt = 0
                data.append(inp * 65534 + inp2)
            else:
                delt += inp
                data.append(data[-1] + delt)
        f.close()
        # TODO: 0.4/60.0 should be obtained from the file???
        times = np.array(start_time + np.arange(len(data)) * (0.2 / 60.0))
        return Series(np.array([data]).T, times, name='TIC')
