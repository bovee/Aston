# -*- coding: utf-8 -*-

import os.path as op
import gzip
import io
import struct
from datetime import datetime
from xml.etree import ElementTree
import numpy as np
import scipy.sparse
from aston.cache import cache
from aston.trace import Trace, Chromatogram
from aston.tracefile import TraceFile, ScanListFile
from aston.spectra import Scan


class AgilentMS(TraceFile):
    mime = 'application/vnd-agilent-chemstation-ms'
    traces = ['#ms']

    def total_trace(self, twin=None):
        # TODO: use twin?
        f = open(self.filename, 'rb')

        # get number of scans to read in
        f.seek(0x5)
        if f.read(4) == 'GC':
            f.seek(0x142)
        else:
            f.seek(0x118)
        nscans = struct.unpack('>H', f.read(2))[0]

        # find the starting location of the data
        f.seek(0x10A)
        f.seek(2 * struct.unpack('>H', f.read(2))[0] - 2)

        tme = np.zeros(nscans)
        tic = np.zeros(nscans)
        for i in range(nscans):
            npos = f.tell() + 2 * struct.unpack('>H', f.read(2))[0]
            tme[i] = struct.unpack('>I', f.read(4))[0] / 60000.
            f.seek(npos - 4)
            tic[i] = struct.unpack('>I', f.read(4))[0]
            f.seek(npos)
        f.close()
        return Trace(tic, tme, name='TIC')

    @property
    @cache(maxsize=1)
    def data(self):
        f = open(self.filename, 'rb')

        # get number of scans to read in
        # note that GC and LC chemstation store this in slightly different
        # places
        f.seek(0x5)
        if f.read(4) == 'GC':
            f.seek(0x142)
        else:
            f.seek(0x118)
        nscans = struct.unpack('>H', f.read(2))[0]

        f.seek(0x10A)
        f.seek(2 * struct.unpack('>H', f.read(2))[0] - 2)
        dstart = f.tell()

        # determine total number of measurements in file
        tot_pts = 0
        rowst = np.empty(nscans + 1, dtype=int)
        rowst[0] = 0

        for scn in range(nscans):
            # get the position of the next scan
            npos = f.tell() + 2 * struct.unpack('>H', f.read(2))[0]

            # keep a running total of how many measurements
            tot_pts += (npos - f.tell() - 26) // 4
            rowst[scn + 1] = tot_pts

            # move forward
            f.seek(npos)

        # go back to the beginning and load all the other data
        f.seek(dstart)

        ions = []
        i_lkup = {}
        cols = np.empty(tot_pts, dtype=int)
        vals = np.empty(tot_pts, dtype=np.int32)
        times = np.empty(nscans)

        for scn in range(nscans):
            npos = f.tell() + 2 * struct.unpack('>H', f.read(2))[0]

            # the sampling rate is evidentally 60 kHz on all Agilent's MS's
            times[scn] = struct.unpack('>I', f.read(4))[0] / 60000.

            f.seek(f.tell() + 12)
            npts = rowst[scn + 1] - rowst[scn]
            mzs = struct.unpack('>' + npts * 'HH', f.read(npts * 4))

            # there's some bug in the numpy implementation that makes this fail
            # after the first time
            # mzs = np.fromfile(f, dtype='>H', count=npts * 2)

            nions = set(mzs[0::2]).difference(i_lkup)
            i_lkup.update({ion: i + len(ions) for i, ion in enumerate(nions)})
            ions += nions

            cols[rowst[scn]:rowst[scn + 1]] = [i_lkup[i] for i in mzs[0::2]]
            vals[rowst[scn]:rowst[scn + 1]] = mzs[1::2]
            f.seek(npos)
        f.close()

        vals = ((vals & 16383) * 8 ** (vals >> 14)).astype(float)
        data = scipy.sparse.csr_matrix((vals, cols, rowst),
                                       shape=(nscans, len(ions)), dtype=float)
        ions = np.array(ions) / 20.
        return Chromatogram(data, times, ions)

    @property
    @cache(maxsize=1)
    def old_data(self):
        f = open(self.filename, 'rb')

        # get number of scans to read in
        # note that GC and LC chemstation store this in slightly different
        # places
        f.seek(0x5)
        if f.read(4) == 'GC':
            f.seek(0x142)
        else:
            f.seek(0x118)
        nscans = struct.unpack('>H', f.read(2))[0]

        # find the starting location of the data
        f.seek(0x10A)
        f.seek(2 * struct.unpack('>H', f.read(2))[0] - 2)

        # make a list of all of the ions and also read in times
        ions = set()
        times = np.empty(nscans)
        scan_locs = np.empty(nscans, dtype=int)
        scan_pts = np.empty(nscans, dtype=int)
        for scn in range(nscans):
            npos = f.tell() + 2 * struct.unpack('>H', f.read(2))[0]

            # the sampling rate is evidentally 60 kHz on all Agilent's MS's
            times[scn] = struct.unpack('>I', f.read(4))[0] / 60000.

            f.seek(f.tell() + 6)
            npts = struct.unpack('>H', f.read(2))[0]

            # jump to the data and save relevant parameters for later
            f.seek(f.tell() + 4)
            scan_locs[scn] = f.tell()
            scan_pts[scn] = npts

            # TODO: use numpy.fromfile?
            nions = np.fromfile(f, dtype='>H', count=npts * 2)[0::2]
            if scn < 2:
                print(npts)
                print(nions)
            # nions = struct.unpack('>' + npts * 'HH', f.read(npts * 4))[0::2]
            ions.update(nions)
            f.seek(npos)

        ions = np.array(sorted(list(ions)))
        data = np.empty((len(times), len(ions)), dtype=float)
        for scn in range(nscans):
            f.seek(scan_locs[scn])
            # TODO: use numpy.fromfile?
            mzs = np.fromfile(f, dtype='>H', count=scan_pts[scn] * 2)
            # mzs = np.array(struct.unpack('>' + npts * 'HH', f.read(npts * 4)))  # noqa
            if len(mzs) == 0:
                continue
            ilocs = np.searchsorted(ions, mzs[0::2])
            abn = (mzs[1::2] & 16383) * 8 ** (mzs[1::2] >> 14)
            data[scn][ilocs] = abn
        f.close()

        ions /= 20.
        return Chromatogram(data, times, ions)

    @property
    def info(self):
        d = super(AgilentMS, self).info
        f = open(self.filename, 'rb')
        f.seek(0x18)
        d['name'] = f.read(struct.unpack('>B', f.read(1))[0]).decode().strip()
        f.seek(0x94)
        d['r-opr'] = f.read(struct.unpack('>B', f.read(1))[0]).decode()
        f.seek(0xE4)
        d['m-name'] = f.read(struct.unpack('>B', f.read(1))[0]).decode().strip()  # noqa
        f.seek(0xB2)
        rawdate = f.read(struct.unpack('>B', f.read(1))[0]).decode()
        try:
            d['r-date'] = datetime.strptime(rawdate,
                                            "%d %b %y %H:%M %p").isoformat(' ')
        except ValueError:
            pass  # date is not in correct format to parse?
        # TODO: vial number in here too?
        f.close()

        # TODO: fill this out
        # read info from the acqmeth.txt file
        # fname = op.join(op.dirname(self.filename), 'acqmeth.txt')

        return d


