"""
This module acts as an intermediary between the Agilent, Thermo,
and other instrument specific classes and the rest of the program.
"""
#pylint: disable=C0103

import os.path as op
import numpy as np
from scipy.interpolate import interp1d
from scipy.optimize import leastsq
from aston.Database import DBObject
from aston.FileFormats.FileFormats import ftype_to_class
from aston.TimeSeries import TimeSeries


class Datafile(DBObject):
    """
    Generic chromatography data containter. This abstacts away
    the implementation details of the specific file formats.
    """
    def __new__(cls, db, db_id, parent_id, info, data):
        if 's-file-type' not in info:
            return None
        ncls = ftype_to_class(info['s-file-type'])
        args = (db, db_id, parent_id, info, data)
        return super(Datafile, cls).__new__(ncls, *args)

    def __init__(self, *args, **kwargs):
        super(Datafile, self).__init__('file', *args, **kwargs)
        #self._update_info_from_file()

        #make stubs for the time array and the data array
        self.data = None

    def trace(self, ion=None, twin=None):
        """
        Returns an array, either time/ion filtered or not
        of chromatographic data.
        """
        if type(ion) == str or type(ion) == unicode:
            t, ic = self._parse_ion_string(ion.lower(), twin)
        elif type(ion) == int or type(ion) == float:
            #if the ion is a number, do the straightforward thing
            t, ic = self._ion_trace(ion, twin=twin)
        else:
            #all other cases, just return the total trace
            t, ic = self._total_trace(twin=twin)

        if 't-yscale' in self.info:
            ic *= float(self.info['t-yscale'])
        if 't-yoffset' in self.info:
            ic += float(self.info['t-yoffset'])

        if 'remove noise' in self.info:
            #TODO: LOESS (local regression) filter
            pass

        if 't-smooth' in self.info:
            if self.info['t-smooth'].lower() == 'moving average':
                wnd = self.info['t-smooth-window']
                if wnd.isdigit():
                    t, ic = self._apply_fxn(t, ic, 'movingaverage', wnd)
            elif self.info['t-smooth'].lower() == 'savitsky-golay':
                wnd = self.info['t-smooth-window']
                sord = self.info['t-smooth-order']
                if wnd.isdigit() and sord.isdigit():
                    t, ic = self._apply_fxn(t, ic, 'savitskygolay', wnd, sord)

        return t, ic

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
            t, ic = self._parse_ion_string(istr[1:], twin)
            return t, -1.0 * ic

        #this is a function
        if istr[:istr.find('(')].isalnum() and istr.find('(') != -1:
            fxn = istr[:istr.find('(')]
            if fxn == 'file' or fxn == 'f':
                args = istr[istr.find('(') + 1:-1].split(';')
                dt = self.database.getFileByName(args[0])
                if dt is None:
                    return self._const(0, twin)
                if len(args) > 1:
                    ot, y = dt.trace(args[1], twin=twin)
                else:
                    ot, y = dt.trace(twin=twin)
                f = interp1d(ot, y, bounds_error=False, fill_value=0.0)
                return self.time(twin), f(t)
            else:
                args = istr[istr.find('(') + 1:-1].split(';')
                t, ic = self._parse_ion_string(args[0], twin)
                return t, self._apply_fxn(t, ic, fxn, *args[1:])

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

        #TODO: this should make sure that the ICs it's
        #manipulating have the same t axis or else adjust them

        #parse out the additive parts
        t, ic = self._const(0, twin)
        pa = ''
        for i in istr:
            if i in '+-' and pa[-1] not in '*/+' and \
              pa.count('(') == pa.count(')'):
                ic += self._parse_ion_string(pa, twin)[1]
                pa = ''
            pa += i

        if pa != istr:
            return t, ic + self._parse_ion_string(pa, twin)[1]

        #no additive parts, parse multiplicative/divisive parts
        ic = None
        pa = ''
        for i in istr:
            if i in '*/' and pa.count('(') == pa.count(')'):
                if ic is None:
                    ic = self._parse_ion_string(pa, twin)[1]
                elif pa[0] in '*':
                    ic *= self._parse_ion_string(pa[1:], twin)[1]
                elif pa[0] in '/':
                    ic /= self._parse_ion_string(pa[1:], twin)[1]
                pa = ''
            pa += i

        if pa[0] in '*':
            return t, ic * self._parse_ion_string(pa[1:], twin)[1]
        elif pa[0] in '/':
            return t, ic / self._parse_ion_string(pa[1:], twin)[1]
        else:
            return 0  # this should never happen?

    def _named_trace(self, name, twin=None):
        t = self.time(twin)
        lookdict = {'temp': 'm-tmp', 'pres': 'm-prs', 'flow': 'm-flw'}
        if name == 't' or name == 'time':
            return t, t
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
              if o.getInfo('sp-type') == 'Isotope Standard']
            x = [float(o.getInfo('sp-time')) for o in std_specs]
            y = [o.ion(topion) / o.ion(44) for o in std_specs]

            if len(x) == 0:
                return self._const(0.0, twin)

            p0 = [y[0], 0]
            errfunc = lambda p, x, y: p[0] + p[1] * x - y
            try:
                p, succ = leastsq(errfunc, p0, args=(np.array(x), np.array(y)))
            except:
                p = p0

            return t, np.array(errfunc(p, t, self._const(0.0)))
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

            val = self.getInfo(lookdict[name])
            if ',' in val:
                #turn the time list into a dictionary
                tpts = dict([tpt.split(':') for tpt in \
                  self.getInfo(lookdict[name]).split(',')])
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
                    return t, np.interp(t, x[srt_ind], y[srt_ind])
            elif is_num(val):
                return t, self._const(float(val))
        else:
            return self._other_trace(name)

    def _apply_fxn(self, t, ic, fxn, *args):
        """
        Apply the function, fxn, to the trace, ic, and returns the result.
        """
        #TODO: pass t into functions
        from aston.Math.Chromatograms import fxns
        if fxn in fxns:
            f = fxns[fxn]
            try:
                return t, f(ic, *args)
            except TypeError:
                pass
        return t, np.zeros(t.shape[0])

    def get_point(self, trace, time):
        """
        Return the value of the trace at a certain time.
        """
        t = self.time()
        f = interp1d(*self.trace(trace), \
          bounds_error=False, fill_value=0.0)
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
                times = [float(pk.getInfo('p-s-time')) for pk in pks]
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

    def time(self, twin=None):
        """
        Returns an array with all of the time points at which
        data was collected
        """
        #load the data if it hasn't been already
        #TODO: this should cache only the times (to speed up access
        #in case we're looking at something with the _total_trace)
        if self.data is None:
            self._cache_data()

        #return the time series
        return self.data.time(twin)

    def scan(self, time):
        """
        Returns the spectrum from a specific time.
        """
        if self.data is None:
            self._cache_data()

        return self.data.scan(time)

    def _const(self, val, twin=None):
        if self.data is None:
            self._cache_data()

        t = self.time(twin)
        return t, val * np.array(self.data.len(twin))

    def _ions(self):
        if self.data is None:
            self._cache_data()

        return self.data.ions

    #The following function stubs should be filled out in the
    #subclasses that handle the raw datafiles.

    def _cache_data(self):
        """
        Load the data into the Datafile for the first time.
        """
        if self.data is None:
            self.data = TimeSeries()

        if 't-offset' in self.info:
            self.data.offset = float(self.info['t-offset'])
        if 't-scale' in self.info:
            self.data.scale = float(self.info['t-scale'])

    def _update_info_from_file(self):
        """
        Return file information.
        """
        pass

    def _total_trace(self, twin=None):
        """
        Return the default, total trace.
        """
        if self.data is None:
            self._cache_data()

        return self.data.trace()

    def _ion_trace(self, val, tol=0.5, twin=None):
        """
        Return a specific ion trace from the data.
        """
        if self.data is None:
            self._cache_data()

        return self.data.trace(val, tol)

    def _other_trace(self, name, twin=None):
        """
        Return a named trace, like pressure or temperature.
        """
        return self.time(twin), self.data.const(0.0)

