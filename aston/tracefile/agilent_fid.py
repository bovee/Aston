import numpy as np
import struct
from aston.trace import Trace
from aston.tracefile import TraceFile


class AgilentFID(TraceFile):
    # TODO: preliminary support, math may not be correct
    """
    Reads a Agilent FID *.ch file.
    """
    mime = 'application/vnd-agilent-chemstation-fid'
    traces = ['fid']

    def _trace(self, name, twin):
        # this method allows self.trace('fid') to get something
        return self.total_trace(twin)

    def total_trace(self, twin=None):
        f = open(self.filename, 'rb')

        f.seek(0x11A)
        start_time = struct.unpack('>f', f.read(4))[0] / 60000.
        # end_time = struct.unpack('>f', f.read(4))[0] / 60000.
        # end_time 0x11E '>i'

        # FIXME: why is there this del_ab code here?
        # f.seek(0x284)
        # del_ab = struct.unpack('>d', f.read(8))[0]
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
        # times = np.linspace(start_time, end_time, data.shape[0])
        return Trace(np.array([data]).T, times, name='TIC')


class AgilentFID2(TraceFile):
    # TODO: preliminary support, math may not be correct
    """
    Reads a Agilent FID *.ch file.
    """
    mime = 'application/vnd-agilent-chemstation-fid2'
    traces = ['fid']

    def _trace(self, name, twin):
        # this method allows self.trace('fid') to get something
        return self.total_trace(twin)

    def total_trace(self, twin=None):
        f = open(self.filename, 'rb')

        f.seek(0x11A)
        start_time = struct.unpack('>f', f.read(4))[0] / 60000.
        end_time = struct.unpack('>f', f.read(4))[0] / 60000.

        # TODO: figure out if this exists and where?
        # FID signal seems like 10x higher than it should be?
        # f.seek(0x284)
        # del_ab = 0.1  # struct.unpack('>d', f.read(8))[0]
        # data = []

        f.seek(0x1800)
        data = np.fromfile(f, '<f8')
        times = np.linspace(start_time, end_time, data.shape[0])
        return Trace(data, times, name='TIC')
