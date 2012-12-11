# -*- coding: utf-8 -*-
import struct
import numpy as np
import scipy
import os.path as op
import gzip
import io
from datetime import datetime
from xml.etree import ElementTree
from aston import Datafile
from aston.TimeSeries import TimeSeries


class AgilentMS(Datafile.Datafile):
    ext = 'MS'
    mgc = '0132'

    def __init__(self, *args, **kwargs):
        super(AgilentMS, self).__init__(*args, **kwargs)

    def _total_trace(self, twin=None):
        f = open(self.rawdata, 'rb')

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
        return TimeSeries(tic, tme, ['TIC'])

    def _cache_data(self):
        if self.data is not None:
            return

        f = open(self.rawdata, 'rb')

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

        tot_pts = 0
        indptr = np.empty(nscans + 1, dtype=int)
        indptr[0] = 0
        for scn in range(nscans):
            npos = f.tell() + 2 * struct.unpack('>H', f.read(2))[0]
            #f.seek(f.tell()+10)
            #tot_pts += 1+struct.unpack('>H',f.read(2))[0]
            tot_pts += (npos - f.tell() - 22) / 4
            indptr[scn + 1] = tot_pts
            f.seek(npos)

        # find the starting location of the data
        f.seek(0x10A)
        # jump to the start of the data
        f.seek(2 * struct.unpack('>H', f.read(2))[0] - 2)

        ions = []
        i_lkup = {}
        idxs = np.empty(tot_pts, dtype=int)
        vals = np.empty(tot_pts, dtype=float)

        times = np.empty(nscans)
        for scn in range(nscans):
            npos = f.tell() + 2 * struct.unpack('>H', f.read(2))[0]
            # the sampling rate is evidentally 60 kHz on all Agilent's MS's
            times[scn] = struct.unpack('>I', f.read(4))[0] / 60000.

            f.seek(f.tell() + 4)
            npts = indptr[scn + 1] - indptr[scn]
            mzs = struct.unpack('>' + npts * 'HH', f.read(npts * 4))

            nions = set([mz for mz in mzs[0::2] if mz not in i_lkup])
            i_lkup.update(dict((ion, i + len(ions)) \
              for i, ion in enumerate(nions)))
            ions += nions

            idxs[indptr[scn]:indptr[scn + 1]] = \
              [i_lkup[i] for i in mzs[0::2]]
            vals[indptr[scn]:indptr[scn + 1]] = mzs[1::2]
            f.seek(npos)
        f.close()

        idxs += 1
        data = scipy.sparse.csr_matrix((vals, idxs, indptr), \
                                    shape=(nscans, len(ions)), \
                                    dtype=float)
        ions = [i / 20. for i in ions]
        self.data = TimeSeries(data, times, ions)

    def _update_info_from_file(self):
        d = {}
        f = open(self.rawdata, 'rb')
        f.seek(0x18)
        d['name'] = f.read(struct.unpack('>B', f.read(1))[0]).decode().strip()
        f.seek(0x94)
        d['r-opr'] = f.read(struct.unpack('>B', f.read(1))[0]).decode()
        f.seek(0xE4)
        d['m'] = f.read(struct.unpack('>B', f.read(1))[0]).decode().strip()
        f.seek(0xB2)
        rawdate = f.read(struct.unpack('>B', f.read(1))[0]).decode()
        d['r-date'] = datetime.strptime(rawdate, \
          "%d %b %y %H:%M %p").isoformat(' ')
        d['r-type'] = 'Sample'
        #TODO: vial number in here too?
        f.close()
        self.info.update(d)


