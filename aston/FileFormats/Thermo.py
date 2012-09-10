from aston import Datafile
import struct
import time
import os
import numpy as np


class ThermoCF(Datafile.Datafile):
    ext = 'CF'
    mgc = 0xFFFF

    def __init__(self, *args, **kwargs):
        super(ThermoCF, self).__init__(*args, **kwargs)

    def _cacheData(self):
        if self.data is not None:
            return

        f = open(self.rawdata, 'rb')
        f.seek(19)
        while True:
            f.seek(f.tell() - 19)
            if f.read(19) == b'CRawDataScanStorage':
                break
            if f.read(1) == b'':
                f.close()
                return

        f.seek(f.tell() + 62)
        nscans = struct.unpack('H', f.read(2))[0]

        #TODO: this shouldn't be hardcoded
        self.ions = [44, 45, 46]
        ni = len(self.ions)

        f.seek(f.tell() + 35)
        self.data = np.array([struct.unpack('<f' + ni * 'd', \
          f.read(4 + ni * 8)) for _ in range(nscans)])
        self.data[:, 0] /= 60.  # convert time to minutes
        f.close()

    def _updateInfoFromFile(self):
        d = {}
        d['r-opr'] = ''
        d['m'] = ''
        #try: #TODO: this crashes in python 3; not clear why?
        d['r-date'] = time.ctime(os.path.getctime(self.rawdata))
        #except:
        #    pass
        #info['file name'] = os.path.basename(self.filename)
        d['name'] = os.path.splitext(os.path.basename(self.rawdata))[0]
        d['r-type'] = 'Sample'
        self.info.update(d)


class ThermoDXF(Datafile.Datafile):
    ext = 'DXF'
    mgc = 0xFFFF

    def __init__(self, *args, **kwargs):
        super(ThermoDXF, self).__init__(*args, **kwargs)

    def _cacheData(self):
        if self.data is not None:
            return

        f = open(self.rawdata, 'rb')
        f.seek(11)
        while True:
            f.seek(f.tell() - 11)
            if f.read(11) == b'CEvalGCData':
                break
            if f.read(1) == b'':
                f.close()
                return

        f.read(4)  # not sure what this value means?

        #TODO: this shouldn't be hardcoded
        self.ions = [44, 45, 46]
        ni = len(self.ions)

        #bytes until the end converted to # of records
        nscans = int(struct.unpack('<I', f.read(4))[0] / \
                (4.0 + ni * 8.0))

        self.data = np.array([struct.unpack('<f' + ni * 'd', \
          f.read(4 + ni * 8)) for _ in range(nscans)])
        self.data[:, 0] /= 60.  # convert time to minutes
        f.close()

    def _updateInfoFromFile(self):
        d = {}
        d['r-opr'] = ''
        d['m'] = ''
        #try: #TODO: this crashes in python 3; not clear why?
        d['date'] = time.ctime(os.path.getctime(self.rawdata))
        #except:
        #    pass
        #info['file name'] = os.path.basename(self.filename)
        d['name'] = os.path.splitext(os.path.basename(self.rawdata))[0]
        d['r-type'] = 'Sample'
        self.info.update(d)
