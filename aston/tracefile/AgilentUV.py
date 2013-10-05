import os
import re
import struct
from datetime import datetime
import numpy as np
from pandas import DataFrame
from aston.tracefile.AgilentCommon import AgilentMH, AgilentCS


class AgilentMWD(AgilentCS):
    ext = 'CH'
    mgc = '0233'

    @property
    def data(self):
        #Because the spectra are stored in several files in the same
        #directory, we need to loop through them and return them together.
        ions = []
        dtraces = []
        foldname = os.path.dirname(self.filename)
        #if foldname == '': foldname = os.curdir
        for i in [os.path.join(foldname, i) for i \
          in os.listdir(foldname)]:
            if i[-3:].upper() == '.CH':
                wv, dtrace = self._read_ind_file(i)

                #generate the time points if this is the first trace
                if len(ions) == 0:
                    f = open(i, 'rb')
                    f.seek(0x11A)
                    st_t = struct.unpack('>i', f.read(4))[0] / 60000.
                    en_t = struct.unpack('>i', f.read(4))[0] / 60000.
                    f.close()

                    times = np.linspace(st_t, en_t, len(dtrace))

                #add the wavelength and trace into the appropriate places
                ions.append(float(wv))
                dtraces.append(dtrace)
        data = np.array(dtraces).transpose()
        return DataFrame(data, times, ions)

    def _read_ind_file(self, fname):
        f = open(fname, 'rb')

        f.seek(0x254)
        sig_name = str(f.read(struct.unpack('>B', f.read(1))[0]))
        #wavelength the file was collected at
        wv = re.search("Sig=(\d+),(\d+)", sig_name).group(1)

        f.seek(0x284)
        del_ab = struct.unpack('>d', f.read(8))[0]

        data = np.array([])

        f.seek(0x401)
        loc = 0
        while True:
            rec_len = struct.unpack('>B', f.read(1))[0]
            if rec_len == 0:
                break
            data = np.append(data, np.empty(rec_len))
            for _ in range(rec_len):
                inp = struct.unpack('>h', f.read(2))[0]
                if inp == -32768:
                    inp = struct.unpack('>i', f.read(4))[0]
                    data[loc] = del_ab * inp
                elif loc == 0:
                    data[loc] = del_ab * inp
                else:
                    data[loc] = data[loc - 1] + del_ab * inp
                loc += 1
            f.read(1)  # this value is always 0x10?
        f.close()
        return wv, data

    @property
    def info(self):
        d = super(AgilentMWD, self).info
        #TODO: fix this so that it doesn't rely upon MWD1A.CH?
        f = open(self.filename, 'rb')
        f.seek(0x18)
        d['name'] = f.read(struct.unpack('>B', f.read(1))[0]).decode()
        f.seek(0x94)
        d['r-opr'] = f.read(struct.unpack('>B', f.read(1))[0]).decode()
        f.seek(0xE4)
        d['m'] = f.read(struct.unpack('>B', f.read(1))[0]).decode()
        #try:
        f.seek(0xB2)
        rawdate = f.read(struct.unpack('>B', f.read(1))[0]).decode()
        d['r-date'] = datetime.strptime(rawdate, \
          "%d-%b-%y, %H:%M:%S").isoformat(' ')
        #except: pass #TODO: find out why this chokes
        f.seek(0x244)
        d['m-y-units'] = f.read(struct.unpack('>B', f.read(1))[0]).decode()
        f.seek(0x254)
        #TODO: replace signal name with reference_wavelength?
        #d['signal name'] = f.read(struct.unpack('>B', f.read(1))[0]).decode()
        d['r-type'] = 'Sample'
        f.close()
        return d


