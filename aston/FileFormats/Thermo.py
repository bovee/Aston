import struct
import os
import numpy as np
from aston import Datafile
from aston.TimeSeries import TimeSeries


class ThermoCF(Datafile.Datafile):
    ext = 'CF'
    mgc = 'FFFF'

    def _cache_data(self):
        if self.data is not None:
            return

        f = open(self.rawdata, 'rb')
        f.seek(19)
        while True:
            f.seek(f.tell() - 19)
            if f.read(19) == b'CRawDataScanStorage':
                break
            if f.read(1) == b'':
                f.close()
                return

        f.seek(f.tell() + 62)
        nscans = struct.unpack('H', f.read(2))[0]

        #TODO: this shouldn't be hardcoded
        ions = [44, 45, 46]
        ni = len(ions)

        f.seek(f.tell() + 35)
        data = np.array([struct.unpack('<f' + ni * 'd', \
          f.read(4 + ni * 8)) for _ in range(nscans)])
        data[:, 0] /= 60.  # convert time to minutes
        self.data = TimeSeries(data[:, 1:], data[:, 0], ions)
        f.close()

    def _update_info_from_file(self):
        d = {}
        d['r-opr'] = ''
        d['m'] = ''
        #info['file name'] = os.path.basename(self.filename)
        d['name'] = os.path.splitext(os.path.basename(self.rawdata))[0]
        d['r-type'] = 'Sample'
        self.info.update(d)


class ThermoDXF(Datafile.Datafile):
    ext = 'DXF'
    mgc = 'FFFF'

    def _cache_data(self):
        if self.data is not None:
            return

        f = open(self.rawdata, 'rb')
        f.seek(11)
        while True:
            f.seek(f.tell() - 11)
            if f.read(11) == b'CEvalGCData':
                break
            if f.read(1) == b'':
                f.close()
                return

        f.read(4)  # not sure what this value means?

        #TODO: this shouldn't be hardcoded
        # these values can be found under
        #CChannelGasConfPart?
        #45.0 0x1420ef
        #46.0 0x14211c
        #
        ions = [44, 45, 46]
        ni = len(ions)

        #bytes until the end converted to # of records
        nscans = int(struct.unpack('<I', f.read(4))[0] / \
                (4.0 + ni * 8.0))

        data = np.array([struct.unpack('<f' + ni * 'd', \
          f.read(4 + ni * 8)) for _ in range(nscans)])

        data[:, 0] /= 60.  # convert time to minutes
        self.data = TimeSeries(data[:, 1:], data[:, 0], ions)
        f.close()

    def _update_info_from_file(self):
        d = {}
        d['r-opr'] = ''
        d['m'] = ''
        #try: #TODO: this crashes in python 3; not clear why?
        #except:
        #    pass
        #info['file name'] = os.path.basename(self.filename)
        d['name'] = os.path.splitext(os.path.basename(self.rawdata))[0]
        d['r-type'] = 'Sample'
        #TODO: there has to be a better way than this to get these values
        # at least don't keep cycling through the file for each one
        foff_o = self._th_off('d 18O/16O'.encode('utf_16_le'))
        foff_c = self._th_off('d 13C/12C'.encode('utf_16_le'), hint=foff_o)
        with open(self.rawdata, 'rb') as f:
            if foff_o is not None:
                f.seek(foff_o + 68)
                d['r-d18o-std'] = str(struct.unpack('<d', f.read(8)))
            if foff_c is not None:
                f.seek(foff_c + 68)
                d['r-d13c-std'] = str(struct.unpack('<d', f.read(8)))
        self.info.update(d)

    def _th_off(self, search_str, hint=None):
        if hint is None:
            hint = 0
        with open(self.rawdata, 'rb') as f:
            f.seek(hint)
            f.seek(len(search_str))
            while True:
                f.seek(f.tell() - len(search_str))
                if f.read(len(search_str)) == search_str:
                    break
                if f.read(1) == b'':
                    f.close()
                    return None
            foff = f.tell()
        return foff

    def events(self, kind):
        #TODO: read in ref gas pulses
        evts = super(ThermoDXF, self).events(kind)
        if kind == 'refgas':
            with open(self.rawdata, 'rb') as f:
                f.seek(self._th_off('CActionHwTransferContainer'))
                evt, time, status = [], [], []
                while True:
                    d = struct.unpack('<ihHBB', f.read(10))
                    if d[0] != 3:
                        #TODO: probably a better way to figure this out
                        break
                    #name1 = f.read(2 * d[4]).decode('utf-16')
                    f.read(2 * d[4])
                    d = struct.unpack('<HBB', f.read(4))
                    name2 = f.read(2 * d[2]).decode('utf-16')
                    d = struct.unpack('<iiiiiiiih', f.read(34))
                    if d[4] == 2:
                        status.append(d[5])
                    else:
                        time.append(d[4] / 60000.)
                        evt.append(name2)
                    if d[-1] == -1:
                        # first record ends (?) with this, so skip
                        # the CValveTransfer part afterwards
                        f.read(22)
            p_st, gas_on, i = None, False, 0
            for e, t, s in zip(evt, time, status):
                if e.startswith('Reference'):
                    gas_on = (s == 1)
                if gas_on:
                    p_st = t
                elif not gas_on and p_st is not None:
                    i += 1
                    evts.append([p_st, t, 'R' + str(i)])
        return evts


class ThermoRAW(Datafile.Datafile):
    ext = 'RAW'
    mgc = '01A1'

    #TODO: write the rest of this!
