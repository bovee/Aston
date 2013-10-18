import os.path as op
import gzip
import io
import struct
from functools import lru_cache
import numpy as np
#import scipy
from datetime import datetime
from xml.etree import ElementTree
from pandas import DataFrame, Series
from aston.tracefile.AgilentCommon import AgilentMH, AgilentCS


class AgilentMS(AgilentCS):
    ext = 'MS'
    mgc = '0132'

    def total_trace(self, twin=None):
        #TODO: use twin?
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
        return Series(tic, tme, name='TIC')

    @property
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

            #TODO: use numpy.fromfile?
            nions = struct.unpack('>' + npts * 'HH', f.read(npts * 4))[0::2]
            ions.update(nions)
            f.seek(npos)

        ions = np.array(sorted(list(ions)))
        data = np.empty((len(times), len(ions)), dtype=float)
        for scn in range(nscans):
            f.seek(scan_locs[scn])
            npts = scan_pts[scn]
            #TODO: use numpy.fromfile?
            mzs = np.array(struct.unpack('>' + npts * 'HH', f.read(npts * 4)))
            if len(mzs) == 0:
                continue
            ilocs = np.searchsorted(ions, mzs[0::2])
            abn = (mzs[1::2] & 16383) * 8 ** (mzs[1::2] >> 14)
            data[scn][ilocs] = abn
        f.close()

        ions = ions / 20
        return DataFrame(data, times, ions)

    @property
    def info(self):
        d = super(AgilentMS, self).info
        f = open(self.filename, 'rb')
        f.seek(0x18)
        d['name'] = f.read(struct.unpack('>B', f.read(1))[0]).decode().strip()
        f.seek(0x94)
        d['r-opr'] = f.read(struct.unpack('>B', f.read(1))[0]).decode()
        f.seek(0xE4)
        d['m'] = f.read(struct.unpack('>B', f.read(1))[0]).decode().strip()
        f.seek(0xB2)
        rawdate = f.read(struct.unpack('>B', f.read(1))[0]).decode()
        try:
            d['r-date'] = datetime.strptime(rawdate, \
              "%d %b %y %H:%M %p").isoformat(' ')
        except ValueError:
            pass  # date is not in correct format to parse?
        d['r-type'] = 'Sample'
        #TODO: vial number in here too?
        f.close()

        #TODO: fill this out
        ## read info from the acqmeth.txt file
        #fname = op.join(op.dirname(self.filename), 'acqmeth.txt')

        return d


class AgilentMSMSScan(AgilentMH):
    ext = 'BIN'
    mgc = '0101'

    def _msscan_iter(self, keylist):
        f = open(self.filename, 'rb')
        r = ElementTree.parse(op.splitext(self.filename)[0] + '.xsd').getroot()

        xml_to_struct = {'xs:int': 'i', 'xs:long': 'q', 'xs:short': 'h', \
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
        for t, z in self._msscan_iter(['ScanTime', 'TIC']):
            if t < twin[0]:
                continue
            elif t > twin[1]:
                break
            tme.append(t)
            tic.append(z)
        return Series(np.array(tic), np.array(tme), name='TIC')
        #TODO: set .twin(twin) bounds on this

    #FIXME: need to define a trace_names with ions in it
    def trace(self, name='', tol=0.5, twin=None):
        #TODO: should be able to call my parent classes too
        if name in ['', 'X', 'TIC']:
            return self.total_trace(twin)
        if twin is None:
            twin = (-np.inf, np.inf)

        #super hack-y way to disable checksum and length checking
        gzip.GzipFile._read_eof = lambda _: None
        # standard prefix for every zip chunk
        gzprefix = b'\x1f\x8b\x08\x00\x00\x00\x00\x00\x04\x00'
        uncompress = lambda d: gzip.GzipFile(fileobj=io.BytesIO(d)).read()
        f = open(op.join(op.split(self.filename)[0], 'MSProfile.bin'), 'rb')

        tme, ic = [], []
        sminx, smaxx = np.inf, np.inf
        for t, off, bc, pc, minx, maxx in self._msscan_iter( \
          ['ScanTime', 'SpectrumOffset', 'ByteCount', \
          'PointCount', 'MinX', 'MaxX']):
            if t < twin[0]:
                continue
            elif t > twin[1]:
                break
            tme.append(t)
            f.seek(off)
            profdata = uncompress(gzprefix + f.read(bc))
            pd = np.array(struct.unpack('dd' + pc * 'i', profdata)[2:])
            if sminx != minx or smaxx != maxx:
                ions = np.linspace(minx, maxx, len(pd))
                ion_loc = np.logical_and(ions > name - tol, \
                  ions < name + tol)
                sminx, smaxx = minx, maxx
            ic.append(sum(pd[ion_loc]))

        f.close()
        return Series(np.array(ic), np.array(tme), name=str(name))

    def mrm_trace(self, parent=None, daughter=None, tol=0.5, twin=None):
        if twin is None:
            twin = (-np.inf, np.inf)

        tme, ic = [], []
        for t, off, bc, pc, minx, maxx, d_mz, p_mz, z in self._msscan_iter( \
          ['ScanTime', 'SpectrumOffset', 'ByteCount', 'PointCount', \
           'MinX', 'MaxX', 'BasePeakMZ', 'MzOfInterest', 'TIC']):
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

        return Series(np.array(ic), np.array(tme), \
                      name=str(str(parent) + '->' + str(daughter)))

    def scan(self, time, to_time=None):
        #TODO: support time ranges
        #super hack-y way to disable checksum and length checking
        gzip.GzipFile._read_eof = lambda _: None
        # standard prefix for every zip chunk
        gzprefix = b'\x1f\x8b\x08\x00\x00\x00\x00\x00\x04\x00'
        uncompress = lambda d: gzip.GzipFile(fileobj=io.BytesIO(d)).read()
        f = open(op.join(op.split(self.filename)[0], 'MSProfile.bin'), 'rb')

        time_dist = np.inf
        time = self._sc_off(time)
        for t, off, bc, pc, minx, maxx in self._msscan_iter( \
          ['ScanTime', 'SpectrumOffset', 'ByteCount', \
          'PointCount', 'MinX', 'MaxX']):
            if time_dist > np.abs(t - time):
                time_dist = np.abs(t - time)
                s_p = (off, bc, pc, minx, maxx)
            else:
                off, bc, pc, minx, maxx = s_p
                f.seek(off)
                profdata = uncompress(gzprefix + f.read(bc))
                pd = struct.unpack('dd' + pc * 'i', profdata)[2:]
                break
        f.close()
        ions = np.linspace(minx, maxx, len(pd))
        return np.vstack([ions, pd])
