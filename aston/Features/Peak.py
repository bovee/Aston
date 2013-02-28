import json
import numpy as np
from aston.Features.DBObject import DBObject
import aston.Math.Peak as peakmath
from aston.Features.Spectrum import Spectrum
from aston.TimeSeries import TimeSeries
from aston.Math.Other import delta13C_Santrock, delta13C_Craig
from aston.Math.PeakFitting import fit, guess_initc
from aston.Math.PeakModels import peak_models

peak_models = dict([(pm.__name__, pm) for pm in peak_models])


class Peak(DBObject):
    def __init__(self, *args, **kwargs):
        super(Peak, self).__init__(*args, **kwargs)
        self.db_type = 'peak'

    @property
    def data(self):
        if 'p-model' not in self.info:
            return self.rawdata

        f = peak_models.get(self.info['p-model'], None)
        if f is None:
            return self.rawdata
        #TODO: if p-params is a list, plot each item as current
        #p-params; allow for multiple functions to fit one peak

        p = json.loads(self.info['p-params'])
        y = f(self.rawdata.times, **p)
        return TimeSeries(y, self.rawdata.times, [self.rawdata.ions[0]])

    def baseline(self, ion=None, interp=False):
        if self.info['p-baseline'] == '':
            return None
        bases = json.loads(self.info['p-baseline'])
        new_bases = bases.copy()
        #TODO: incredibly hacky and slow
        for b in bases:
            try:
                new_bases[float(b)] = bases[b]
            except:
                pass
        if ion in new_bases:
            return np.array(new_bases[ion])
        else:
            return None

    def set_baseline(self, ion, value=None):
        if self.info['p-baseline'] == '':
            bases = {}
        else:
            bases = json.loads(self.info['p-baseline'])
        if value is None and str(ion) in bases:
            del bases[str(ion)]
        elif value is None:
            return
        else:
            assert type(value) == np.ndarray
        bases[str(ion)] = value.tolist()
        self.info['p-baseline'] = json.dumps(bases)

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
            prt = self.parent_of_type('file')
            if prt is None:
                return ''
            t = float(prt.info['s-peaks-en']) - \
                float(prt.info['s-peaks-st'])
            return str(t / peakmath.length(self.as_poly()) + 1)
        elif fld == 'p-s-d13c':
            return self.d13C()
        return ''

    def contains(self, x, y, ion=None):
        if not self.data.has_ion(ion):
            return False
        if self.info['p-s-time'] == '1.3236661911':
            print(self.info['p-baseline'], ion)
            print(peakmath.contains(self.as_poly(ion), x, y))
        return peakmath.contains(self.as_poly(ion), x, y)

    def as_poly(self, ion=None, sub_base=False):
        # add in the baseline on either side
        if ion is None:
            row = 0
        elif not self.data.has_ion(ion):
            row = 0
        else:
            try:
                row = self.data.ions.index(float(ion))
            except ValueError:
                row = self.data.ions.index(ion)
        pk = np.vstack([self.data.times, self.data.data.T[row]]).T
        base = self.baseline(ion)
        if sub_base:
            # this subtracts out the base line before returning it
            # it's useful for numerical fxns that don't take baseline
            if base is None:
                base_pts = np.interp(pk[:, 0], [pk[1, 0], pk[-1, 0]], \
                                     [pk[0, 1], pk[-1, 1]])
            else:
                base_pts = np.interp(pk[:, 0], *base)

            ply = np.array([pk[:, 0], pk[:, 1] - base_pts]).T
        elif base is None:
            ply = pk
        else:
            ply = np.vstack([base[0], pk, base[:0:-1]])
        return ply[np.logical_not(np.any(np.isnan(ply), axis=1))]

    def area(self, ion=None):
        if ion == '!':
            pk = self.as_poly() #sub_base=True)
        elif not self.data.has_ion(ion):
            return 0
        else:
            pk = self.as_poly(ion) #, sub_base=True)
        #if peakmath.area(pk, method='shoelace') / peakmath.area(pk, method='trapezoid') != 1:
        #    print(pk)
        return peakmath.area(pk)

    def d13C(self):
        dt = self.parent_of_type('file')
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

        calc_meth = self.db.get_key('d13c_method', dflt='santrock')
        consts = self.db.get_key('d13c_const', dflt='Santrock')

        r45std = dt.get_point('r45std', peakmath.time(self.as_poly(44)))
        r46std = dt.get_point('r46std', peakmath.time(self.as_poly(44)))

        # if no peak has been designated as a isotope std
        if r45std == 0.0:
            return ''

        i44, i45, i46 = self.area(44), self.area(45), self.area(46)
        # if one of the areas is 0, clearly there's a problem
        if i44 * i45 * i46 == 0:
            return ''
        if calc_meth == 'craig':
            d = delta13C_Craig(i45 / i44, i46 / i44, \
              float(dt.info['r-d13c-std']), r45std, r46std)
        else:
            d = delta13C_Santrock(i45 / i44, i46 / i44, \
              float(dt.info['r-d13c-std']), r45std, r46std,
              ks=consts)

        return '{0:.3f}'.format(d)

    def createSpectrum(self, method=None):
        prt = self.parent_of_type('file')
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
        self.info['p-model'] = str(key)
        self.info.del_items('p-s-')

        f = peak_models.get(str(key), None)
        if f is not None:
            t = self.rawdata.times
            y = self.rawdata.y
            #TODO: subtract baseline
            #ya = x[1:-1] - np.linspace(x[0], x[-1], len(x) - 2)

            ts = TimeSeries(y, t)
            initc = guess_initc(ts, f, [t[y.argmax()]])
            params, res = fit(ts, [f], initc)
            params = params[0]

            params['f'] = str(key)
            self.info['p-s-base'] = str(params['v'])
            self.info['p-s-height'] = str(params['h'])
            self.info['p-s-time'] = str(params['x'])
            self.info['p-s-width'] = str(params['w'])
            self.info['p-s-model-fit'] = str(res['r^2'])
            self.info['p-params'] = json.dumps(params)
