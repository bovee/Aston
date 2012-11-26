"""
This module acts as an intermediary between the Agilent, Thermo,
and other instrument specific classes and the rest of the program.
"""
#pylint: disable=C0103

import os.path as op
import numpy as np
from scipy.interpolate import interp1d
from scipy.optimize import leastsq
from aston.Features import DBObject
from aston.TimeSeries import TimeSeries


class Datafile(DBObject):
    """
    Generic chromatography data containter. This abstacts away
    the implementation details of the specific file formats.
    """
    def __init__(self, *args, **kwargs):
        super(Datafile, self).__init__('file', *args, **kwargs)
        #self._update_info_from_file()

        #make stubs for the time array and the data array
        self.data = None

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

    def trace(self, ion=None, twin=None):
        """
        Returns an array, either time/ion filtered or not
        of chromatographic data.
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
        #TODO: better error checking in here?

        #null case
        if istr.strip() == '':
            return self._const(0, twin)

        #remove any parantheses or pluses around the whole thing
        istr = istr.lstrip('+(').rstrip(')')

        #invert it if preceded by a minus sign
        if istr[0] == '-':
            ts = self._parse_ion_string(istr[1:], twin)
            return -ts

        #this is a function
        if istr[:istr.find('(')].isalnum() and istr.find('(') != -1:
            fxn = istr[:istr.find('(')]
            if fxn == 'file' or fxn == 'f':
                args = istr[istr.find('(') + 1:].split(';')
                dt = self.database.getFileByName(args[0])
                if dt is None:
                    return self._const(0, twin)
                if len(args) > 1:
                    ts = dt.trace(args[1], twin=twin)
                else:
                    ts = dt.trace(twin=twin)
                return ts.retime(self.time(twin))
            else:
                args = istr[istr.find('(') + 1:].split(';')
                ts = self._parse_ion_string(args[0], twin)
                return self._apply_fxn(ts, fxn, *args[1:])

        #have we simplified enough? is all of the tricky math gone?
        if set(istr).intersection(set('+-/*()')) == set():
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

        #parse out the additive parts
        ts = self._const(0, twin)
        pa = ''
        for i in istr:
            if i in '+-' and pa[-1] not in '*/+' and \
              pa.count('(') == pa.count(')'):
                ts += self._parse_ion_string(pa, twin)
                pa = ''
            pa += i

        if pa != istr:
            return ts + self._parse_ion_string(pa, twin)

        #TODO: exponents?

        #no additive parts, parse multiplicative/divisive parts
        ts = None
        pa = ''
        for i in istr:
            if i in '*/' and pa.count('(') == pa.count(')'):
                if ts is None:
                    ts = self._parse_ion_string(pa, twin)
                elif pa[0] in '*':
                    ts *= self._parse_ion_string(pa[1:], twin)
                elif pa[0] in '/':
                    ts /= self._parse_ion_string(pa[1:], twin)
                pa = ''
            pa += i

        if pa[0] in '*':
            return ts * self._parse_ion_string(pa[1:], twin)
        elif pa[0] in '/':
            return ts / self._parse_ion_string(pa[1:], twin)
        else:
            return 0  # this should never happen?

    def _named_trace(self, name, twin=None):
        t = self.time(twin, adjust=False)
        lookdict = {'temp': 'm-tmp', 'pres': 'm-prs', 'flow': 'm-flw'}
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
            if name == 'r45std':
                topion = 45
            else:
                topion = 46
            std_specs = [o for o in \
              self.getAllChildren('spectrum') \
              if o.info['sp-type'] == 'Isotope Standard']
            x = [float(o.info['sp-time']) for o in std_specs]
            y = [o.ion(topion) / o.ion(44) for o in std_specs]

            if len(x) == 0:
                return self._const(0.0, twin)

            p0 = [y[0], 0]
            errfunc = lambda p, x, y: p[0] + p[1] * x - y
            try:
                p, succ = leastsq(errfunc, p0, args=(np.array(x), np.array(y)))
            except:
                p = p0
            return TimeSeries(np.array(errfunc(p, t, self._const(0.0))), t, [name])
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
                    return t, np.interp(t, x[srt_ind], \
                      y[srt_ind], float(tpts['S']))
                else:
                    return TimeSeries(np.interp(t, x[srt_ind], \
                      y[srt_ind]), t, [name])
            elif is_num(val):
                return self._const(float(val))
        else:
            return self._other_trace(name)

    def _apply_fxn(self, ts, fxn, *args):
        """
        Apply the function, fxn, to the trace, ic, and returns the result.
        """
        from aston.Math.Chromatograms import fxns as math_fxns

        if fxn in math_fxns:
            f = fxns[fxn]
            return ts.apply_fxn(f)
        return self._const(0.0)

    def get_point(self, trace, time):
        """
        Return the value of the trace at a certain time.
        """
        time = self._sc_off(time)

        t = self.time()
        f = interp1d(*self.trace(trace), bounds_error=False, \
          fill_value=0.0)
        return f(t)

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
        elif fld == 's-time-st' or fld == 's-time-en':
            time = self.time()
            self.info['s-time-st'] = str(min(time))
            self.info['s-time-en'] = str(max(time))
        elif fld == 's-peaks' or fld == 's-spectra':
            self.info['s-peaks'] = len(self.getAllChildren('peak'))
            self.info['s-spectra'] = len(self.getAllChildren('spectrum'))
        elif fld == 's-peaks-st' or fld == 's-peaks-en':
            pks = self.getAllChildren('peak')
            if len(pks) > 0:
                times = [float(pk.info['p-s-time']) for pk in pks]
                self.info['s-peaks-st'] = str(min(times))
                self.info['s-peaks-en'] = str(max(times))
        elif fld == 's-mz-min' or fld == 's-mz-max':
            ions = np.array([i for i in self._ions() \
                             if type(i) is int or type(i) is float])
            self.info['s-mz-min'] = str(min(ions))
            self.info['s-mz-max'] = str(max(ions))
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

        return self.data.scan(self._sc_off(time))

    def _const(self, val, twin=None):
        """
        Return a TimeSeries with the times of the current
        chromatogram, but constant values of val.
        """
        if self.data is None:
            self._cache_data()

        if twin is not None:
            twin = (self._sc_off(twin[0]), self._sc_off(twin[1]))

        return TimeSeries(val * np.ones(self.data.len(twin)), \
          self.time(twin, adjust=False), ['!' + str(val)])

    def _ions(self):
        if self.data is None:
            self._cache_data()

        return self.data.ions

    def as_2D(self, twin=None):
        """
        Returns a array summarizing all of the data.
        """
        return self.data.as_2D()

    def _total_trace(self, twin=None):
        """
        Return the default, total trace.
        """
        #Note: it's useful to override this to speed up
        #display of the TIC if it can be calculated easily.
        if self.data is None:
            self._cache_data()

        return self.data.trace(twin=twin)

    def _ion_trace(self, val, tol=0.5, twin=None):
        """
        Return a specific ion trace from the data.
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

    def _cache_data(self):
        """
        Load the data into the Datafile for the first time.
        """
        if self.data is None:
            self.data = TimeSeries()

    def _update_info_from_file(self):
        """
        Return file information.
        """
        pass
