import struct
import numpy as np


def read_reg_file(f):
    # convenience function for reading in data
    rd = lambda st: struct.unpack(st, f.read(struct.calcsize(st)))

    f.seek(0x2D)
    nrecs = rd('<I')[0]
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
                colnamelocs = [slice(20 + 30 * i, 36 + 30 * i) for i in range(ncol)]
                colnames = [d[i].split(b'\x00')[0].decode('ascii') for i in colnamelocs]
                tab = struct.unpack('f' * nrow * ncol, d[-4 * nrow * ncol:])
                data[table_names[r[4]]] = [colnames, np.array(tab).reshape((nrow, ncol))]
            #except:
            #    pass
        elif r[1] == 32774:  # b'0680'
            #TODO: these are strings referenced in tables
            #print(d[2:-1].decode('ascii'))
            pass
    return data
