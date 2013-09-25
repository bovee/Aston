import numpy as np
import struct
from pandas import DataFrame, Series
from aston.file_adapters.Common import FileAdapter
from aston.file_adapters.AgilentCommon import AgilentCS


class AgilentFID(AgilentCS):
    # TODO: preliminary support, math is probably not correct
    """
    Reads a Agilent FID *.ch file.
    """
    ext = 'CH'
    mgc = '0238'

    def data(self):
        f = open(self.rawdata, 'rb')

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


class CSVFile(FileAdapter):
    '''
    Reads in a *.CSV. Assumes that the first line is the header and
    that the file is comma delimited.
    '''
    ext = 'CSV'
    mgc = None
    #TODO: use pandas to make this much better

    def data(self):
        delim = ','
        try:  # TODO: better, smarter error checking than this
            with open(self.rawdata, 'r') as f:
                lns = f.readlines()
                ions = [float(i) for i in lns[0].split(delim)[1:]]
                data = np.array([np.fromstring(ln, sep=delim) \
                                 for ln in lns[1:]])
                return DataFrame(data[:, 1:], data[:, 0], ions)
        except:
            return DataFrame()
