import os.path as op
import numpy as np
from scipy.sparse import lil_matrix
#from aston.Databases.Database import AstonDatabase
from aston.spectra.Spectrum import Spectrum
from aston.spectra.Math import find_spectrum_match


class AMDISDatabase(object):
    def __init__(self, database):
        self.database_path = database
        self._load_children()
        self._speclib = None

    def object_from_id(self, db_id, parent=None):
        pass

    def _load_children(self):
        def make_spc(arr_str, info):
            b = [int(i.strip('()')) for i in \
                    arr_str.split() if i.strip('()') != '']
            b = np.array(b)
            data = np.reshape(b, (b.shape[0] / 2, 2)).T
            return Spectrum(info, data)

        val_prt = lambda x: x.split(':')[1].lower().strip()

        self.children = []
        with open(self.database_path, 'r') as f:
            info, arr_str = {'name': val_prt(f.readline())}, ''
            for line in f:
                if line.startswith('('):
                    arr_str += line + ' '
                elif line.startswith('NAME:'):
                    spc = make_spc(arr_str, info)
                    self.children.append(spc)
                    info, arr_str = {'name': val_prt(line)}, ''
                elif line.startswith('RT:'):
                    info['p-s-time'] = val_prt(line)

    def get_children(self, obj):
        if obj is self:
            return self.children
        else:
            return []

    def find_spectrum(self, spc):
        if self._speclib is None:
            # build the speclib
            ions = set()
            for c in self.children:
                ions.update(c.data[0])
            self._ions = np.sort(np.array(list(ions)))
            self._names = []
            self._speclib = lil_matrix((len(self.children), len(ions)))
            for i, c in enumerate(self.children):
                self._names.append(c.info['name'])
                self._speclib[i, self._ions.searchsorted(c.data[0])] = \
                        c.data[1] / float(c.data[1].max())
        #TODO: this next part should be rewritted to be faster
        adj_spc = np.zeros(self._ions.shape)
        for ion, abn in spc.T:
            adj_spc[np.abs(self._ions - ion) < 0.5] += abn

        spec_num, dist = find_spectrum_match(adj_spc, self._speclib)

        #print(self.children[spec_num].info['name'], dist)
        if dist < 1:
            return self.children[spec_num]
        else:
            return None

        #pic = np.zeros((len(self.children), max(self._ions) + 1))
        #for abn, ion in zip(self._speclib.A.T, self._ions):
        #    pic[:, ion] = abn
        #from pylab import imshow, show
        #imshow(pic)
        #show()

        #from pylab import plot, show
        #plot(self._ions, self._speclib.A[spec_num], 'r.')
        #plot(self._ions, adj_spc / np.sum(adj_spc), 'k.')
        #spc[1] = spc[1] / np.sum(spc[1])
        #plot(spc[0], spc[1], 'k.')
        #show()

    # following don't need to be implemented yet
    def __enter__(self):
        pass

    def __exit__(self, type, value, traceback):
        pass

    def all_keys(self):
        return {}

    def get_key(self, key, dflt=''):
        return dflt

    def set_key(self, key, val):
        return

    def save_object(self, obj):
        return False

    def delete_object(self, obj):
        return False


class AstonCompoundDatabase(object):
    def __init__(self, database):
        #TODO: not implemented yet
        self.database_path = database
        self.children = []

    def get_key(self, key, dflt=''):
        return dflt


def get_compound_db(filename):
    ext = op.splitext(filename)[1].lower()
    if ext == '.msl':
        cmpd_db = AMDISDatabase(filename)
    elif ext == '.sqlite':
        cmpd_db = AstonCompoundDatabase(filename)
    else:
        return None
    return cmpd_db