class AgilentMSMSScan(Datafile.Datafile):
    ext = 'BIN'
    mgc = '0101'

    def __init__(self, *args, **kwargs):
        super(AgilentMSMSScan, self).__init__(*args, **kwargs)

    def _msscan_iter(self, keylist):
        f = open(self.rawdata, 'rb')
        r = ElementTree.parse(op.splitext(self.rawdata)[0] + '.xsd').getroot()

        xml_to_struct = {'xs:int': 'i', 'xs:long': 'q', 'xs:byte': 'b', 'xs:double': 'd'}
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

    def _total_trace(self, twin):
        tme = []
        tic = []
        for t, z in self._msscan_iter(['ScanTime', 'TIC']):
            tme.append(t)
            tic.append(z)
        return TimeSeries(np.array(tic), np.array(tme), ['TIC'])

    def _ion_trace(self, val, tol=0.5, twin=None):
        #super hack-y way to disable checksum and length checking
        gzip.GzipFile._read_eof = lambda _: None
        # standard prefix for every zip chunk
        gzprefix = b'\x1f\x8b\x08\x00\x00\x00\x00\x00\x04\x00'
        uncompress = lambda d: gzip.GzipFile(fileobj=io.BytesIO(d)).read()
        f = open(op.join(op.split(self.rawdata)[0], 'MSProfile.bin'), 'rb')

        tme = []
        ic = []
        sminx, smaxx = np.inf, np.inf
        for t, off, bc, pc, minx, maxx in self._msscan_iter( \
          ['ScanTime', 'SpectrumOffset', 'ByteCount', \
          'PointCount', 'MinX', 'MaxX']):
            tme.append(t)
            f.seek(off)
            profdata = uncompress(gzprefix + f.read(bc))
            pd = np.array(struct.unpack('dd' + pc * 'i', profdata)[2:])
            if sminx != minx or smaxx != maxx:
                ions = np.linspace(minx, maxx, len(pd))
                ion_loc = np.logical_and(ions > val - tol, \
                  ions < val + tol)
                sminx, smaxx = minx, maxx
            ic.append(sum(pd[ion_loc]))

        f.close()
        return TimeSeries(np.array(ic), np.array(tme), [val])

    def scan(self, time, to_time=None):
        #TODO: support time ranges
        #super hack-y way to disable checksum and length checking
        gzip.GzipFile._read_eof = lambda _: None
        # standard prefix for every zip chunk
        gzprefix = b'\x1f\x8b\x08\x00\x00\x00\x00\x00\x04\x00'
        uncompress = lambda d: gzip.GzipFile(fileobj=io.BytesIO(d)).read()
        f = open(op.join(op.split(self.rawdata)[0], 'MSProfile.bin'), 'rb')

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

    def _update_info_from_file(self):
        d = {}
        try:
            u = lambda s: s.decode('utf-8')
            u('')
        except:
            u = lambda s: s

        xml_file = op.join(op.dirname(self.rawdata), 'sample_info.xml')
        r = ElementTree.parse(xml_file).getroot()
        info = dict((i.find('Name').text, i.find('Value').text) \
          for i in r.findall('Field'))
        d['name'] = info.get('Sample Name', '')
        d['r-vial-pos'] = info.get('Sample Position', '')
        d['r-inst'] = info.get('InstrumentName', '')
        d['r-opr'] = info.get('OperatorName', '')
        d['r-date'] = info.get('AcqTime', '').replace('T',' ').rstrip('Z')
        d['m-inj-size'] = info.get(u('Inj Vol (µl)'), '')

        xml_file = op.join(op.dirname(self.rawdata), 'acqmethod.xml')
        r = ElementTree.parse(xml_file).getroot()
        d['m-len'] = r.find('.//CapPump//Stoptime').text
        d['m-flw'] = r.find('.//CapPump//Flow').text
        d['m-slv'] = r.find('.//CapPump//SolvNameA').text
        d['m-slv-B'] = r.find('.//CapPump//SolvNameB').text
        d['m-slv-B-per'] = r.find('.//CapPump//SolvRatioB').text
        d['m-slv-C'] = r.find('.//CapPump//SolvNameC').text
        d['m-slv-D'] = r.find('.//CapPump//SolvNameD').text
        d['m-tmp'] = r.find('.//TCC//LeftTemp').text

        self.info.update(d)

    def _other_trace(self, name):
        #TODO: read from MSPeriodicActuals.bin and TCC.* files
        return np.zeros(len(self.times))