class AgilentMSMSScan(ScanListFile):
    mime = 'application/vnd-agilent-masshunter-msmsscan'
    traces = ['#ms']

    # TODO: __init__ method that adds mrm trace names to traces
    def _scan_iter(self, keylist):
        f = open(self.filename, 'rb')
        r = ElementTree.parse(op.splitext(self.filename)[0] + '.xsd').getroot()

        xml_to_struct = {'xs:int': 'i', 'xs:long': 'q', 'xs:short': 'h',
                         'xs:byte': 'b', 'xs:double': 'd', 'xs:float': 'f'}
        rfrmt = {}

        for n in r.getchildren():
            name = n.get('name')
            for sn in n.getchildren()[0].getchildren():
                if rfrmt.get(name, None) is None:
                    rfrmt[name] = []
                sname = sn.get('name')
                stype = sn.get('type')
                rfrmt[name].append((sname, xml_to_struct.get(stype, stype)))

        def resolve(lookup, recname):
            names = [i[0] for i in lookup[recname]]
            frmts = [i[1] for i in lookup[recname]]
            flatnames = []
            flatfrmts = ''
            for n, f in zip(names, frmts):
                if len(f) != 1:
                    n, f = resolve(lookup, f)
                    flatnames += n
                else:
                    flatnames.append(n)
                flatfrmts += f
            return flatnames, flatfrmts

        fnames, ffrmts = resolve(rfrmt, 'ScanRecordType')
        rec_str = '<' + ffrmts
        sz = struct.calcsize(rec_str)

        f.seek(0x58)
        start_offset = struct.unpack('<i', f.read(4))[0]
        f.seek(start_offset)

        loc = [fnames.index(k) for k in keylist]
        while True:
            try:
                data = struct.unpack(rec_str, f.read(sz))
            except struct.error:
                break
            yield (data[l] for l in loc)
        f.close()

    def total_trace(self, twin=None):
        if twin is None:
            twin = (-np.inf, np.inf)
        tme = []
        tic = []
        for t, z in self._scan_iter(['ScanTime', 'TIC']):
            if t < twin[0]:
                continue
            elif t > twin[1]:
                break
            tme.append(t)
            tic.append(z)
        return Trace(np.array(tic), np.array(tme), name='TIC')
        # TODO: set .twin(twin) bounds on this

    def scans(self, twin=None):
        if twin is None:
            twin = (-np.inf, np.inf)

        # super hack-y way to disable checksum and length checking
        gzip.GzipFile._read_eof = lambda _: None  # noqa
        # standard prefix for every zip chunk
        gzprefix = b'\x1f\x8b\x08\x00\x00\x00\x00\x00\x04\x00'

        def uncompress(d):
            return gzip.GzipFile(fileobj=io.BytesIO(gzprefix + d)).read()

        f = open(op.join(op.split(self.filename)[0], 'MSProfile.bin'), 'rb')

        flds = ['ScanTime', 'SpectrumFormatID', 'SpectrumOffset',
                'ByteCount', 'PointCount', 'MinX', 'MaxX']

        for t, fmt, off, bc, pc, minx, maxx in self._scan_iter(flds):
            if t < twin[0]:
                continue
            if t > twin[1]:
                break

            f.seek(off)
            if fmt == 1:
                # this record is compressed with gz
                profdata = uncompress(f.read(bc))
                pd = np.array(struct.unpack('dd' + pc * 'i', profdata)[2:])
            elif fmt == 2:
                profdata = f.read(bc)
                pd = np.array(struct.unpack('dd' + pc * 'f', profdata)[2:])
            else:
                raise NotImplementedError('Unknown Agilent MH Scan format')
            # TODO: probably not a good approximation?
            ions = np.linspace(minx, maxx, len(pd))
            yield Scan(ions, pd, name=t)

        f.close()

    def mrm_trace(self, parent=None, daughter=None, tol=0.5, twin=None):
        # TODO: should override `trace` and then call parent's `trace` method
        # if name is not an mrm trace
        if twin is None:
            twin = (-np.inf, np.inf)

        tme, ic = [], []
        for t, off, bc, pc, minx, maxx, d_mz, p_mz, z in self._scan_iter([
            'ScanTime', 'SpectrumOffset', 'ByteCount', 'PointCount',
            'MinX', 'MaxX', 'BasePeakMZ', 'MzOfInterest', 'TIC'
        ]):
            if t < twin[0]:
                continue
            elif t > twin[1]:
                break
            if parent is not None:
                if np.abs(parent - p_mz) > tol:
                    continue
            if daughter is not None:
                if np.abs(daughter - d_mz) > tol:
                    continue
            tme.append(t)
            ic.append(z)

        return Trace(np.array(ic), np.array(tme),
                     name=str(str(parent) + '→' + str(daughter)))
