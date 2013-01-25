import json
import numpy as np
from aston.Features.DBObject import DBObject
import aston.Math.Peak as peakmath
from aston.Features.Spectrum import Spectrum
from aston.TimeSeries import TimeSeries
from aston.Math.Other import delta13C
from aston.Math.PeakModels import fit_to
from aston.Math.PeakModels import peak_models

peak_models = dict([(pm.__name__, pm) for pm in peak_models])


class Peak(DBObject):
    def __init__(self, *args, **kwargs):
        super(Peak, self).__init__('peak', *args, **kwargs)

    @property
    def data(self):
        if 'p-model' not in self.info:
            return self.rawdata

        f = peak_models.get(self.info['p-model'], None)
        if f is None:
            return self.rawdata
        #TODO: if p-params is a list, plot each item as current
        #p-params; allow for multiple functions to fit one peak

        times = self.rawdata.times[1:-1]
        p = json.loads(self.info['p-params'])
        y = f(times, **p)
        #y[0] = self.rawdata.data[0, 0]
        #y[-1] = self.rawdata.data[-1, 0]
        return TimeSeries(y, times, ['X'])

    def time(self, twin=None):
        return self.rawdata.trace('!', twin=twin).time

    def trace(self, ion='!', twin=None):
        return self.rawdata.trace(ion, twin=twin).y

    def _load_info(self, fld):
        if fld == 's-mzs':
            ions = self.data.ions
            if len(ions) < 10:
                self.info[fld] = ','.join(str(i) for i in ions)
            else:
                # only display a range of the numeric ions
                ions = [i for i in ions \
                  if type(i) is int or type(i) is float]
                if len(ions) > 0:
                    self.info['s-mzs'] = str(min(ions)) + '-' + str(max(ions))
        elif fld == 'p-s-area':
            self.info[fld] = str(self.area('!'))
        elif fld == 'p-s-length':
            self.info[fld] = str(peakmath.length(self.as_poly()))
        elif fld == 'p-s-height':
            self.info[fld] = str(peakmath.height(self.as_poly()))
        elif fld == 'p-s-time':
            self.info[fld] = str(peakmath.time(self.as_poly()))
        elif fld == 'p-s-pwhm':
            self.info[fld] = str(peakmath.length(self.as_poly(), pwhm=True))

    def _calc_info(self, fld):
        if fld == 'p-s-pkcap':
            prt = self.getParentOfType('file')
            if prt is None:
                return ''
            t = float(prt.getInfo('s-peaks-en')) - \
                float(prt.getInfo('s-peaks-st'))
            return str(t / peakmath.length(self.as_poly()) + 1)
        elif fld == 'sp-d13c':
            return self.d13C()
            #spcs = self.getAllChildren('spectrum')
            #if len(spcs) > 0:
            #    return spcs[0].d13C()
        return ''

    def contains(self, x, y):
        return peakmath.contains(self.as_poly(), x, y)

    def as_poly(self, ion=None):
        if ion is None:
            row = 0
        elif ion not in self.data.ions:
            row = 0
        else:
            row = self.data.ions.index(ion)
        return np.vstack([self.data.times, self.data.data.T[row]]).T

    def area(self, ion=None):
        if ion == '!':
            return peakmath.area(self.as_poly())
        elif ion not in self.data.ions:
            return 0
        else:
            return peakmath.area(self.as_poly(ion))

    def d13C(self):
        dt = self.getParentOfType('file')
        #TODO: not sure if we should do this or not
        # by not doing it, we can show relative error
        # between standard peaks
        #if self.info['p-type'] == 'Isotope Standard':
        #    return dt.info['r-d13c-std']

        # if there's no reference number, we can't do this
        try:
            float(dt.info['r-d13c-std'])
        except:
            return ''

        r45std = dt.get_point('r45std', peakmath.time(self.as_poly(44)))
        r46std = dt.get_point('r46std', peakmath.time(self.as_poly(44)))

        # if no peak has been designated as a isotope std
        if r45std == 0.0:
            return ''

        i44, i45, i46 = self.area(44), self.area(45), self.area(46)
        # if one of the areas is 0, clearly there's a problem
        if i44 * i45 * i46 == 0:
            return ''
        d = delta13C(i45 / i44, i46 / i44, \
          float(dt.info['r-d13c-std']), r45std, r46std)
        return '{0:.3f}'.format(d)

    def createSpectrum(self, method=None):
        prt = self.getParentOfType('file')
        time = peakmath.time(self.as_poly())
        if method is None:
            data = prt.scan(time)
            #listify = lambda l: [float(i) for i in l]
            #data = listify(data[0]), listify(data[1])
        info = {'sp-time': str(time)}
        return Spectrum(self.db, None, self.db_id, info, data)

    def update_model(self, key):
        # TODO: the model should be applied to *all* of the
        # ions in self.rawdata
        t = self.rawdata.times[1:-1]
        x = self.rawdata.data[:, 0][1:-1]
        #xa = x[1:-1] - np.linspace(x[0], x[-1], len(x) - 2)
        self.info['p-model'] = str(key)

        f = peak_models.get(str(key), None)

        self.info.del_items('p-s-')
        if f is not None:
            #TODO: use baseline detection?
            params = fit_to(f, t, x)
            params['f'] = str(key)
            self.info['p-s-base'] = str(params['v'])
            self.info['p-s-height'] = str(params['h'])
            self.info['p-s-time'] = str(params['x'])
            self.info['p-s-width'] = str(params['w'])
            self.info['p-params'] = json.dumps(params)
