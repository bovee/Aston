"""
This module acts as an intermediary between the Agilent, Thermo,
and other instrument specific classes and the rest of the program.
"""
#pylint: disable=C0103

import os.path as op
import numpy as np
from scipy.interpolate import interp1d
from aston.Database import DBObject
from aston.FileFormats.FileFormats import ftype_to_class


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
        #self._updateInfoFromFile()

        #make stubs for the time array and the data array
        self.ions = []
        self.data = None

    def _getTimeSlice(self, arr, st_time=None, en_time=None):
        '''Returns a slice of the incoming array filtered between
        the two times specified. Assumes the array is the same
        length as self.data. Acts in the time() and trace() functions.'''
        if self.data.shape[0] == 0:
            return self.data[:, 0]

        tme = self.data[:, 0].copy()
        if 't-scale' in self.info:
            tme *= float(self.info['t-scale'])
        if 't-offset' in self.info:
            tme += float(self.info['t-offset'])

        if st_time is None:
            st_idx = 0
        else:
            st_idx = (np.abs(tme - st_time)).argmin()
        if en_time is None:
            en_idx = self.data.shape[0]
        else:
            en_idx = (np.abs(tme - en_time)).argmin() + 1
        return arr[st_idx:en_idx]

    def time(self, st_time=None, en_time=None):
        """
        Returns an array with all of the time points at which
        data was collected
        """
        #load the data if it hasn't been already
        #TODO: this should cache only the times (to speed up access
        #in case we're looking at something with the _getTotalTrace)
        if self.data is None:
            self._cacheData()

        #scale and offset the data appropriately
        tme = self.data[:, 0].copy()
        try:  # convert it back if it's sparse
            tme = np.array(tme.todense())
        except:  # it's a regular array, keep it
            pass
        if 't-scale' in self.info:
            tme *= float(self.info['t-scale'])
        if 't-offset' in self.info:
            tme += float(self.info['t-offset'])
        #return the time series
        return self._getTimeSlice(tme, st_time, en_time)

    def trace(self, ion=None, st_time=None, en_time=None):
        '''Returns an array, either time/ion filtered or not
        of chromatographic data.'''
        if self.data is None:
            self._cacheData()

        if type(ion) == str or type(ion) == unicode:
            ic = self._parseIonString(ion.lower())
        elif type(ion) == int or type(ion) == float:
            #if the ion is a number, do the straightforward thing
            ic = self._getIonTrace(ion)
        else:
            #all other cases, just return the total trace
            ic = self._getTotalTrace()

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
                    ic = self._applyFxn(ic, 'movingaverage', wnd)
            elif self.info['t-smooth'].lower() == 'savitsky-golay':
                wnd = self.info['t-smooth-window']
                sord = self.info['t-smooth-order']
                if wnd.isdigit() and sord.isdigit():
                    ic = self._applyFxn(ic, 'savitskygolay', wnd, sord)

        return self._getTimeSlice(ic, st_time, en_time)

    def _parseIonString(self, istr):
        '''Recursive string parser that handles "ion" strings.'''
        #TODO: better error checking in here?

        #null case
        if istr.strip() == '':
            return np.zeros(self.data.shape[0])

        #remove any parantheses or pluses around the whole thing
        if istr[0] in '+':
            istr = istr[1:]
        if istr[0] in '(' and istr[-1] in ')':
            istr = istr[1:-1]

        #invert it if preceded by a minus sign
        if istr[0] in '-':
            return -1.0 * self._parseIonString(istr[1:])

        #this is a function
        if istr[:istr.find('(')].isalnum() and istr.find('(') != -1:
            fxn = istr[:istr.find('(')]
            if fxn == 'file' or fxn == 'f':
                args = istr[istr.find('(') + 1:-1].split(';')
                dt = self.database.getFileByName(args[0])
                if dt is None:
                    return np.zeros(self.data.shape[0])
                if len(args) > 1:
                    y = dt.trace(args[1])
                else:
                    y = dt.trace()
                t = dt.data[:, 0]
                f = interp1d(t, y, bounds_error=False, fill_value=0.0)
                return f(self.data[:, 0])
            else:
                args = istr[istr.find('(') + 1:-1].split(';')
                ic = self._parseIonString(args[0])
                return self._applyFxn(ic, fxn, *args[1:])

        #have we simplified enough? is all of the tricky math gone?
        if set(istr).intersection(set('+-/*()')) == set():
            if istr == 'x' or istr == 'tic':
                return self._getTotalTrace()
            elif istr.count(':') == 1:
                #contains an ion range
                ion = np.array([float(i) for i in istr.split(':')]).mean()
                tol = abs(float(istr.split(':')[0]) - ion)
                return self._getIonTrace(ion, tol)
            elif all(i in '0123456789.' for i in istr):
                return self._getIonTrace(float(istr))
            elif istr[0] == '!' and all(i in '0123456789.' for i in istr[1:]):
                return np.ones(self.data.shape[0]) * float(istr[1:])
            elif istr == '!pi':
                return np.ones(self.data.shape[0]) * np.pi
            else:
                return self._getNamedTrace(istr)

        #parse out the additive parts
        ic = np.zeros(self.data.shape[0])
        pa = ''
        for i in istr:
            if i in '+-' and pa[-1] not in '*/+' and \
              pa.count('(') == pa.count(')'):
                ic += self._parseIonString(pa)
                pa = ''
            pa += i

        if pa != istr:
            return ic + self._parseIonString(pa)

        #no additive parts, parse multiplicative/divisive parts
        ic = None
        pa = ''
        for i in istr:
            if i in '*/' and pa.count('(') == pa.count(')'):
                if ic is None:
                    ic = self._parseIonString(pa)
                elif pa[0] in '*':
                    ic *= self._parseIonString(pa[1:])
                elif pa[0] in '/':
                    ic /= self._parseIonString(pa[1:])
                pa = ''
            pa += i

        if pa[0] in '*':
            return ic * self._parseIonString(pa[1:])
        elif pa[0] in '/':
            return ic / self._parseIonString(pa[1:])
        else:
            return 0  # this should never happen?

    def _getNamedTrace(self, name):
        lookdict = {'temp': 'm-tmp', 'pres': 'm-prs', 'flow': 'm-flw'}
        if name == 't' or name == 'time':
            return self.data[:, 0].copy()
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
                    return np.interp(self.data[:, 0], x[srt_ind], \
                      y[srt_ind], float(tpts['S']))
                else:
                    return np.interp(self.data[:, 0], x[srt_ind], \
                      y[srt_ind])
            elif is_num(val):
                return float(val) * np.ones(self.data.shape[0])
        else:
            return self._getOtherTrace(name)

    def _applyFxn(self, ic, fxn, *args):
        '''Apply the function, fxn, to the trace, ic, and returns the result.'''
        from aston.Math.Chromatograms import fxns
        if fxn in fxns:
            f = fxns[fxn]
            try:
                return f(ic, *args)
            except TypeError:
                pass
        return np.zeros(ic.shape[0])

    def scan(self, time):
        """
        Returns the spectrum from a specific time.
        """
        if self.data is None:
            self._cacheData()

        if 't-offset' in self.info:
            time -= float(self.info['t-offset'])
        if 't-scale' in self.info:
            time /= float(self.info['t-scale'])

        times = self.data[:, 0]
        try:
            times = np.array(times.todense())
        except NameError:
            times = np.array(times)
        idx = (np.abs(times - time)).argmin()
        ion_abs = self.data[idx, 1:]
        try:
            ion_abs = np.array(ion_abs.todense())
        except NameError:
            ion_abs = np.array(ion_abs)
        print(len(self.ions), len(ion_abs))
        return (np.array(self.ions), ion_abs)

    def _loadInfo(self, fld):
        #create the key if it doesn't yet exist
        if fld == 'vis':
            self.info['vis'] = 'n'
        elif fld == 'r-filename':
            #TODO: generate this in Database on creation?
            #the filename used for display in the program.
            self.info[fld] = op.join(op.basename( \
              op.dirname(self.rawdata)), op.basename(self.rawdata))
        elif fld == 's-scans':
            self.info['s-scans'] = str(self.data.shape[0])
        elif fld == 's-time-st' or fld == 's-time-en':
            time = self.data[:, 0]
            self.info['s-time-st'] = str(min(time))
            self.info['s-time-en'] = str(max(time))
        elif fld == 's-peaks' or fld == 's-spectra':
            #fts = self.db.getFeatsByFile(self.fid[1])
            #self.info['s-peaks'] = \
            #  str(len([ft for ft in fts if isinstance(ft, Peak)]))
            #self.info['s-spectra'] = \
            #  str(len([ft for ft in fts if isinstance(ft, Spectrum)]))
            pass
        elif fld == 's-peaks-st' or fld == 's-peaks-en':
            pks = self.getAllChildren('peak')
            if len(pks) > 0:
                times = [float(pk.getInfo('p-s-time')) for pk in pks]
                self.info['s-peaks-st'] = str(min(times))
                self.info['s-peaks-en'] = str(max(times))
        elif fld == 's-mz-min' or fld == 's-mz-max':
            if self.data is None:
                self._cacheData()
            ions = np.array([i for i in self.ions \
                             if type(i) is int or type(i) is float])
            self.info['s-mz-min'] = str(min(ions))
            self.info['s-mz-max'] = str(max(ions))
        else:
            pass

    #The following function stubs should be filled out in the
    #subclasses that handle the raw datafiles.

    def _cacheData(self):
        '''Load the data into the Datafile for the first time.'''
        self.ions = []
        self.data = None

    def _getIonTrace(self, val, tol=0.5):
        '''Return a specific ion trace from the data.'''
        if self.data is None:
            self._cacheData()
        ions = np.array([i for i in self.ions \
          if type(i) is int or type(i) is float])
        rows = 1 + np.where(np.abs(ions - val) < tol)[0]
        if len(rows) == 0:
            return np.zeros(self.data.shape[0]) * np.nan
        else:
            return self.data[:, rows].sum(axis=1)

    def _getOtherTrace(self, name):
        '''Return a named trace, like pressure or temperature.'''
        return np.zeros(self.data.shape[0])

    def _getTotalTrace(self):
        '''Return the default, total trace.'''
        if self.data is None:
            self._cacheData()
        return self.data[:, 1:].sum(axis=1)
        #return np.array([sum(i.values()) for i in self.data])

    def _updateInfoFromFile(self):
        '''Return file information.'''
        pass