class AgilentMWD2(AgilentCS):
    ext = 'CH'
    mgc = '0331'

    @property
    def data(self):
        #Because the spectra are stored in several files in the same
        #directory, we need to loop through them and return them together.
        ions = []
        dtraces = []
        foldname = os.path.dirname(self.filename)
        for i in [os.path.join(foldname, i) for i \
          in os.listdir(foldname)]:
            if i[-3:].upper() == '.CH':
                wv, dtrace = self._read_ind_file(i)

                #generate the time points if this is the first trace
                if len(ions) == 0:
                    f = open(i, 'rb')
                    f.seek(0x11A)
                    st_t = struct.unpack('>i', f.read(4))[0] / 60000.
                    en_t = struct.unpack('>i', f.read(4))[0] / 60000.
                    f.close()

                    times = np.linspace(st_t, en_t, len(dtrace))

                #add the wavelength and trace into the appropriate places
                ions.append(float(wv))
                dtraces.append(dtrace)
        data = np.array(dtraces).transpose()
        return DataFrame(data, times, ions)

    def _read_ind_file(self, fname):
        f = open(fname, 'rb')

        f.seek(0x1075)
        sig_name = f.read(2 * struct.unpack('>B', \
          f.read(1))[0]).decode('utf-16')
        #wavelength the file was collected at
        wv = re.search("Sig=(\d+),(\d+)", sig_name).group(1)

        f.seek(0x127C)
        del_ab = struct.unpack('>d', f.read(8))[0]

        #data = np.array([])
        data = []

        f.seek(0x1800)
        while True:
            x, nrecs = struct.unpack('>BB', f.read(2))
            if x == 0 and nrecs == 0:
                break
            for _ in range(nrecs):
                inp = struct.unpack('>h', f.read(2))[0]
                if inp == -32768:
                    inp = struct.unpack('>i', f.read(4))[0]
                    data.append(del_ab * inp)
                elif len(data) == 0:
                    data.append(del_ab * inp)
                else:
                    data.append(data[-1] + del_ab * inp)
        f.close()
        return wv, np.array(data)

    @property
    def info(self):
        d = super(AgilentMWD2, self).info
        #TODO: fix this so that it doesn't rely upon MWD1A.CH?

        def get_str(f, off):
            """
            Convenience function to quickly pull out strings.
            """
            f.seek(off)
            return f.read(2 * struct.unpack('>B', \
              f.read(1))[0]).decode('utf-16')

        f = open(self.filename, 'rb')
        d['name'] = get_str(f, 0x35A)
        d['r-opr'] = get_str(f, 0x758)
        d['m'] = get_str(f, 0xA0E)
        rawdate = get_str(f, 0x957)
        d['r-date'] = datetime.strptime(rawdate, \
          "%d-%b-%y, %H:%M:%S").isoformat(' ')
        d['m-y-units'] = get_str(f, 0x104C)
        #TODO: replace signal name with reference_wavelength?
        #d['signal name'] = f.read(struct.unpack('>B', f.read(1))[0]).decode()
        d['r-type'] = 'Sample'
        f.close()
        return d


class AgilentDAD(AgilentMH):
    ext = 'SD'

    #header data in DAD1.sd
    #80 byte repetition
    #offset = 0xA4, format = 'IIfIfffQIIdddd'
    # 750 entries
    #f.seek(0xA4); struct.unpack('<IddffIQIIdddd', f.read(80))

    #time series in DAD1.sg
    #all doubles, starts at 0x44
    #750x 54 double entries
    @property
    def data(self):
        fhead = open(self.filename[:-3] + '.sd', 'rb')
        fdata = open(self.filename[:-3] + '.sp', 'rb')

        fhead.seek(0x50)
        nscans = struct.unpack('Q', fhead.read(8))[0]
        fhead.seek(0xA4)

        ions = []
        for scn in range(nscans):
            t = struct.unpack('<IdddIQIIdddd', fhead.read(80))

            npts = t[7]
            if scn == 0:
                #TODO: this will fail if the wavelengths collected
                #change through the run.
                data = np.zeros((nscans, npts))
                times = np.zeros((nscans))
                ions = [str(t[8] + x * t[3]) for x in range(npts)]

            times[scn] = t[1]

            fdata.seek(t[5] + 16)
            #TODO: use np.fromfile?
            data[scn] = struct.unpack('<' + npts * 'd', fdata.read(npts * 8))
        return DataFrame(data, times, ions)

        fhead.close()
        fdata.close()


class AgilentCSDAD(AgilentCS):
    """
    Interpreter for *.UV files from Agilent Chemstation
    """
    ext = 'UV'
    mgc = '0331'

    @property
    def data(self):
        #TODO: the chromatograms this generates are not exactly the
        #same as the ones in the *.CH files. Maybe they need to be 0'd?
        f = open(self.filename, 'rb')

        f.seek(0x116)
        nscans = struct.unpack('>i', f.read(4))[0]

        times = np.zeros(nscans)
        data = nscans * [{}]
        ions = []
        npos = 0x202
        for i in range(nscans):
            f.seek(npos)
            npos += struct.unpack('<H', f.read(2))[0]
            times[i] = struct.unpack('<L', f.read(4))[0] / 60000.
            nm_srt = struct.unpack('<H', f.read(2))[0] / 20.
            nm_end = struct.unpack('<H', f.read(2))[0] / 20.
            nm_stp = struct.unpack('<H', f.read(2))[0] / 20.
            f.read(8)
            s = {}
            v = struct.unpack('<h', f.read(2))[0] / 2000.
            s[nm_srt] = v
            for wv in np.arange(nm_srt, nm_end, nm_stp):
                ov = struct.unpack('<h', f.read(2))[0]
                if ov == -32768:
                    v = struct.unpack('<i', f.read(4))[0] / 2000.
                else:
                    v += ov / 2000.
                s[wv] = v
                if wv not in ions:
                    ions.append(wv)
            data[i] = s

        ndata = np.zeros((nscans, len(ions)))
        for i, d in zip(range(nscans), data):
            for ion, abn in d.items():
                ndata[i, ions.index(ion)] = abn
        return DataFrame(ndata, times, ions)

    @property
    def info(self):
        d = super(AgilentCSDAD, self).info
        with open(self.filename, 'rb') as f:
            string_read = lambda f: f.read(struct.unpack('>B', \
                f.read(1))[0]).decode('ascii').strip()
            f.seek(0x18)
            d['name'] = string_read(f)
            f.seek(0x94)
            d['r-opr'] = string_read(f)
            f.seek(0xE4)
            d['m'] = string_read(f)
            f.seek(0xB2)
            rawdate = string_read(f)
            try:  # fails on 0331 UV files
                d['r-date'] = datetime.strptime(rawdate, \
                    "%d-%b-%y, %H:%M:%S").isoformat(' ')
            except:
                pass
            f.seek(0x146)
            d['m-y-units'] = string_read(f)
            f.seek(0xD0)
            d['r-inst'] = string_read(f)
            #TODO: are the next values correct?
            f.seek(0xFE)
            d['r-vial-pos'] = string_read(f)
            f.seek(0xFE)
            d['r-seq-num'] = string_read(f)
        return d


