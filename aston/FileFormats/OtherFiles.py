from aston import Datafile
import os.path as op
import numpy as np
import struct


class AgilentFID(Datafile.Datafile):
    # TODO: preliminary support, math is probably not correct
    """
    Reads a Agilent FID *.ch file.
    """
    ext = 'CH'
    mgc = 0x0238

    def __init__(self, *args, **kwargs):
        super(AgilentFID, self).__init__(*args, **kwargs)

    def _cacheData(self):
        if self.data is not None:
            return
        f = open(self.rawdata, 'rb')

        f.seek(0x11A)
        start_time = struct.unpack('>f', f.read(4))[0] / 60000.
        #end_time 0x11E '>i'

        f.seek(0x284)
        del_ab = struct.unpack('>d', f.read(8))[0]
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
                data.append(del_ab * (inp * 32767 + inp2))
            else:
                delt += del_ab * inp
                data.append(data[-1] + delt)
        f.close()
        # TODO: 0.4/60.0 should be obtained from the file???
        times = np.array(start_time + np.arange(len(data)) * (0.2 / 60.0))
        self.ions = [1]
        self.data = np.array([times, data]).T

    def _updateInfoFromFile(self):
        pass


class CSVFile(Datafile.Datafile):
    '''
    Reads in a *.CSV. Assumes that the first line is the header and
    that the file is comma delimited.
    '''
    ext = 'CSV'
    mgc = None

    def __init__(self, *args, **kwargs):
        super(CSVFile, self).__init__(*args, **kwargs)

    def _cacheData(self):
        delim = ','
        try:  # TODO: better, smarter error checking than this
            with open(self.rawdata, 'r') as f:
                lns = f.readlines()
                self.ions = [float(i) for i in lns[0].split(delim)[1:]]
                self.data = np.array( \
                    [np.fromstring(ln, sep=delim) for ln in lns[1:]])
        except:
            self.data = np.array([])

    def _updateInfoFromFile(self):
        d = {}
        d['name'] = op.splitext(op.basename(self.rawdata))[0]
        d['r-type'] = 'Sample'
        self.info.update(d)
