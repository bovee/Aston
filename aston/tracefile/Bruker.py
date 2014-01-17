import struct
import numpy as np
import scipy.sparse
from aston.trace.Trace import AstonFrame, AstonSeries
from aston.tracefile.TraceFile import TraceFile


class BrukerMSMS(TraceFile):
    ext = 'AMI'
    mgc = None
    traces = ['#ms']

    #def _getTotalTrace(self):
    #    pass

    @property
    def data(self):
        # convenience function for reading in data
        rd = lambda f, st: struct.unpack(st, f.read(struct.calcsize(st)))

        # open the file
        f = open(self.filename, 'rb')

        nscans = rd(f, 'ii')[1]
        if nscans == 0:
            self.data = AstonSeries(np.array([]), np.array([]), [])
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
            tot_pts += npts
            indptr[scn + 1] = tot_pts
        f.seek(dpos)

        ions = []
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
            i_lkup.update(dict((ion, i + len(ions) - 1) \
              for i, ion in enumerate(nions)))
            ions += nions

            idxs[indptr[scn]:indptr[scn + 1]] = \
                [i_lkup[int(i)] for i in rd_ions]
            vals[indptr[scn]:indptr[scn + 1]] = \
                abun

        idxs += 1
        data = scipy.sparse.csr_matrix((vals, idxs, indptr), \
                                    shape=(nscans, len(ions)), \
                                    dtype=float)
        return AstonFrame(data, times, ions)

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


#class BrukerBAF(TraceFile):
#    ext = 'BAF'
#    mgc = '2400'
#
#    pass
#    #TODO: implement this
