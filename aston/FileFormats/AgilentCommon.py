# -*- coding: utf-8 -*-
import struct
import os.path as op
from xml.etree import ElementTree
from aston.Datafile import Datafile


class AgilentMH(Datafile):
    """
    Base class for Agilent files from Masshunter.
    """
    pass


class AgilentCS(Datafile):
    """
    Base class for Agilent files from ChemStation.
    """
    pass


def read_chemstation_info(folder):
    d = {}
    try:
        pass
    except TypeError:
        pass
    pass


def get_FIA(folder):
    #TODO: get fia from new-style *.REG files.
    d = read_reg_file(open(op.join(folder, 'ACQRES.REG'), 'rb'))
    if not d.get('FIARun', False):
        return []
    fis = []
    prev_f = d['FIASeriesInfo'][1][1]
    for f in d['FIASeriesInfo'][1][2:]:
        fis.append([prev_f[0], f[0], prev_f[2]])
        prev_f = f
    else:
        if len(fis) > 0:
            off_t = fis[-1][1] - fis[-1][0]
            fis.append([prev_f[0], prev_f[0] + off_t, prev_f[2]])
    return fis


def read_reg_file(f):
    """
    Given a file handle for an old-style Agilent *.REG file, this
    will parse that file into a dictonary of key/value pairs
    (including any tables that are in the *.REG file, which will
    be parsed into lists of lists).
    """
    # convenience function for reading in data
    rd = lambda st: struct.unpack(st, f.read(struct.calcsize(st)))

    f.seek(0x2D)
    nrecs = rd('<I')[0]  # TODO: should be '<H'
    if nrecs == 0:
        raise TypeError("Version of REG file is too new.")
    rec_tab = [rd('<HHIII') for n in range(nrecs)]

    names = {}
    f.seek(0x31 + 20 * nrecs)
    for r in rec_tab:
        d = f.read(r[2])
        if r[1] == 1539:  # '0306'
            # this is part of the linked list too, but contains a
            # reference to a table
            cd = struct.unpack('<HIII21sI', d)
            names[cd[5]] = cd[4].decode('iso8859').strip('\x00')
            #except:
            #    pass
        elif r[1] == 32774:  # b'0680'
            names[r[4]] = d[2:-1].decode('iso8859')
    #return names

    data = {}
    f.seek(0x31 + 20 * nrecs)
    for r in rec_tab:
        d = f.read(r[2])
        if r[1] == 1538:  # '0206'
            # this is part of a linked list
            if len(d) == 43:
                cd = struct.unpack('<HIII21sd', d)
                data[cd[4].decode('iso8859').strip('\x00')] = cd[5]
            else:
                pass
        elif r[1] == 1793:  # b'0107'
            #try:
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
                data[names[r[4]]] = \
                    [colnames, tab]
    return data


def parse_c_serialized(f):
    """
    Reads in a binary file created by a C++ serializer (prob. MFC?)
    and returns tuples of (header name, data following the header).
    These are used by Thermo for *.CF and *.DXF files and by Agilent
    for new-style *.REG files.
    """
    f.seek(0)
    try:
        p_rec_type = None
        while True:
            rec_off = f.tell()
            while True:
                if f.read(2) == b'\xff\xff':
                    h = struct.unpack('<HH', f.read(4))
                    if h[1] < 64 and h[1] != 0:
                        rec_type = f.read(h[1])
                        if rec_type[0] == 67:  # starts with 'C'
                            break
                if f.read(1) == b'':
                    raise EOFError
                f.seek(f.tell() - 2)
            if p_rec_type is not None:
                rec_len = f.tell() - 6 - len(rec_type) - rec_off
                f.seek(rec_off)
                yield p_rec_type, f.read(rec_len)
                f.seek(f.tell() + 6 + len(rec_type))
            p_rec_type, p_type = rec_type, h[0]
    except EOFError:
        rec_len = f.tell() - 6 - len(rec_type) - rec_off
        f.seek(rec_off)
        yield p_rec_type, f.read(rec_len)


def read_masshunter_info(folder):
    d = {}
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
