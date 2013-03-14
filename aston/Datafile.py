#    Copyright 2011-2013 Roderick Bovee
#
#    This file is part of Aston.
#
#    Aston is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Aston is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Aston.  If not, see <http://www.gnu.org/licenses/>.

"""
This module allows Agilent, Thermo, and other instrument
specific file formats to be accessed through the same
interface.
"""

import os.path as op
import numpy as np
from scipy.interpolate import interp1d
from scipy.optimize import leastsq
from aston.Features import DBObject
from aston.TimeSeries import TimeSeries
from aston.FileFormats.FileFormats import get_magic, ftype_to_class
from aston.FileFormats.FileFormats import ext_to_classtable


class Datafile(DBObject):
    """
    Generic chromatography data containter. This abstacts away
    the implementation details of the specific file formats.

    An example of its usage:
    >>> from aston.Datafile import Datafile
    >>> from matplotlib.pyplot import plot, show
    >>> dt = Datafile('/path/to/filename.csv')
    >>> ts = dt.trace('TIC')
    >>> plot(ts.times, ts.y)
    >>> show()
    """
    def __init__(self, *args, **kwargs):
        if len(args) == 1:
            # this section allows Datafiles to be used outside of
            # the UI
            fname = args[0]
            ext2ftype = ext_to_classtable()
            ext, magic = get_magic(fname)

            ftype = None
            if magic is not None:
                ftype = ext2ftype.get(ext + '.' + magic, None)
            if ftype is None:
                ftype = ext2ftype.get(ext, None)
            info = {'s-file-type': ftype}
            args = []
            kwargs['info'] = info
            kwargs['data'] = fname
            autoload = True
        else:
            autoload = False

        super(Datafile, self).__init__(*args, **kwargs)
        self.db_type = 'file'
        self.childtypes = ('peak', 'peakgroup', 'spectrum')
        self.data = None

        if autoload:
            # preload everything
            self.__class__ = ftype_to_class(ftype)
            self._cache_data()
            self._update_info_from_file()

    def _sc_off(self, t):
        """
        Scale and offset a time.
        """
        if t is None:
            return None
        else:
            scale = float(self.info.get('t-scale', 1.0))
            offset = float(self.info.get('t-offset', 0.0))
            return (t - offset) / scale

    def active_traces(self, n=None, all_tr=False, twin=None):
        """
        Returns TimeSeries for some subset of ions.

        If all_tr is True, return all TimeSeries in self,
        otherwise return the 'n'th trace specified in the 'traces'
        property; if n is None, then return all traces in the 'traces'
        property.
        """
        if all_tr:
            ions = self._ions()
        else:
            ions = self.info['traces'].split(',')
            ions = [i.strip() for i in ions]

        if n is not None:
            if n > len(ions):
                return []
            else:
                ts = self.trace(ions[n], twin=twin)
                ts.ions[0] = ions[n]
                return [ts]
        else:
            tss = []
            for ion in ions:
                ts = self.trace(ion, twin=twin)
                ts.ions[0] = ion
                tss += [ts]
            return tss

    def trace(self, ion=None, twin=None):
        """
        Returns a TimeSeries object derived from this Datafile.

        Example 'ions's:
            "TIC" or "X": sum of all of mzs/wavelengths
            "280": either the trace at 280 nm or mz 280
            "X/!2": half of the TIC trace
            "SIN(X)": sin of the TIC trace
        twin is a tuple of the range of the trace to return.
        """
        if twin is not None:
            twin = (self._sc_off(twin[0]), self._sc_off(twin[1]))

        if type(ion) == str or type(ion) == unicode:
            ts = self._parse_ion_string(ion.lower(), twin)
        elif type(ion) == int or type(ion) == float:
            #if the ion is a number, do the straightforward thing
            ts = self._ion_trace(ion, twin=twin)
        else:
            #all other cases, just return the total trace
            ts = self._total_trace(twin=twin)

        if 't-yscale' in self.info:
            ts *= float(self.info['t-yscale'])
        if 't-yoffset' in self.info:
            ts += float(self.info['t-yoffset'])

        if 'remove noise' in self.info:
            #TODO: LOESS (local regression) filter
            pass

        if 't-smooth' in self.info:
            if self.info['t-smooth'].lower() == 'moving average':
                wnd = self.info['t-smooth-window']
                if wnd.isdigit():
                    ts = self._apply_fxn(ts, 'movingaverage', wnd)
            elif self.info['t-smooth'].lower() == 'savitsky-golay':
                wnd = self.info['t-smooth-window']
                sord = self.info['t-smooth-order']
                if wnd.isdigit() and sord.isdigit():
                    ts = self._apply_fxn(ts, 'savitskygolay', wnd, sord)

        offset = float(self.info.get('t-offset', 0.0))
        scale = float(self.info.get('t-scale', 1.0))
        return ts.adjust_time(offset, scale)

    def _parse_ion_string(self, istr, twin=None):
        """
        Recursive string parser that handles "ion" strings.
        """
        def tokenize(istr, token):
            plevel, words, sacc = 0, [], ''
            for s in istr.split(token):
                plevel += sum(1 for i in s if i == '(')
                plevel -= sum(1 for i in s if i == ')')
                if sacc == '':
                    sacc += s
                else:
                    sacc += token + s
                if plevel == 0:
                    words.append(sacc.strip())
                    sacc = ''
            if sacc != '':
                words.append(sacc.strip())
            return words

        def is_parans_exp(istr):
            fxn = istr.split('(')[0]
            if (not fxn.isalnum() and fxn != '(') or istr[-1] != ')':
                return False
            plevel = 1
            for c in '('.join(istr[:-1].split('(')[1:]):
                if c == '(':
                    plevel += 1
                elif c == ')':
                    plevel -= 1
                if plevel == 0:
                    return False
            return True

        if istr.strip() == '':
            return self._const(0, twin)

        #remove (unnessary?) pluses from the front
        #TODO: plus should be abs?
        istr = istr.lstrip('+')

        #invert it if preceded by a minus sign
        if istr[0] == '-':
            return -self._parse_ion_string(istr[1:], twin)

        #this is a function or paranthesized expression
        if is_parans_exp(istr):
            if ')' not in istr:
                # unbalanced parantheses
                pass
            fxn = istr.split('(')[0]
            args = istr[istr.find('(') + 1:istr.find(')')].split(';')
            if fxn == '':
                # strip out the parantheses and continue
                istr = args[0]  # istr[1:-1]
            elif fxn == 'file' or fxn == 'f':
                dt = self.database.getFileByName(args[0])
                if dt is None:
                    return self._const(0, twin)
                if len(args) > 1:
                    ts = dt.trace(args[1], twin=twin)
                else:
                    ts = dt.trace(twin=twin)
                return ts.retime(self.time(twin))
            else:
                ts = self._parse_ion_string(args[0], twin)
                return self._apply_fxn(ts, fxn, *args[1:])

        # all the complicated math is gone, so simple lookup
        if set(istr).intersection(set('+-/*()')) == set():
            return self._parse_simple_ion_string(istr, twin)

        # go through and handle operators
        for token in '/*+-^':
            if len(tokenize(istr, token)) != 1:
                ts = tokenize(istr, token)
                s = self._parse_ion_string(ts[0], twin)
                for t in ts[1:]:
                    if token == '/':
                        s /= self._parse_ion_string(t, twin)
                    elif token == '*':
                        s *= self._parse_ion_string(t, twin)
                    elif token == '+':
                        s += self._parse_ion_string(t, twin)
                    elif token == '-':
                        s -= self._parse_ion_string(t, twin)
                    elif token == '^':
                        s **= self._parse_ion_string(t, twin)
                return s
        #TODO: shouldn't hit this point?
        pass

    def _parse_simple_ion_string(self, istr, twin):
        if istr == 'x' or istr == 'tic':
            return self._total_trace(twin)
        elif istr.count(':') == 1:
            #contains an ion range
            #TODO: shouldn't this be:
            #ion = sum(float(i) for i in istr.split(':')) / 2.0
            ion = np.array([float(i) for i in istr.split(':')]).mean()
            tol = abs(float(istr.split(':')[0]) - ion)
            return self._ion_trace(ion, tol, twin=twin)
        elif all(i in '0123456789.' for i in istr):
            return self._ion_trace(float(istr), twin=twin)
        elif istr[0] == '!' and all(i in '0123456789.' for i in istr[1:]):
            #TODO: should this handle negative numbers?
            return self._const(float(istr[1:]), twin)
        elif istr == '!pi':
            return self._const(np.pi, twin)
        elif istr == '!e':
            return self._const(np.e, twin)
        else:
            return self._named_trace(istr, twin=twin)

    def _named_trace(self, name, twin=None):
        t = self.time(twin, adjust=False)
        lookdict = {'mtemp': 'm-tmp', 'mpres': 'm-prs', 'mflow': 'm-flw'}
        if name == 't' or name == 'time':
            return TimeSeries(t, t, [name])
        #elif name == 'b' or name == 'base':
        #    #TODO: create a baseline
        #    pass
        elif name == 'coda':
            # Windig W: The use of the Durbin-Watson criterion for
            # noise and background reduction of complex liquid
            # chromatography/mass spectrometry data and a new algorithm
            # to determine sample differences. Chemometrics and
            # Intelligent Laboratory Systems. 2005, 77:206-214.
            pass
        elif name == 'rnie':
            # Yunfei L, Qu H, and Cheng Y: A entropy-based method
            # for noise reduction of LC-MS data. Analytica Chimica
            # Acta 612.1 (2008)
            pass
        elif name == 'wmsm':
            # Fleming C et al. Windowed mass selection method:
            # a new data processing algorithm for LC-MS data.
            # Journal of Chromatography A 849.1 (1999) 71-85.
            pass
        elif name == 'r45std' or name == 'r46std':
            # calculate isotopic reference for chromatogram
            #from aston.Math.Peak import area
            if name == 'r45std':
                topion = 45
            else:
                topion = 46
            std_specs = [o for o in \
              self.children_of_type('peak') \
              if o.info['p-type'] == 'Isotope Standard']
            x = [float(o.info['p-s-time']) for o in std_specs]
            y = [o.area(topion) / o.area(44) for o in std_specs \
                 if o.area(44) != 0]
            if len(x) == 0 or len(y) == 0:
                return self._const(0.0, twin)

            p0 = [y[0], 0]
            errfunc = lambda p, x, y: p[0] + p[1] * x - y
            try:
                p, succ = leastsq(errfunc, p0, args=(np.array(x), np.array(y)))
            except:
                p = p0
            sim_y = np.array(errfunc(p, t, np.zeros(len(t))))
            return TimeSeries(sim_y, t, [name])
        elif name in lookdict:
            #we can store time-series data as a list of timepoints
            #in certain info fields and query it here
            def is_num(x):
                #stupid function to determine if something is a number
                try:
                    float(x)
                    return True
                except:
                    return False

            val = self.info[lookdict[name]]
            if ',' in val:
                #turn the time list into a dictionary
                tpts = dict([tpt.split(':') for tpt in \
                  self.info[lookdict[name]].split(',')])
                #get the valid times out
                valid_x = [v for v in tpts if is_num(v)]
                #generate arrays from them
                x = np.array([float(v) for v in valid_x])
                y = np.array([float(tpts[v]) for v in valid_x])
                srt_ind = np.argsort(x)
                if 'S' in tpts:
                    #there's a "S"tart value defined
                    return TimeSeries(np.interp(t, x[srt_ind], \
                      y[srt_ind], float(tpts['S'])), t, [name])
                else:
                    return TimeSeries(np.interp(t, x[srt_ind], \
                      y[srt_ind]), t, [name])
            elif is_num(val):
                return self._const(float(val))
            else:
                return self._const(np.nan)
        else:
            return self._other_trace(name)

    def _apply_fxn(self, ts, fxn, *args):
        """
        Apply the function, fxn, to the trace, ic, and returns the result.
        """
        from aston.Math.Chromatograms import fxns as math_fxns

        if fxn in math_fxns:
            f = math_fxns[fxn]
            return f(ts, *args)
        else:
            return self._const(np.nan)

    def get_point(self, trace, time):
        """
        Return the value of the trace at a certain time.
        """
        ts = self.trace(trace)
        f = interp1d(ts.times, ts.data.T, \
          bounds_error=False, fill_value=0.0)
        return f(self._sc_off(time))[0]

    def _load_info(self, fld):
        #create the key if it doesn't yet exist
        if fld == 'vis':
            self.info['vis'] = 'n'
        elif fld == 'r-filename':
            #TODO: generate this in Database on creation?
            #the filename used for display in the program.
            self.info[fld] = op.join(op.basename( \
              op.dirname(self.rawdata)), op.basename(self.rawdata))
        elif fld == 's-scans':
            self.info['s-scans'] = str(len(self.time()))
        elif fld == 's-mzs':
            # this isn't exactly the same as the code in Peak
            # because a datafile could inject another trace type
            # (i.e. pressure) into self._ions that's not in self.data
            ions = self._ions()
            if len(ions) < 10:
                self.info['s-mzs'] = ','.join(str(i) for i in ions)
            else:
                ions = [i for i in ions \
                  if type(i) is int or type(i) is float]
                if len(ions) > 0:
                    self.info['s-mzs'] = str(min(ions)) + '-' + str(max(ions))
        elif fld == 's-st-time' or fld == 's-en-time':
            self.info['s-st-time'] = str(min(self.time()))
            self.info['s-en-time'] = str(max(self.time()))
        elif fld == 's-peaks' or fld == 's-spectra':
            self.info['s-peaks'] = len(self.children_of_type('peak'))
            self.info['s-spectra'] = len(self.children_of_type('spectrum'))
        elif fld == 's-peaks-st' or fld == 's-peaks-en':
            pks = self.children_of_type('peak')
            if len(pks) > 0:
                times = [float(pk.info['p-s-time']) for pk in pks]
                self.info['s-peaks-st'] = str(min(times))
                self.info['s-peaks-en'] = str(max(times))
        else:
            pass

    #The follow functions only need to be rewritten in subclasses
    #if not using the TimeSeries object (i.e. in a large MSMS dataset)

    def time(self, twin=None, adjust=True):
        """
        Returns an array with all of the time points at which
        data was collected
        """
        #load the data if it hasn't been already
        if self.data is None:
            self._cache_data()

        if twin is not None:
            twin = (self._sc_off(twin[0]), self._sc_off(twin[1]))

        #return the time series
        t = self.data.time(twin)
        if adjust and 't-scale' in self.info:
            t *= float(self.info['t-scale'])
        if adjust and 't-offset' in self.info:
            t += float(self.info['t-offset'])
        return t

    def scan(self, time, to_time=None):
        """
        Returns the spectrum from a specific time.
        (or range of times if to_time is specified).
        """
        if self.data is None:
            self._cache_data()

        return self.data.scan(self._sc_off(time), to_time=to_time)

    def _const(self, val, twin=None):
        """
        Return a TimeSeries with the times of the current
        chromatogram, but constant values of val.
        """
        if self.data is None:
            self._cache_data()

        t = self.time(twin, adjust=False)
        return TimeSeries(val * np.ones(t.shape), t, ['!' + str(val)])

    def _ions(self):
        if self.data is None:
            self._cache_data()

        return self.data.ions

    def as_2D(self, twin=None):
        """
        Returns a tuple of ranges and a 2D array summarizing
        the data that can be plotted.
        """
        return self.data.as_2D()

    def _total_trace(self, twin=None):
        """
        Return the default, total trace. This is the
        sum of the individual traces.
        """
        #Note: it's useful to override this to speed up
        #display of the TIC if it can be calculated easily.
        if self.data is None:
            self._cache_data()

        return self.data.trace(twin=twin)

    def _ion_trace(self, val, tol=0.5, twin=None):
        """
        Return a specific mz/wavelength trace from the data.
        """
        if self.data is None:
            self._cache_data()

        return self.data.trace(val, tol, twin=twin)

    def _other_trace(self, name, twin=None):
        """
        Return a named trace, like pressure or temperature.
        """
        return self._const(0.0, twin=twin)

    #The following function stubs should be filled out in the
    #subclasses that handle the raw datafiles.

    def events(self, kind):
        """
        Returns events that happen during a run, like FIA injections
        or fraction collections windows. These happen at one (or over
        a range of) time.
        """
        return []

    def points(self):
        """
        Retuns an array of points, their intensity and an associated
        MZ for each. This is principally used for MSMS points right now.
        """
        return []

    def _cache_data(self):
        """
        Load the data into the Datafile for the first time.
        """
        if self.data is None:
            self.data = TimeSeries(np.array([]), np.array([]))

    def _update_info_from_file(self):
        """
        Loads my property "data" with a dictionary
        derived from method/run information in the file.
        """
        pass
