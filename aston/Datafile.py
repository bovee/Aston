'''This module acts as an intermediary between the Agilent, Thermo,
and other instrument specific classes and the rest of the program.'''
#pylint: disable=C0103

import struct
import os.path as op
import numpy as np
import json
from scipy.interpolate import interp1d
from aston.Features import Spectrum, Peak
 
class Datafile(object):
    '''Generic chromatography data containter. This abstacts away
    the implementation details of the specific file formats.'''
    def __new__(cls, filename, *args):

        ext = filename.split('.')[-1].upper()
        try:
            f = open(filename, mode='rb')
            magic = struct.unpack('>H', f.read(2))[0]
            f.close()
        except struct.error:
            magic = 0

        #TODO: .BAF : Bruker instrument data format
        #TODO: .FID : Bruker instrument data format
        #TODO: .PKL : MassLynx associated format
        #TODO: .RAW : Micromass MassLynx directory format
        #TODO: .WIFF : ABI/Sciex (QSTAR and QTRAP instrument) file format
        #TODO: .YEP : Bruker instrument data format
        #TODO: .RAW : PerkinElmer TurboMass file format
        
        if ext == 'MS' and magic == 0x0132:
            from aston.FileFormats.AgilentMS import AgilentMS
            return super(Datafile, cls).__new__(AgilentMS, filename, *args)
        #elif ext == 'BIN' and magic == 513:
        #    from .AgilentMS import AgilentMSMSProf
        #    return super(Datafile, cls).__new__(AgilentMSMSProf,filename,*args)
        #elif ext == 'BIN' and magic == 257:
        #    from .AgilentMS import AgilentMSMSScan
        #    return super(Datafile, cls).__new__(AgilentMSMSScan,filename,*args)
        elif ext == 'CF' and magic == 0xFFFF:
            from aston.FileFormats.Thermo import ThermoCF
            return super(Datafile, cls).__new__(ThermoCF, filename, *args)
        elif ext == 'DXF' and magic == 0xFFFF:
            from aston.FileFormats.Thermo import ThermoDXF
            return super(Datafile, cls).__new__(ThermoDXF, filename, *args)
        elif ext == 'SD':
            from aston.FileFormats.AgilentUV import AgilentDAD
            return super(Datafile, cls).__new__(AgilentDAD, filename, *args)
        elif ext == 'CH' and magic == 0x0233:
            from aston.FileFormats.AgilentUV import AgilentMWD
            return super(Datafile, cls).__new__(AgilentMWD, filename, *args)
        elif ext == 'UV' and magic == 0x0233:
            from aston.FileFormats.AgilentUV import AgilentCSDAD
            return super(Datafile, cls).__new__(AgilentCSDAD, filename, *args)
        elif ext == 'CSV':
            from aston.FileFormats.OtherFiles import CSVFile
            return super(Datafile, cls).__new__(CSVFile, filename, *args)
        else:
            return None
            #return super(Datafile, cls).__new__(cls,filename,*args)

    def __init__(self, filename, database=None, info=()):
        #info is of the form: [name,info,projid,fileid]
        self.filename = filename
        self.database = database

        #ways to initialize myself
        #1. using parameters passed to me
        if database is not None:
            self.info = json.loads(info[0])
            self.fid = (info[1], info[2]) #(project_id, file_id)
        #2. from file info -> use this if not using the Aston GUI
        else:
            self.info = {'traces':'TIC','name':''}
            self._updateInfoFromFile()
            self.fid = (None, None)
        
        #make invisible at first
        self.visible = False

        #make stubs for the time array and the data array
        self.times = None
        self.data = None

    def _getTimeSlice(self, arr, st_time=None, en_time=None):
        '''Returns a slice of the incoming array filtered between
        the two times specified. Assumes the array is the same
        length as self.times. Acts in the time() and trace() functions.'''
        if len(self.times) == 0:
            return np.array([])
        if st_time is None:
            st_idx = 0
        else:
            st_idx = (np.abs(np.array(self.times)-st_time)).argmin()
        if en_time is None:
            en_idx = len(self.times)
        else:
            en_idx = (np.abs(np.array(self.times)-en_time)).argmin()+1
        return arr[st_idx:en_idx]

    def time(self, st_time=None, en_time=None):
        '''Returns an array with all of the time points at which
        data was collected'''
        #load the data if it hasn't been already
        #TODO: this should cache only the times (to speed up access
        #in case we're looking at something with the _getTotalTrace)
        if self.times is None:
            self._cacheData()
        
        #scale and offset the data appropriately
        tme = np.array(self.times)
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
            if self.info['t-smooth'] == 'moving average':
                wnd = self.info['t-smooth-window']
                ic = self._applyFxn(ic, 'movingaverage', wnd)
            elif self.info['t-smooth'] == 'savitsky-golay':
                wnd = self.info['t-smooth-window']
                sord = self.info['t-smooth-order']
                ic = self._applyFxn(ic, 'savitskygolay', wnd, sord)

        return self._getTimeSlice(ic, st_time, en_time)

    def _parseIonString(self, istr):
        '''Recursive string parser that handles "ion" strings.'''
        #TODO: better error checking in here?

        #null case
        if istr.strip() == '':
            return np.zeros(len(self.times))
        
        #remove any parantheses or pluses around the whole thing
        if istr[0] in '+':
            istr = istr[1:]
        if istr[0] in '(' and istr[-1] in ')':
            istr = istr[1:-1]

        #invert it if preceded by a minus sign
        if istr[0] in '-':
            return -1.0*self._parseIonString(istr[1:])

        #this is a function
        if istr[:istr.find('(')].isalnum() and istr.find('(') != -1:
            fxn = istr[:istr.find('(')]
            if fxn == 'file' or fxn == 'f':
                args = istr[istr.find('(')+1:-1].split(';')
                dt = self.database.getFileByName(args[0])
                if dt is None: return np.zeros(len(self.times))
                if len(args) > 1:
                    y = dt.trace(args[1])
                else:
                    y = dt.trace()
                t = np.array(dt.times)
                f = interp1d(t, y, bounds_error=False, fill_value=0.0)
                return f(self.times)
            else:
                args = istr[istr.find('(')+1:-1].split(';')
                ic = self._parseIonString(args[0])
                return self._applyFxn(ic, fxn, *args[1:])

        #have we simplified enough? is all of the tricky math gone?
        if set(istr).intersection(set('+-/*()')) == set():
            if istr.count(':') == 1:
                #contains an ion range
                ion = np.array([float(i) for i in istr.split(':')]).mean()
                tol = abs(float(istr.split(':')[0]) - ion)
                return self._getIonTrace(ion, tol)
            elif all(i in '0123456789.' for i in istr):
                return self._getIonTrace(float(istr))
            elif istr == 't' or istr == 'time':
                return self.time()
            elif istr == 'x' or istr == 'tic':
                return self._getTotalTrace()
            #elif istr == 'b' or istr == 'base':
            #    #TODO: create a baseline
            #    pass
            elif istr == 'coda':
                # Windig W: The use of the Durbin-Watson criterion for
                # noise and background reduction of complex liquid
                # chromatography/mass spectrometry data and a new algorithm
                # to determine sample differences. Chemometrics and
                # Intelligent Laboratory Systems. 2005, 77:206-214.
                pass
            elif istr == 'rnie':
                # Yunfei L, Qu H, and Cheng Y: A entropy-based method
                # for noise reduction of LC-MS data. Analytica Chimica
                # Acta 612.1 (2008)
                pass
            elif istr == 'wmsm':
                # Fleming C et al. Windowed mass selection method:
                # a new data processing algorithm for LC-MS data.
                # Journal of Chromatography A 849.1 (1999) 71-85.
                pass
            elif istr[0] == '!' and all(i in '0123456789.' for i in istr[1:]):
                return np.ones(len(self.times)) * float(istr[1:])
            elif istr == '!pi':
                return np.ones(len(self.times)) * np.pi
            else:
                return self._getOtherTrace(istr)
        
        #parse out the additive parts
        ic = np.zeros(len(self.times))
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
            return 0 #this should never happen?

    def _applyFxn(self, ic, fxn, *args):
        '''Apply the function, fxn, to the trace, ic, and returns the result.'''
        if fxn == 'fft':
            #FIXME: "time" of FFT axis doesn't match time of ic axis
            oc = np.abs(np.fft.fftshift(np.fft.fft(ic))) / len(ic)
        #elif fxn == 'ifft':
        #    ic = np.fft.ifft(np.fft.fftshift(ic * len(ic)))# / len(ic)
        elif fxn == 'noisefilter' and len(args) == 1:
            #adapted from http://glowingpython.blogspot.com/
            #2011/08/fourier-transforms-and-image-filtering.html
            I = np.fft.fftshift(np.fft.fft(ic)) # entering to frequency domain
            # fftshift moves zero-frequency component to the center of the array
            P = np.zeros(len(I), dtype=complex)
            c1 = len(I)/2 # spectrum center
            r = float(args[0]) #percent of signal to save
            r = int((r*len(I))/2) #convert to coverage of the array
            for i in range(c1-r, c1+r):
                P[i] = I[i] # frequency cutting
            oc = np.real(np.fft.ifft(np.fft.ifftshift(P)))
        elif fxn == 'abs':
            oc = np.abs(ic)
        elif fxn == 'sin':
            oc = np.sin(ic)
        elif fxn == 'cos':
            oc = np.cos(ic)
        elif fxn == 'tan':
            oc = np.tan(ic)
        elif fxn == 'd' or fxn == 'derivative':
            #FIXME: not adjusted for time at all
            ic = np.gradient(ic)
        elif fxn == 'base':
            #INSPIRED by Algorithm A12 from Zupan
            #5 point pre-smoothing
            sc = np.convolve(np.ones(5) / 5.0, ic, mode='same')
            #get local minima
            mn = np.arange(len(ic))[np.r_[True,((sc < np.roll(sc, 1)) &
              (sc < np.roll(sc, -1)))[1:-1], True]]
            #don't allow baseline to have a slope greater than
            #10x less than the steepest peak
            max_slope = np.max(np.gradient(ic))/10.0
            slope = max_slope
            pi = 0 #previous index
            oc = np.zeros(len(ic))
            for i in range(1, len(mn)):
                if slope < (ic[mn[i]]-ic[mn[pi]]) / (mn[i]-mn[pi]) and \
                  slope < max_slope:
                    #add trend
                    oc[mn[pi]:mn[i-1]] = \
                      np.linspace(ic[mn[pi]],ic[mn[i-1]],mn[i-1]-mn[pi])
                    pi = i -1
                slope = (ic[mn[i]]-ic[mn[pi]])/(mn[i]-mn[pi])
            print(mn[pi], mn[-1])
            oc[mn[pi]:mn[-1]] = \
              np.linspace(ic[mn[pi]],ic[mn[-1]],mn[-1]-mn[pi])
            oc[-1] = oc[-2] #FIXME: there's definitely a bug in here somewhere
        elif (fxn == 'movingaverage' and len(args) == 1) or \
          (fxn == 'savitskygolay' and len(args) == 2):
            if fxn == 'movingaverage':
                x = int(args[0])
                half_wind = (x-1) // 2
                m = np.ones(x) / x
            elif fxn == 'savitskygolay':
                # adapted from http://www.scipy.org/Cookbook/SavitzkyGolay
                half_wind = (int(args[0]) -1) // 2
                order_range = range(int(args[1])+1)
                # precompute coefficients
                b = [[k**i for i in order_range] \
                     for k in range(-half_wind, half_wind+1)]
                m = np.linalg.pinv(b)
                m = m[0]
            # pad the signal at the extremes with
            # values taken from the signal itself
            firstvals = ic[0] - np.abs(ic[1:half_wind+1][::-1] - ic[0])
            lastvals = ic[-1] + np.abs(ic[-half_wind-1:-1][::-1] - ic[-1])
            y = np.concatenate((firstvals, ic, lastvals))
            oc = np.convolve(m, y, mode='valid')
        else:
            oc = ic
        return oc

    def scan(self, time):
        '''Returns the spectrum from a specific time.'''
        if 't-offset' in self.info:
            time -= float(self.info['t-offset'])
        if 't-scale' in self.info:
            time /= float(self.info['t-scale'])
        try:
            return self.data[self.times.index(time)]
        except ValueError:
            idx = (np.abs(np.array(self.times)-time)).argmin()
            return self.data[idx]

    def mz_bounds(self):
        '''Returns the highest and lowest m/z values in the data.
           Used for plotting data in 2D heatmaps.'''
        if self.data is None:
            self._cacheData()
            
        mz_min, mz_max = 100, 0
        for i in self.data:
            try:
                mz_min = min(min(i.keys()), mz_min)
                mz_max = max(max(i.keys()), mz_max)
            except ValueError:
                pass
        return mz_min, mz_max
    
    def delInfo(self,fld):
        delkeys = None
        if fld == 's-peaks':
            delkeys = ['s-peaks','s-peaks-st','s-peaks-en']
        
        if delkeys is not None:
            for key in delkeys:
                if key in self.info:
                    del self.info[key]
    
    def getInfo(self,fld):
        #create the key if it doesn't yet exist
        if fld not in self.info.keys():
            if fld == 'r-filename':
                #the filename used for display in the program.
                self.info[fld] = op.join(op.basename( \
                  op.dirname(self.filename)), op.basename(self.filename))
            elif fld == 's-scans':
                self.info['s-scans'] = str(len(self.time()))
            elif fld == 's-time-st' or fld == 's-time-en':
                time = self.time()
                self.info['s-time-st'] = str(min(time))
                self.info['s-time-en'] = str(max(time))
            elif fld == 's-peaks' or fld == 's-spectra':
                fts = self.database.getFeatsByFile(self.fid[1])
                self.info['s-peaks'] = \
                  str(len([ft for ft in fts if isinstance(ft, Peak)]))
                self.info['s-spectra'] = \
                  str(len([ft for ft in fts if isinstance(ft, Spectrum)]))
            elif fld == 's-peaks-st' or fld == 's-peaks-en':
                fts = self.database.getFeatsByFile(self.fid[1])
                if len(fts) > 0: 
                    times = [ft.time() for ft in fts \
                      if isinstance(ft, Peak)]
                    self.info['s-peaks-st'] = str(min(times))
                    self.info['s-peaks-en'] = str(max(times))
            else:
                pass
        
        #check again to see if we figured out the value
        if fld not in self.info.keys():
            return ''
        else:
            return self.info[fld]
    
    def saveChanges(self):
        '''Save any changes to the datafile to the database.'''
        if self.fid[1] is not None:
            return self.database.updateFile(self)
        else:
            return False

    #The following function stubs should be filled out in the
    #subclasses that handle the raw datafiles.

    def _cacheData(self):
        '''Load the data into the Datafile for the first time.'''
        self.times = []
        self.data = []

    def _getIonTrace(self, val, tol=0.5):
        '''Return a specific ion trace from the data.'''
        if self.data is None:
            self._cacheData()
        return np.array([sum([i for ion, i in pt.items() \
            if ion >= val-tol and ion <= val+tol]) for pt in self.data])

    def _getOtherTrace(self, name):
        '''Return a named trace, like pressure or temperature.'''
        return np.zeros(len(self.times))

    def _getTotalTrace(self):
        '''Return the default, total trace.'''
        if self.data is None:
            self._cacheData()
        return np.array([sum(i.values()) for i in self.data])

    #    def _updateInfoFromFile(self):
        '''Return file information.'''
    #    pass
