# -*- coding: utf-8 -*-
import struct
import numpy as np
from aston.cache import cache
from aston.trace import Trace
from aston.tracefile import TraceFile


class AgilentCSPump(TraceFile):
    mime = 'application/vnd-agilent-chemstation-pump'
    traces = []
    # traces = ['mslva', 'mslvb', 'mslvc', 'mslvd', 'mflow']

    @property
    def info(self):
        d = super(AgilentCSPump, self).info
        fd = read_reg_file(open(self.filename, 'rb'))
        if fd.get('TIMETABLE', False):
            # get solv_B, solv_C, solv_D, flow
            # calculate solv_A
            pass
        else:
            if fd.get('SOLV_RATIO_A', False):
                pass
            if fd.get('SOLV_RATIO_B', False):
                pass
            if fd.get('SOLV_RATIO_C', False):
                pass
            if fd.get('SOLV_RATIO_D', False):
                pass
            if fd.get('FLOW', False):
                pass
        return d

    def _trace(self, name, twin):
        # TODO: return method traces
        pass


class AgilentCSFraction(TraceFile):
    mime = 'application/vnd-agilent-chemstation-fraction'
    traces = ['*fxn']

    def events(self, name='fxn', twin=None):
        # TODO: use twin
        evts = super(AgilentCSFraction, self).events(name, twin)
        if name != 'fxn':
            return evts

        acq_file = open(self.filename, 'rb')
        acq_file.seek(0x19)
        vers = acq_file.read(7)

        if vers.startswith(b'A'):
            print('FXN', self.filename)
        elif vers == b'notused':
            acq_file.seek(0xED)
            nfxns = struct.unpack('<I', acq_file.read(4))[0]
            acq_file.seek(0x33F)
            for _ in range(nfxns):
                d = struct.unpack('<Q9fI4f7I', acq_file.read(92))
                evts.append({'t0': d[13] / 60000., 't1': d[14] / 60000.})

            acq_file.seek(acq_file.tell() + 264)
            for i in range(nfxns):
                slen = struct.unpack('<H', acq_file.read(2))[0] - 1
                evts[i]['name'] = acq_file.read(2 * slen).decode('utf-16')
        return evts


class AgilentCSFlowInject(TraceFile):
    mime = 'application/vnd-agilent-chemstation-flowinject'
    traces = ['*fia']

    def events(self, name='fia', twin=None):
        # TODO: use twin
        evts = super(AgilentCSFlowInject, self).events(name, twin)
        if name != 'fia':
            return evts

        acq_file = open(self.filename, 'rb')
        acq_file.seek(0x19)
        vers = acq_file.read(7)

        if vers.startswith(b'A'):
            d = read_reg_file(acq_file)
            if not d.get(u'FIARun', False):
                return []
            prev_f = d['FIASeriesInfo'][1][1]
            for f in d['FIASeriesInfo'][1][2:]:
                evts.append({'t0': prev_f[0], 't1': f[0], 'name': prev_f[2]})
                prev_f = f
            else:
                if len(evts) > 0:
                    off_t = evts[-1]['t1'] - evts[-1]['t0']
                    evts.append({'t0': prev_f[0], 't1': prev_f[0] + off_t,
                                 'name': prev_f[2]})
        elif vers == b'notused':
            # TODO: get fia from new-style *.REG files.
            print('FIA', self.filename)
            pass
        return evts


class AgilentCSLC(TraceFile):
    mime = 'application/vnd-agilent-chemstation-lcstat'

    _tr_names = {'pres': 'PMP1, Pressure', 'flow': 'PMP1, Flow',
                 'slva': 'PMP1, Solvent A', 'slvb': 'PMP1, Solvent B',
                 'slvc': 'PMP1, Solvent C', 'slvd': 'PMP1, Solvent D'}

    @property
    @cache(maxsize=1)
    def traces(self):
        traces = []
        for abrv, full in self._tr_names.items():
            df = read_multireg_file(open(self.filename, 'rb'), title=full)
            if 'Trace' in df:
                traces.append(abrv)
        return traces

    def _trace(self, name, twin):
        # TODO: read info from new style REG files
        df = read_multireg_file(open(self.filename, 'rb'),
                                title=self._tr_names[name])
        if 'Trace' not in df:
            return Trace([], [])
        ts = df['Trace']
        ts.name = name
        return ts.twin(twin)


def read_multireg_file(f, title=None):
    """
    Some REG files have multiple "sections" with different data.
    This parses each chunk out of such a file (e.g. LCDIAG.REG)
    """
    f.seek(0x26)
    nparts = struct.unpack('<H', f.read(2))[0]
    foff = 0x2D
    if title is None:
        data = []
        for _ in range(nparts):
            d = read_reg_file(f, foff)
            data.append(d)
            foff = f.tell() + 1
    else:
        for _ in range(nparts):
            d = read_reg_file(f, foff)
            if d.get('Title') == title:
                data = d
                break
            foff = f.tell() + 1
        else:
            data = {}
    return data


