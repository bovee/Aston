import numpy as np
from aston.spectra.Scan import Scan


def read_AMDIS(filename):
    def make_spc(arr_str, info):
        b = [int(i.strip('()')) for i in \
                arr_str.split() if i.strip('()') != '']
        b = np.array(b)
        data = np.reshape(b, (b.shape[0] / 2, 2)).T
        return Scan(info, data)

    val_prt = lambda x: x.split(':')[1].lower().strip()

    with open(filename, 'r') as f:
        info, arr_str = {'name': val_prt(f.readline())}, ''
        for line in f:
            if line.startswith('('):
                arr_str += line + ' '
            elif line.startswith('NAME:'):
                spc = make_spc(arr_str, info)
                yield spc
                info, arr_str = {'name': val_prt(line)}, ''
            elif line.startswith('RT:'):
                info['p-s-time'] = val_prt(line)


def read_JCAMP(filename):
    raise NotImplementedError
