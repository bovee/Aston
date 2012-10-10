from aston import Datafile
import struct
import numpy as np


class BrukerMSMS(Datafile.Datafile):
    ext = 'AMI'
    mgc = None

    def __init__(self, *args, **kwargs):
        super(BrukerMSMS, self).__init__(*args, **kwargs)

    #def _getTotalTrace(self):
    #    pass

    def _cacheData(self):
        if self.data is not None:
            return

        # rd(f,'ii'); plt.plot(range(3000), rd(f,3000*'d')-1.2*range(3000))

        f = open(self.rawdata, 'rb')
        rd = lambda f, st: struct.unpack(st, f.read(struct.calcsize(st)))
        recs = rd(f, 'ii')[1]
        self.data = np.zeros((recs, 2))
        times = rd(f, recs * 'd')
        self.data[:, 0] = np.array(times) / 60
        ions = set()
        rd(f, 'i')  # number of data points again
        for i in range(recs):
            n_pts = rd(f, 'i')[0]
            ions.update(rd(f, n_pts * 'f'))
            rd(f, 'i')  # number of pts in spectra again
            abun = rd(f, n_pts * 'f')
            #self.data[i, 0] = times[i] / 60
            self.data[i, 1] = sum(abun)
        print(sorted(ions)[:20])
        f.close()
        self.ions = [1]

    def _updateInfoFromFile(self):
        d = {}
        d['r-type'] = 'Sample'
        self.info.update(d)
