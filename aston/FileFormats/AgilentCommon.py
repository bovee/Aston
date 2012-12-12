# -*- coding: utf-8 -*-
import struct
import os.path as op
from xml.etree import ElementTree
import numpy as np


def read_chemstation_info(folder):
    d = {}
    try:
        pass
    except TypeError:
        pass
    pass


def read_reg_file(f):
    # convenience function for reading in data
    rd = lambda st: struct.unpack(st, f.read(struct.calcsize(st)))

    f.seek(0x2D)
    nrecs = rd('<I')[0]  #TODO: should be '<H'
    if nrecs == 0:
        raise TypeError("Version of REG file is too new.")
    rec_tab = [rd('<HHIII') for n in range(nrecs)]

    f.seek(0x31 + 20 * nrecs)
    data = {}
    table_names = {}
    for r in rec_tab:
        d = f.read(r[2])
        if r[1] == 1538:  # '0206'
            # this is part of a linked list
            if len(d) == 43:
                cd = struct.unpack('<HIII21sd', d)
                data[cd[4].decode('ascii').strip('\x00')] = cd[5]
            else:
                pass
        elif r[1] == 1539:  # '0306'
            # this is part of the linked list too, but contains a
            # reference to a table
            cd = struct.unpack('<HIII21sI', d)
            table_names[cd[5]] = cd[4].decode('ascii').strip('\x00')
        elif r[1] == 1793:  # b'0107'
            #try:
            #TODO: doesn't work on tables that contain text
            nrow = struct.unpack('<H', d[4:6])[0]
            ncol = struct.unpack('<H', d[16:18])[0]
            if nrow * ncol != 0:
                colnamelocs = [slice(20 + 30 * i, 36 + 30 * i)
                               for i in range(ncol)]
                colnames = [d[i].split(b'\x00')[0].decode('ascii')
                            for i in colnamelocs]
                tab = struct.unpack('f' * nrow * ncol,
                                    d[-4 * nrow * ncol:])
                data[table_names[r[4]]] = \
                    [colnames, np.array(tab).reshape((nrow, ncol))]
            #except:
            #    pass
        elif r[1] == 32774:  # b'0680'
            #TODO: these are strings referenced in tables
            #print(d[2:-1].decode('ascii'))
            pass
    return data


def read_new_reg_file(f):
    pass


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

    return d