class AgilentCSDAD2(AgilentCS):
    """
    Interpreter for *.UV files from Agilent Chemstation
    """
    ext = 'UV'
    mgc = '0331'

    #@profile
    @property
    def data(self):
        f = open(self.filename, 'rb')

        f.seek(0x116)
        nscans = struct.unpack('>i', f.read(4))[0]

        # get all wavelengths and times
        wvs = set()
        times = np.empty(nscans)
        npos = 0x1002
        for i in range(nscans):
            f.seek(npos)
            npos += struct.unpack('<H', f.read(2))[0]
            times[i] = struct.unpack('<L', f.read(4))[0]
            nm_srt, nm_end, nm_stp = struct.unpack('<HHH', f.read(6))
            n_wvs = np.arange(nm_srt, nm_end, nm_stp) / 20.
            wvs.update(set(n_wvs).difference(wvs))
        wvs = list(wvs)

        ndata = np.empty((nscans, len(wvs)), dtype="<i4")
        npos = 0x1002
        for i in range(nscans):
            f.seek(npos)
            dlen = struct.unpack('<H', f.read(2))[0]
            npos += dlen
            f.seek(f.tell() + 4)  # skip time
            nm_srt, nm_end, nm_stp = struct.unpack('<HHH', f.read(6))
            f.seek(f.tell() + 8)

            ## OLD CODE
            v = 0
            pos = f.tell()
            for wv in np.arange(nm_srt, nm_end, nm_stp) / 20.:
                ov = struct.unpack('<h', f.read(2))[0]
                if ov == -32768:
                    v = struct.unpack('<i', f.read(4))[0]
                else:
                    v += ov
                ndata[i, wvs.index(wv)] = v
            f.seek(pos)

            ## WORKING ON A FASTER WAY TO READ ALL THIS DATA BELOW
            ## read in all the data
            #data = np.fromfile(f, dtype="<i2", count=int((dlen - 24) / 2))

            ## if there are any records marked -32768, we need to reinterpret
            ## parts of the array as i4's
            #oob_idxs = np.where(data == -32768)[0]

            ## locations of the cells to merge into 32-bit ints
            #big_idxs = np.repeat(oob_idxs, 2) + \
            #        np.tile([1, 2], oob_idxs.shape[0])
            #big_data = data[big_idxs].view('<i4').copy()

            ## remove the 32-bit cells, so the arrays the right size
            #data = np.delete(data, big_idxs).astype("<i4")

            ## set the marker cells to the right values
            #oob_idxs = np.where(data == -32768)[0]
            #data[oob_idxs] = big_data

            ## compute cumulative sums for each chunk
            #pidx = 0
            #if data.shape[0] != ndata.shape[1]:
            #    print(big_data)
            #for idx in np.hstack([oob_idxs, data.shape[0]]):
            #    ndata[i, pidx:idx] = np.cumsum(data[pidx:idx])
            #    pidx = idx

        return DataFrame(ndata / 2000., times / 60000., wvs)

    @property
    def info(self):
        d = super(AgilentCSDAD2, self).info
        with open(self.filename, 'rb') as f:
            string_read = lambda f: f.read(2 * struct.unpack('>B', \
                f.read(1))[0]).decode('utf-16').strip()
            f.seek(0x35A)
            d['name'] = string_read(f)
            f.seek(0x758)
            d['r-opr'] = string_read(f)
            # get date into correct format before using this
            #f.seek(0x957)
            #d['r-date'] = string_read()
            f.seek(0xA0E)
            d['m'] = string_read(f)
            f.seek(0xC15)
            d['m-y-units'] = string_read(f)
        return d
