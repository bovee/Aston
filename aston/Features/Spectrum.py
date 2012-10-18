import math
from aston.Database import DBObject

class Spectrum(DBObject):
    def __init__(self, *args, **kwargs):
        super(Spectrum, self).__init__('spectrum', *args, **kwargs)

    @property
    def data(self):
        return self.rawdata

    def _calcInfo(self, fld):
        if fld == 'sp-d13c':
            return self.d13C()
        else:
            return ''

    def ion(self, ion):
        lst = dict(zip(*self.data))
        for i in lst:
            if abs(float(i) - ion) < 1:
                return float(lst[i])
        return None

    def d13C(self):
        dt = self.getParentOfType('file')
        if self.getInfo('sp-type') == 'Isotope Standard':
            return dt.getInfo('r-d13c-std')

        r45std = dt.get_point('r45std', float(self.getInfo('sp-time')))
        r46std = dt.get_point('r45std', float(self.getInfo('sp-time')))

        A, K = 0.5164, 0.0092
        rcpdb, rosmow = 0.011237, 0.002005

        #known delta values for the peak
        r13std = (float(dt.getInfo('r-d13c-std')) / 1000. + 1) * rcpdb
        r18std = (0 / 1000. + 1) * rosmow  # approx. - shouldn't affect results much

        #determine the correction factors
        c45 = (r13std + 2*K*r18std**A) / r45std
        c46 = ((K*r18std**A)**2 + 2*r13std*K*r18std**A + 2*r18std)/r46std

        #correct the voltage ratios to ion ratios
        r45 = c45 * self.ion(45) / self.ion(44)
        r46 = c46 * self.ion(46) / self.ion(44)

        r18 = rosmow #best guess for oxygen ratio (VSMOW value)
        #newton's method to find 18/17O
        for _ in range(4):
            r18 -= (-3*(K*r18**A)**2 + 2*K*r45*r18**A + 2*r18 - r46) / \
                   (-6*A*K**2*r18**(2*A-1) + 2*A*K*r45*r18**(A-1) + 2)
        r13 = r45 - 2 * K * r18 ** A
        return str(1000 * (r13 / rcpdb - 1))
