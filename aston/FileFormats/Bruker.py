from aston import Datafile
import struct
import numpy as np
import scipy.sparse


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

        # convenience function for reading in data
        rd = lambda f, st: struct.unpack(st, f.read(struct.calcsize(st)))

        # open the file
        f = open(self.rawdata, 'rb')

        nscans = rd(f, 'ii')[1]
        if nscans == 0:
            self.ions = []
            self.data = None
            return
        times = np.array(rd(f, nscans * 'd')) / 60.0
        f.seek(f.tell() + 4)  # number of scans again

        # set up the array of column indices
        indptr = np.empty(nscans + 1, dtype=int)
        indptr[0] = 0

        # figure out the total number of points
        dpos = f.tell()
        tot_pts = 0
        for scn in range(nscans):
            npts = rd(f, 'i')[0]
            #rd(f, npts * 'f' + 'i' + n_pts * 'f')
            f.seek(f.tell() + 8 * npts + 4)
            tot_pts += npts + 1
            indptr[scn + 1] = tot_pts
        f.seek(dpos)

        self.ions = []
        i_lkup = {}
        idxs = np.empty(tot_pts, dtype=int)
        vals = np.empty(tot_pts, dtype=float)

        for scn in range(nscans):
            npts = rd(f, 'i')[0]
            rd_ions = rd(f, npts * 'f')
            f.seek(f.tell() + 4)  # number of points again
            abun = rd(f, npts * 'f')

            nions = set([int(i) for i in rd_ions \
              if int(i) not in i_lkup])
            i_lkup.update(dict((ion, i + len(self.ions)) \
              for i, ion in enumerate(nions)))
            self.ions += nions

            idxs[indptr[scn]:indptr[scn + 1]] = \
                [-1] + [i_lkup[int(i)] for i in rd_ions]
            vals[indptr[scn]:indptr[scn + 1]] = \
                (times[scn],) + abun

        idxs += 1
        self.data = scipy.sparse.csr_matrix((vals, idxs, indptr), \
                                    shape=(nscans, len(self.ions) + 1), \
                                    dtype=float)

        #self.data = np.zeros((recs, 2))
        #times = rd(f, nscans * 'd')
        #self.data[:, 0] = np.array(times) / 60
        #ions = set()
        #rd(f, 'i')  # number of data points again
        #for i in range(nscans):
        #    n_pts = rd(f, 'i')[0]
        #    ions.update(rd(f, n_pts * 'f'))
        #    rd(f, 'i')  # number of pts in spectra again
        #    abun = rd(f, n_pts * 'f')
        #    #self.data[i, 0] = times[i] / 60
        #    self.data[i, 1] = sum(abun)
        #f.close()
        #self.ions = [1]

    def _updateInfoFromFile(self):
        d = {}
        d['r-type'] = 'Sample'
        self.info.update(d)
