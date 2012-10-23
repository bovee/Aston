from aston import Datafile
import struct
import numpy as np
import scipy
import sys
import os.path as op
from xml.etree import ElementTree


class AgilentMS(Datafile.Datafile):
    ext = 'MS'
    mgc = 0x0132

    def __init__(self, *args, **kwargs):
        super(AgilentMS, self).__init__(*args, **kwargs)

    def _getTotalTrace(self):
        #TODO: this no longer does anything
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
        return tic

    def _cacheData(self):
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

        for scn in range(nscans):
            npos = f.tell() + 2 * struct.unpack('>H', f.read(2))[0]
            # the sampling rate is evidentally 60 kHz on all Agilent's MS's
            tme = struct.unpack('>I', f.read(4))[0] / 60000.

            f.seek(f.tell() + 4)
            npts = indptr[scn + 1] - indptr[scn] - 1
            mzs = struct.unpack('>' + npts * 'HH', f.read(npts * 4))

            nions = set([mz for mz in mzs[0::2] if mz not in i_lkup])
            i_lkup.update(dict((ion, i + len(ions)) \
                                  for i, ion in enumerate(nions)))
            ions += nions

            idxs[indptr[scn]:indptr[scn + 1]] = \
                [-1] + [i_lkup[i] for i in mzs[0::2]]
            vals[indptr[scn]:indptr[scn + 1]] = \
                (tme,) + mzs[1::2]

            f.seek(npos)
        f.close()

        idxs += 1
        d = scipy.sparse.csr_matrix((vals, idxs, indptr), \
                                    shape=(nscans, len(ions) + 1), \
                                    dtype=float)

        self.ions = [i / 20. for i in ions]
        self.data = d

    def _updateInfoFromFile(self):
        d = {}
        f = open(self.rawdata, 'rb')
        f.seek(0x18)
        d['name'] = f.read(struct.unpack('>B', f.read(1))[0]).decode().strip()
        f.seek(0x94)
        d['r-opr'] = f.read(struct.unpack('>B', f.read(1))[0]).decode()
        f.seek(0xE4)
        d['m'] = f.read(struct.unpack('>B', f.read(1))[0]).decode().strip()
        f.seek(0xB2)
        d['r-date'] = f.read(struct.unpack('>B', f.read(1))[0]).decode()
        d['r-type'] = 'Sample'
        #TODO: vial number in here too?
        f.close()
        self.info.update(d)


class AgilentMSMSScan(Datafile.Datafile):
    ext = 'BIN'
    mgc = 0x0101

    def __init__(self, *args, **kwargs):
        super(AgilentMSMSScan, self).__init__(*args, **kwargs)

    #def _getTotalTrace(self):
    #    pass

    def _cacheData(self):
        if self.data is not None:
            return

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

        f.seek(0x0058)
        start_offset = struct.unpack('<i', f.read(4))[0]
        f.seek(start_offset)

        import gzip
        import io
        gzip.GzipFile._read_eof = lambda _: None
        gzprefix = b'\x1f\x8b\x08\x00\x00\x00\x00\x00\x04\x00'
        uncompress = lambda d: gzip.GzipFile(fileobj=io.BytesIO(d)).read()
        f2 = open(op.join(op.split(self.rawdata)[0], 'MSProfile.bin'), 'rb')

        #TODO: rewrite below to get ions from MSProf.bin instead
        tloc = fnames.index('ScanTime')
        zloc = fnames.index('TIC')
        t = []
        z = []
        while True:
            try:
                data = struct.unpack(rec_str, f.read(sz))
                if len(t) < 5:
                    d = dict(zip(fnames, data))
                    f2.seek(d['SpectrumOffset'])
                    profdata = uncompress(gzprefix + f2.read(d['ByteCount']))
                    pd = struct.unpack('dd' + d['PointCount'] * 'i', profdata)
                    print(sum(pd[2:]), d['TIC'])
            except struct.error:
                break
            t.append(data[tloc])
            z.append(data[zloc])
        f.close()
        f2.close()
        self.ions = [1]
        self.data = np.array([t, z]).transpose()

    def _updateInfoFromFile(self):
        d = {}
        #d['name'] = str(f.read(struct.unpack('>B',f.read(1))[0]).strip())
        #d['r-opr'] = str(f.read(struct.unpack('>B',f.read(1))[0]))
        #d['m'] = str(f.read(struct.unpack('>B',f.read(1))[0]))
        #d['r-date'] = str(f.read(struct.unpack('>B', f.read(1))[0]))
        #d['r-type'] = 'Sample'
        self.info.update(d)

    def _getOtherTrace(self, name):
        #TODO: read from MSPeriodicActuals.bin and TCC.* files
        return np.zeros(len(self.times))