def read_reg_file(f, foff=0x2D):
    """
    Given a file handle for an old-style Agilent *.REG file, this
    will parse that file into a dictonary of key/value pairs
    (including any tables that are in the *.REG file, which will
    be parsed into lists of lists).
    """
    # convenience function for reading in data
    def rd(st):
        return struct.unpack(st, f.read(struct.calcsize(st)))

    f.seek(0x19)
    if f.read(1) != b'A':
        # raise TypeError("Version of REG file is too new.")
        return {}

    f.seek(foff)
    nrecs = rd('<I')[0]  # TODO: should be '<H'
    rec_tab = [rd('<HHIII') for n in range(nrecs)]

    names = {}
    f.seek(foff + 20 * nrecs + 4)
    for r in rec_tab:
        d = f.read(r[2])
        if r[1] == 1539:  # '0306'
            # this is part of the linked list too, but contains a
            # reference to a table
            cd = struct.unpack('<HIII21sI', d)
            names[cd[5]] = cd[4].decode('iso8859').strip('\x00')
            # except:
            #     pass
        elif r[1] == 32769 or r[1] == 32771:  # b'0180' or b'0380'
            names[r[4]] = d[:-1].decode('iso8859')
        elif r[1] == 32774:  # b'0680'
            # this is a string that is referenced elsewhere (in a table)
            names[r[4]] = d[2:-1].decode('iso8859')
        elif r[1] == 32770:  # b'0280'
            # this is just a flattened numeric array
            names[r[4]] = np.frombuffer(d, dtype=np.uint32, offset=4)

    data = {}
    f.seek(foff + 20 * nrecs + 4)
    for r in rec_tab:
        d = f.read(r[2])
        if r[1] == 1538:  # '0206'
            # this is part of a linked list
            if len(d) == 43:
                cd = struct.unpack('<HIII21sd', d)
                data[cd[4].decode('iso8859').strip('\x00')] = cd[5]
            else:
                pass
        elif r[1] == 1537:  # b'0106'
            # name of property
            n = d[14:30].split(b'\x00')[0].decode('iso8859')
            # with value from names
            data[n] = names.get(struct.unpack('<I', d[35:39])[0], '')
        elif r[1] == 1793:  # b'0107'
            # this is a table of values
            nrow = struct.unpack('<H', d[4:6])[0]
            ncol = struct.unpack('<H', d[16:18])[0]
            if ncol != 0:
                cols = [struct.unpack('<16sHHHHHI', d[20 + 30 * i:50 + 30 * i])
                        for i in range(ncol)]
                colnames = [c[0].split(b'\x00')[0].decode('iso8859')
                            for c in cols]
                # TODO: type 2 is not a constant size? 31, 17
                rty2sty = {1: 'H', 3: 'I', 4: 'f', 5: 'H',
                           7: 'H', 8: 'd', 11: 'H', 12: 'H',
                           13: 'I', 14: 'I', 16: 'H'}
                coltype = '<' + ''.join([rty2sty.get(c[3], str(c[2]) + 's')
                                         for c in cols])
                lencol = struct.calcsize(coltype)
                tab = []
                for i in reversed(range(2, nrow + 2)):
                    rawrow = struct.unpack(coltype,
                                           d[-i * lencol: (1 - i) * lencol])
                    row = []
                    for j, p in enumerate(rawrow):
                        if cols[j][3] == 3:
                            row.append(names.get(p, str(p)))
                        else:
                            row.append(p)
                    tab.append(row)
                data[names[r[4]]] = [colnames, tab]
        elif r[1] == 1281 or r[1] == 1283:  # b'0105' or b'0305'
            fm = '<HHBIIhIdII12shIddQQB8sII12shIddQQB8s'
            m = struct.unpack(fm, d)
            nrecs = m[4]  # number of points in table

            # x_units = names.get(m[8], '')
            x_arr = m[14] * names.get(m[9], np.arange(nrecs - 1))
            y_arr = m[25] * names.get(m[20])
            y_units = names.get(m[19], '')
            if y_units == 'bar':
                y_arr *= 0.1  # convert to MPa
            # TODO: what to call this?
            data['Trace'] = Trace(y_arr, x_arr, name='')
        # elif r[1] == 1025:  # b'0104'
        #     # lots of zeros? maybe one or two numbers?
        #     # only found in REG entries that have long 0280 records
        #     fm = '<HQQQIHHHHIIHB'
        #     m = struct.unpack(fm, d)
        #     print(m)
        #     #print(r[1], len(d), binascii.hexlify(d))
        #     pass
        # elif r[1] == 512:  # b'0002'
        #     # either points to two null pointers or two other pointers
        #     # (indicates start of linked list?)
        #     print(r[1], len(d), binascii.hexlify(d))
        # elif r[1] == 769 or r[1] == 772:  # b'0103' or b'0403'
        #     # points to 2nd, 3rd & 4th records (two 0002 records and a 0180)
        #     b = binascii.hexlify
        #     print(b(d[10:14]), b(d[14:18]), b(d[18:22]))

    return data


def read_regb_file(f):
    pass
    # CObArray
    # either 2 bytes long (0100) or 8 (0000 0380 0580 XXXX)

    # CHPAnnText
    # [j[36:36+2*struct.unpack('<H', j[34:36])[0]].decode('utf-16') \
    #  for i, j in a if i == b'CHPAnnText']
    # slen = struct.unpack('<H', struct_dat[34:36])
    # struct_dat[36:36 + slen * 2].decode('utf-16')

    # CHPDatLongRow
    #  starts at byte 14?

    # CHPNdrString
    # [j[12:12 + 2 * struct.unpack('<H', j[10:12])[0]].decode('utf-16') \
    #  for i, j in a if i == b'CHPNdrString']

    # CHPNdrObject

    # CHPTable
