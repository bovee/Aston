import struct
import re
import os
import numpy as np
from aston.trace import Chromatogram
from aston.tracefile import TraceFile, find_offset


class ThermoCF(TraceFile):
    mime = 'application/vnd-thermo-cf'
    traces = ['#irms']

    @property
    def data(self):
        f = open(self.filename, 'rb')
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

        # TODO: this shouldn't be hardcoded
        ions = [44, 45, 46]
        ni = len(ions)

        f.seek(f.tell() + 35)
        data = np.array([struct.unpack('<f' + ni * 'd', f.read(4 + ni * 8))
                         for _ in range(nscans)])
        data[:, 0] /= 60.  # convert time to minutes
        # self.data = TimeSeries(data[:, 1:], data[:, 0], ions)
        f.close()
        return Chromatogram(data[:, 1:], data[:, 0], ions)

    @property
    def info(self):
        d = super(ThermoCF, self).info
        # info['file name'] = os.path.basename(self.filename)
        d['name'] = os.path.splitext(os.path.basename(self.filename))[0]
        return d


class ThermoDXF(TraceFile):
    mime = 'application/vnd-thermo-dxf'
    traces = ['#irms', '*refgas']

    @property
    def data(self):
        f = open(self.filename, 'rb')

        # TODO: use find_offset to find this?
        # f.seek(11)
        # while True:
        #     f.seek(f.tell() - 11)
        #     if f.read(11) == b'CEvalGCData':
        #         break
        #     if f.read(1) == b'':
        #         f.close()
        #         return
        f.seek(find_offset(f, b'CRawData') + 9)
        strlen = 2 * struct.unpack('<B', f.read(1))[0]
        tname = f.read(strlen).decode('utf_16_le')
        if tname == 'CO2':
            ions = [44, 45, 46]
        elif tname == 'CO':
            ions = [28, 29, 30]
        elif tname == 'SO2,SO-SO2 Ext,SO':
            # TODO: check this is in the right order
            ions = [48, 49, 50, 64, 65, 66]
        else:
            # TODO: should save the tname somewhere for future reference
            ions = [1, 2, 3]

        f.seek(find_offset(f, b'CEvalGCData') + 4)

        # bytes until the end converted to # of records
        nscans = int(struct.unpack('<I', f.read(4))[0] /
                     (4.0 + len(ions) * 8.0))

        dtype = np.dtype([('index', '<f4'), ('values', '<f8', len(ions))])
        data = np.fromfile(f, dtype=dtype, count=nscans)
        # convert time to minutes
        data['index'] /= 60.

        f.close()
        return Chromatogram(data['values'], data['index'], ions)

    @property
    def info(self):
        d = super(ThermoDXF, self).info
        # try: #TODO: this crashes in python 3; not clear why?
        # except:
        #     pass
        # info['file name'] = os.path.basename(self.filename)
        d['name'] = os.path.splitext(os.path.basename(self.filename))[0]
        with open(self.filename, 'rb') as f:
            foff_o = find_offset(f, 'd 18O/16O'.encode('utf_16_le'))
            foff_c = find_offset(f, 'd 13C/12C'.encode('utf_16_le'))
            if foff_o is not None:
                f.seek(foff_o + 68)
                d['d18o_std'] = str(struct.unpack('<d', f.read(8))[0])
            if foff_c is not None:
                f.seek(foff_c + 68)
                d['d13c_std'] = str(struct.unpack('<d', f.read(8))[0])
        return d

    def _th_off(self, search_str, hint=None):
        # TODO: replace all occurances with find_offset?
        if hint is None:
            hint = 0
        with open(self.filename, 'rb') as f:
            f.seek(hint)
            regexp = re.compile(search_str.encode('ascii'))
            while True:
                d = f.read(len(search_str) * 200)
                srch = regexp.search(d)
                if srch is not None:
                    foff = f.tell() - len(d) + srch.end()
                    break
                if len(d) == len(search_str):  # no data read: EOF
                    f.close()
                    return None
                f.seek(f.tell() - len(search_str))
        return foff

    def events(self, name='refgas', twin=None):
        # TODO: use twin
        # TODO: read in ref gas pulses
        evts = super(ThermoDXF, self).events(name, twin)
        if name != 'refgas':
            return evts

        with open(self.filename, 'rb') as f:
            f.seek(self._th_off('CActionHwTransferContainer'))
            evt, time, status = [], [], []
            while True:
                d = struct.unpack('<ihHBB', f.read(10))
                if d[0] != 3:
                    # TODO: probably a better way to figure this out
                    break
                # name1 = f.read(2 * d[4]).decode('utf-16')
                f.read(2 * d[4])
                d = struct.unpack('<HBB', f.read(4))
                name2 = f.read(2 * d[2]).decode('utf-16')
                d = struct.unpack('<iiiiiiiih', f.read(34))
                if d[4] == 2:
                    status.append(d[5])
                else:
                    # TODO: needs a correction factor to be
                    # derived from guesswork; timing in
                    # Isodat/Conflo is uncoupled? BAD
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
                    evts.append({'t0': p_st, 't1': t, 'name': 'R' + str(i)})
        return evts


class ThermoRAW(TraceFile):
    mime = 'application/vnd-thermo-raw'
    traces = ['#ms']

    # TODO: write the rest of this!
