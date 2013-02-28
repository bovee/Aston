import zlib
import numpy as np
from aston.Features.DBObject import DBObject
from aston.Math.Other import delta13C_Santrock


class Spectrum(DBObject):
    def __init__(self, *args, **kwargs):
        super(Spectrum, self).__init__(*args, **kwargs)
        self.db_type = 'spectrum'

    @property
    def data(self):
        return self.rawdata

    def _calc_info(self, fld):
        if fld == 'sp-d13c':
            return self.d13C()
        else:
            return ''

    def compress(self):
        d = zlib.compress(self.rawdata.T.astype(float).tostring())
        try:  # python 2
            return buffer(d)
        except NameError:  # python 3
            return d

    def ion(self, ion):
        lst = dict(self.data.T)
        for i in lst:
            if abs(float(i) - ion) < 1:
                return float(lst[i])
        return None

    def d13C(self):
        dt = self.getParentOfType('file')
        if self.info['sp-type'] == 'Isotope Standard':
            return dt.info['r-d13c-std']

        # if there's no reference number, we can't do this
        try:
            float(dt.info['r-d13c-std'])
        except:
            return ''

        r45std = dt.get_point('r45std', float(self.info['sp-time']))
        r46std = dt.get_point('r46std', float(self.info['sp-time']))

        # if no peak has been designated as a isotope std
        if r45std == 0.0:
            return ''

        d = delta13C_Santrock(self.ion(44), self.ion(45), self.ion(46), \
                 float(dt.info['r-d13c-std']), r45std, r46std)

        return str(d)


def decompress_to_spec(zdata):
    return np.fromstring(zlib.decompress(zdata)).reshape((-1,2)).T
