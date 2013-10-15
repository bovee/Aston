# -*- coding: utf-8 -*-
import struct
import os.path as op
from xml.etree import ElementTree
import numpy as np
from pandas import Series
from aston.tracefile.Common import TraceFile


class AgilentMH(TraceFile):
    """
    Base class for Agilent files from Masshunter.
    """
    @property
    def info(self):
        folder = op.dirname(self.filename)
        d = super(AgilentMH, self).info
        try:
            u = lambda s: s.decode('utf-8')
            u('')
        except:
            u = lambda s: s

        try:
            xml_file = op.join(folder, 'sample_info.xml')
            r = ElementTree.parse(xml_file).getroot()
            info = dict((i.find('Name').text, i.find('Value').text) \
              for i in r.findall('Field'))
            d['name'] = info.get('Sample Name', '')
            d['r-vial-pos'] = info.get('Sample Position', '')
            d['r-inst'] = info.get('InstrumentName', '')
            d['r-opr'] = info.get('OperatorName', '')
            d['r-date'] = info.get('AcqTime', '').replace('T', \
            ' ').rstrip('Z')
            d['m-inj-size'] = info.get(u('Inj Vol (µl)'), '')
        except IOError:
            pass

        try:
            xml_file = op.join(folder, 'acqmethod.xml')
            r = ElementTree.parse(xml_file).getroot()
            d['m-len'] = r.find('.//CapPump//Stoptime').text
            d['m-flw'] = r.find('.//CapPump//Flow').text
            d['m-slv'] = r.find('.//CapPump//SolvNameA').text
            d['m-slv-B'] = r.find('.//CapPump//SolvNameB').text
            d['m-slv-B-per'] = r.find('.//CapPump//SolvRatioB').text
            d['m-slv-C'] = r.find('.//CapPump//SolvNameC').text
            d['m-slv-D'] = r.find('.//CapPump//SolvNameD').text
            d['m-tmp'] = r.find('.//TCC//LeftTemp').text
        except IOError:
            pass
        except AttributeError:
            #e.g. if LeftTemp is not set, find will
            #return None and None has no attribute text
            #TODO: better fix for this
            pass
        return d

    def trace_names(self, named):
        if named:
            names = ['pres', 'flow', 'slvb', 'temp']
        else:
            names = []
        return super(AgilentMH, self).trace_names(named) + names

    def trace(self, name='', twin=None):
        if name in ['pres', 'flow', 'slvb']:
            fname = op.join(op.dirname(self.filename), 'CapPump1.cd')
            ttab = {'pres': 'Pressure', 'flow': 'Flow', \
                    'slvb': '%B'}
        elif name in ['temp']:
            fname = op.join(op.dirname(self.filename), 'TCC1.cd')
            ttab = {'temp': 'Temperature of Left Heat Exchanger'}
        else:
            return super(AgilentMH, self).trace(name, twin=twin)

        if not op.exists(fname) or not op.exists(fname[:-3] + '.cg'):
            # file doesn't exist, kick it up to the parent
            return super(AgilentMH, self).trace(name, twin=twin)

        f = open(fname, 'rb')
        fdat = open(fname[:-3] + '.cg', 'rb')

        # convenience function for reading in data
        rd = lambda st: struct.unpack(st, f.read(struct.calcsize(st)))

        f.seek(0x4c)
        num_traces = rd('<I')[0]
        for _ in range(num_traces):
            cloc = f.tell()
            f.seek(cloc + 2)
            sl = rd('<B')[0]
            trace_name = rd('<' + str(sl) + 's')[0]
            if ttab[name] == trace_name:
                f.seek(f.tell() + 4)
                foff = rd('<Q')[0]
                npts = rd('<I')[0] + 2  # +2 for the extra time info
                fdat.seek(foff)
                pts = struct.unpack('<' + npts * 'd', fdat.read(8 * npts))
                #TODO: pts[0] is not the true offset?
                t = pts[0] + pts[1] * np.arange(npts - 2)
                d = np.array(pts[2:])
                # get the units
                f.seek(f.tell() + 40)
                sl = rd('<B')[0]
                y_units = rd('<' + str(sl) + 's')[0]
                if y_units == 'bar':
                    d *= 0.1  # convert to MPa for metricness
                elif y_units == '':
                    pass  # TODO: ul/min to ml/min
                return Series(d, t, name=name)

            f.seek(cloc + 87)


