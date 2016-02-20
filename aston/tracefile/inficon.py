# -*- coding: utf-8 -*-
import struct
import numpy as np
from aston.trace import Chromatogram
from aston.tracefile import TraceFile, find_offset


class InficonHapsite(TraceFile):
    mime = 'application/vnd-inficon-hapsite'
    traces = ['#ms']

    def _ions(self, f):
        """
        This is a generator that returns the mzs being measured during
        each time segment, one segment at a time.
        """
        outside_pos = f.tell()
        doff = find_offset(f, 4 * b'\xff' + 'HapsSearch'.encode('ascii'))
        # actual end of prev section is 34 bytes before, but assume 1 rec
        f.seek(doff - 62)
        # seek backwards to find the FFFFFFFF header
        while True:
            f.seek(f.tell() - 8)
            if f.read(4) == 4 * b'\xff':
                break
        f.seek(f.tell() + 64)
        nsegments = struct.unpack('<I', f.read(4))[0]
        for _ in range(nsegments):
            # first 32 bytes are segment name, rest are something else?
            f.seek(f.tell() + 96)
            nions = struct.unpack('<I', f.read(4))[0]
            ions = []
            for _ in range(nions):
                # TODO: check that itype is actually a SIM/full scan switch
                i1, i2, _, _, _, _, itype, _ = struct.unpack('<' + 8 * 'I',
                                                             f.read(32))
                if itype == 0:  # SIM
                    ions.append(i1 / 100.)
                else:  # full scan
                    # TODO: this might be a little hacky?
                    #  ideally we would need to know n for this, e.g.:
                    # ions += np.linspace(i1 / 100, i2 / 100, n).tolist()
                    ions += np.arange(i1 / 100., i2 / 100. + 1, 1).tolist()
            # save the file position and load the position
            # that we were at before we started this code
            inside_pos = f.tell()
            f.seek(outside_pos)
            yield ions
            outside_pos = f.tell()
            f.seek(inside_pos)
        f.seek(outside_pos)

    @property
    def data(self):
        # TODO: handle skip mass ranges
        with open(self.filename, 'rb') as f:
            # read in the time segments/mz ranges for the run

            # read in the data itself
            doff = find_offset(f, 4 * b'\xff' + 'HapsScan'.encode('ascii'))
            if doff is None:
                return
            f.seek(doff - 20)
            data_end = doff + struct.unpack('<I', f.read(4))[0] + 55

            f.seek(doff + 56)
            times, abns, mzs = [], [], []
            cur_seg = None
            mz_reader = self._ions(f)
            while f.tell() <= data_end:
                # record info looks like a standard format
                n, t, _, recs, _, seg = struct.unpack('<IiHHHH', f.read(16))
                if cur_seg != seg:
                    # if we've switched segments, update the list of mzs
                    try:
                        cur_mzs = next(mz_reader)
                    except StopIteration:
                        break
                    mzs += set(cur_mzs).difference(mzs)
                    mz_idx = [mzs.index(i) for i in cur_mzs]
                cur_seg = seg

                # just add the new time in
                times.append(t)

                # read the list of abundances
                cur_abns = struct.unpack('<' + 'f' * recs, f.read(4 * recs))
                # convert this list into an array that matches up with
                # whatever mzs we currently have
                empty_row = np.zeros(len(mzs))
                empty_row[mz_idx] = cur_abns
                # add that row into the list
                abns.append(empty_row)

        # convert the time from milliseconds to minutes
        times = np.array(times, dtype=float) / 60000
        # create the data array and populate it
        data = np.zeros((len(times), len(mzs)))
        for i, r in enumerate(abns):
            data[i, 0:len(r)] = r
        return Chromatogram(data, times, mzs)
