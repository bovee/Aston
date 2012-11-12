import numpy as np
from aston.Database import DBObject
import aston.Math.Peak as peakmath
from aston.Features.Spectrum import Spectrum


class Peak(DBObject):
    def __init__(self, *args, **kwargs):
        super(Peak, self).__init__('peak', *args, **kwargs)

    @property
    def data(self):
        if 'p-model' not in self.info:
            return np.array(self.rawdata)

        if self.info['p-model'] == 'Normal':
            f = peakmath.gaussian
        elif self.info['p-model'] == 'Lognormal':
            f = peakmath.lognormal
        elif self.info['p-model'] == 'Exp Mod Normal':
            f = peakmath.exp_mod_gaussian
        elif self.info['p-model'] == 'Lorentzian':
            f = peakmath.lorentzian
        else:
            return np.array(self.rawdata)

        times = np.array(self.rawdata)[:, 0]
        x0 = float(self.info['p-s-time'])
        y0 = float(self.info['p-s-base'])
        h = float(self.info['p-s-height'])
        s = [float(i) for i in self.info['p-s-shape'].split(',')]
        y = h * f(s, times - x0) + y0
        return np.column_stack((times, y))

    def time(self, st_time=None, en_time=None):
        return self._getTimeSlice(np.array(self.rawdata)[:, 0], \
                                  st_time, en_time)

    def trace(self, ion=None, st_time=None, en_time=None):
        #TODO: figure out if something should be done with the ion parameter
        return self._getTimeSlice(self.data[:, 1], st_time, en_time)

    def _getTimeSlice(self, arr, st_time=None, en_time=None):
        '''Returns a slice of the incoming array filtered between
        the two times specified. Assumes the array is the same
        length as self.data. Acts in the time() and trace() functions.'''
        tme = self.data[:, 0].copy()
        if st_time is None:
            st_idx = 0
        else:
            st_idx = (np.abs(tme - st_time)).argmin()
            if st_idx == 1:
                st_idx = 0
        if en_time is None:
            en_idx = self.data.shape[0]
        else:
            en_idx = (np.abs(tme - en_time)).argmin() + 1
            if en_idx == len(tme) - 1:
                en_idx = len(tme)
        return arr[st_idx:en_idx]

    def _load_info(self, fld):
        if fld == 'p-s-area':
            self.info[fld] = str(peakmath.area(self.data))
        elif fld == 'p-s-length':
            self.info[fld] = str(peakmath.length(self.data))
        elif fld == 'p-s-height':
            self.info[fld] = str(peakmath.height(self.data))
        elif fld == 'p-s-time':
            self.info[fld] = str(peakmath.time(self.data))
        elif fld == 'p-s-pwhm':
            self.info[fld] = str(peakmath.length(self.data, pwhm=True))

    def _calc_info(self, fld):
        if fld == 'p-s-pkcap':
            prt = self.getParentOfType('file')
            if prt is None:
                return ''
            t = float(prt.getInfo('s-peaks-en')) - \
                float(prt.getInfo('s-peaks-st'))
            return str(t / peakmath.length(self.data) + 1)
        elif fld == 'sp-d13c':
            spcs = self.getAllChildren('spectrum')
            if len(spcs) > 0:
                return spcs[0].d13C()
        return ''

    def contains(self, x, y):
        return peakmath.contains(self.data, x, y)

    def createSpectrum(self, method=None):
        prt = self.getParentOfType('file')
        time = peakmath.time(self.data)
        if method is None:
            data = prt.scan(time)
            listify = lambda l: [float(i) for i in l]
            data = [listify(data[0]), listify(data[1])]
        info = {'sp-time': str(time)}
        return Spectrum(self.db, None, self.db_id, info, data)

    def set_info(self, fld, key):
        if fld == 'p-model':
            d = np.array(self.rawdata)
            self.info['p-model'] = key
            if key == 'Normal':
                f = peakmath.gaussian
            elif key == 'Lognormal':
                f = peakmath.lognormal
            elif key == 'Exp Mod Normal':
                f = peakmath.exp_mod_gaussian
            elif key == 'Lorentzian':
                f = peakmath.lorentzian
            else:
                f = None

            self.delInfo('p-s-')
            if f is not None:
                params = peakmath.fit_to(f, d[:, 0], d[:, 1] - d[0, 1])
                self.info['p-s-time'] = str(params[0])
                self.info['p-s-height'] = str(params[1])
                self.info['p-s-base'] = str(d[0, 1])
                self.info['p-s-shape'] = ','.join([str(i) for i \
                                                       in params[2:]])
        super(Peak, self).set_info(fld, key)