class AgilentCS(TraceFile):
    """
    Base class for Agilent files from ChemStation.
    """
    @property
    def info(self):
        folder = op.dirname(self.filename)
        d = super(AgilentCS, self).info
        pmp_file = op.join(folder, 'RUN.M', 'LPMP1.REG')
        if op.exists(pmp_file):
            fd = read_reg_file(open(pmp_file, 'rb'))
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

    def events(self, kind):
        evts = super(AgilentCS, self).events(kind)
        if kind in ('fia', 'fxn'):
            folder = op.dirname(self.filename)
            if kind == 'fia':
                acq_file = op.join(folder, 'ACQRES.REG')
            elif kind == 'fxn':
                acq_file = op.join(folder, 'LAFC1FD.REG')

            if not op.exists(acq_file):
                return {}
            else:
                acq_file = open(acq_file, 'rb')
            acq_file.seek(0x19)
            vers = acq_file.read(7)

        if kind == 'fia' and vers.startswith(b'A'):
            d = read_reg_file(acq_file)
            if not d.get('FIARun', False):
                return {}
            prev_f = d['FIASeriesInfo'][1][1]
            for f in d['FIASeriesInfo'][1][2:]:
                evts.append([prev_f[0], f[0], {'name': prev_f[2]}])
                prev_f = f
            else:
                if len(evts) > 0:
                    off_t = evts[-1][1] - evts[-1][0]
                    evts.append([prev_f[0], prev_f[0] + off_t, \
                                    {'name': prev_f[2]}])
        elif kind == 'fia' and vers == b'notused':
            #TODO: get fia from new-style *.REG files.
            pass
        elif kind == 'fxn' and vers.startswith(b'A'):
            #TODO: get fxn from old-style *.REG files.
            pass
        elif kind == 'fxn' and vers == b'notused':
            acq_file.seek(0xED)
            nfxns = struct.unpack('<I', acq_file.read(4))[0]
            acq_file.seek(0x33F)
            evts = []
            for _ in range(nfxns):
                d = struct.unpack('<Q9fI4f7I', acq_file.read(92))
                evts.append([d[13] / 60000., d[14] / 60000., {}])

            acq_file.seek(acq_file.tell() + 264)
            for i in range(nfxns):
                slen = struct.unpack('<H', acq_file.read(2))[0] - 1
                evts[i][2]['name'] = acq_file.read(2 * slen).decode('utf-16')
        return evts

    def trace_names(self, named):
        if named:
            names = ['pres', 'flow', 'slva', 'slvb', 'slvc', 'slvd',
                     'temp']
        else:
            names = []
        return super(AgilentCS, self).trace_names(named) + names

    def trace(self, name='', twin=None):
        #TODO: use twin
        #TODO: read info from new style REG files
        rf = op.join(op.dirname(self.filename), 'LCDIAG.REG')
        if name in ['pres', 'flow', 'slva', 'slvb', 'slvc', 'slvd']:
            t = {'pres': 'PMP1, Pressure', 'flow': 'PMP1, Flow',
                 'slva': 'PMP1, Solvent A', 'slvb': 'PMP1, Solvent B',
                 'slvc': 'PMP1, Solvent C', 'slvd': 'PMP1, Solvent D'}
            df = read_multireg_file(open(rf, 'rb'), title=t[name])
            ts = df['TimeSeries']
            ts.ions = [name]
            return ts
        else:
            return super(AgilentCS, self).trace(name, twin=twin)


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
    rd = lambda st: struct.unpack(st, f.read(struct.calcsize(st)))

    f.seek(0x19)
    if f.read(1) != b'A':
        #raise TypeError("Version of REG file is too new.")
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
            #except:
            #    pass
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
                cols = [struct.unpack('<16sHHHHHI', \
                        d[20 + 30 * i:50 + 30 * i])
                        for i in range(ncol)]
                colnames = [c[0].split(b'\x00')[0].decode('iso8859')
                            for c in cols]
                # TODO: type 2 is not a constant size? 31, 17
                rty2sty = {1: 'H', 3: 'I', 4: 'f', 5: 'H', \
                           7: 'H', 8: 'd', 11: 'H', 12: 'H', \
                           13: 'I', 14: 'I', 16: 'H'}
                coltype = '<' + ''.join([rty2sty.get(c[3], \
                  str(c[2]) + 's') for c in cols])
                lencol = struct.calcsize(coltype)
                tab = []
                for i in reversed(range(2, nrow + 2)):
                    rawrow = struct.unpack(coltype, \
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

            #x_units = names.get(m[8], '')
            x_arr = m[14] * names.get(m[9], np.arange(nrecs - 1))
            y_arr = m[25] * names.get(m[20])
            y_units = names.get(m[19], '')
            if y_units == 'bar':
                y_arr *= 0.1  # convert to MPa
            #TODO: what to call this?
            data['TimeSeries'] = Series(y_arr, x_arr, name='')
        #elif r[1] == 1025:  # b'0104'
        #    # lots of zeros? maybe one or two numbers?
        #    # only found in REG entries that have long 0280 records
        #    fm = '<HQQQIHHHHIIHB'
        #    m = struct.unpack(fm, d)
        #    print(m)
        #    #print(r[1], len(d), binascii.hexlify(d))
        #    pass
        #elif r[1] == 512:  # b'0002'
        #    # either points to two null pointers or two other pointers
        #    # (indicates start of linked list?)
        #    print(r[1], len(d), binascii.hexlify(d))
        #elif r[1] == 769 or r[1] == 772:  # b'0103' or b'0403'
        #    # points to 2nd, 3rd & 4th records (two 0002 records and a 0180)
        #    b = binascii.hexlify
        #    print(b(d[10:14]), b(d[14:18]), b(d[18:22]))

    return data


def read_regb_file(f):
    pass
    #CObArray
    #either 2 bytes long (0100) or 8 (0000 0380 0580 XXXX)

    #CHPAnnText
    #[j[36:36+2*struct.unpack('<H', j[34:36])[0]].decode('utf-16') \
    # for i, j in a if i == b'CHPAnnText']
    #slen = struct.unpack('<H', struct_dat[34:36])
    #struct_dat[36:36 + slen * 2].decode('utf-16')

    #CHPDatLongRow
    # starts at byte 14?

    #CHPNdrString
    #[j[12:12 + 2 * struct.unpack('<H', j[10:12])[0]].decode('utf-16') \
    # for i, j in a if i == b'CHPNdrString']

    #CHPNdrObject

    #CHPTable
