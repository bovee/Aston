import struct
import numpy as np
import scipy.sparse
from aston.trace import Chromatogram, Trace
from aston.tracefile import TraceFile


class BrukerMSMS(TraceFile):
    mime = 'application/vnd-bruker-msms'
    traces = ['#ms']

    # def _getTotalTrace(self):
    #     pass

    @property
    def data(self):
        # convenience function for reading in data
        def rd(f, st):
            return struct.unpack(st, f.read(struct.calcsize(st)))

        # open the file
        f = open(self.filename, 'rb')

        nscans = rd(f, 'ii')[1]
        if nscans == 0:
            self.data = Trace(np.array([]), np.array([]), [])
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
            # rd(f, npts * 'f' + 'i' + n_pts * 'f')
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

            nions = set([int(i) for i in rd_ions if int(i) not in i_lkup])
            i_lkup.update(dict((ion, i + len(ions) - 1)
                               for i, ion in enumerate(nions)))
            ions += nions

            idxs[indptr[scn]:indptr[scn + 1]] = \
                [i_lkup[int(i)] for i in rd_ions]
            vals[indptr[scn]:indptr[scn + 1]] = \
                abun

        idxs += 1
        data = scipy.sparse.csr_matrix((vals, idxs, indptr),
                                       shape=(nscans, len(ions)), dtype=float)
        return Chromatogram(data, times, ions)

        # self.data = np.zeros((recs, 2))
        # times = rd(f, nscans * 'd')
        # self.data[:, 0] = np.array(times) / 60
        # ions = set()
        # rd(f, 'i')  # number of data points again
        # for i in range(nscans):
        #     n_pts = rd(f, 'i')[0]
        #     ions.update(rd(f, n_pts * 'f'))
        #     rd(f, 'i')  # number of pts in spectra again
        #     abun = rd(f, n_pts * 'f')
        #     #self.data[i, 0] = times[i] / 60
        #     self.data[i, 1] = sum(abun)
        # f.close()
        # self.ions = [1]


class BrukerBAF(TraceFile):
    mime = 'application/vnd-bruker-baf'

    pass
    # TODO: implement this
    # 0x000c - q - 230 or 242

    ###############################################
    # file 1 - 230 ("Carolina")
    # 0xFFFFFFFFFFFF at 0x678D, 0x6825, 0xC459, 0x491AD,
    # 0x500E7, 0x57C39, and 25+ others

    # text section starts 0x018E, ends 0x6708

    # 0x409BF - (d- -1.000) then a ton of doubles

    # 3000 scans?, 2371 ions

    ###############################################
    # file 2 - 230 ("Short")

    ###############################################
    # file 3 - 242
    # 0xFFFFFFFFFFFF at 0x6BEF, 0x6CB7, 0x4044A

    # text section starts 0x0186, ends 0x6B3B

    # some CHP records at 0xAE9B til 0xBF5d (?)

    # 0x42a1e - (d- -1.000) then a ton of doubles
    # til 0x23DFFF56

    # 0x23FA916A - 0xFFFFFFFF before last data chunk?
