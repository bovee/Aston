"""This module acts as an intermediary between the Agilent, Thermo,
and other instrument specific classes and the rest of the program."""
class Datafile(object):
    '''This abstacts away the implementation details of the specific file
    formats'''
    def __new__(cls, filename, *args):
        import struct

        ext = filename.split('.')[-1].upper()
        try:
            f = open(filename,mode='rb')
            magic = struct.unpack('>H',f.read(2))[0]
            f.close()
        except:
            magic = 0

        #TODO: .BAF : Bruker instrument data format
        #TODO: .FID : Bruker instrument data format
        #TODO: .PKL : MassLynx associated format
        #TODO: .RAW : Micromass MassLynx directory format
        #TODO: .WIFF : ABI/Sciex (QSTAR and QTRAP instrument) file format
        #TODO: .YEP : Bruker instrument data format
        #TODO: .RAW : PerkinElmer TurboMass file format
        
        if ext == 'MS' and magic == 0x0132:
            from .AgilentMS import AgilentMS
            return super(Datafile, cls).__new__(AgilentMS,filename,*args)
        #elif ext == 'BIN' and magic == 513:
        #    from .AgilentMS import AgilentMSMSProf
        #    return super(Datafile, cls).__new__(AgilentMSMSProf,filename,*args)
        #elif ext == 'BIN' and magic == 257:
        #    from .AgilentMS import AgilentMSMSScan
        #    return super(Datafile, cls).__new__(AgilentMSMSScan,filename,*args)
        elif ext == 'CF' and magic == 0xFFFF:
            from .Thermo import ThermoCF
            return super(Datafile, cls).__new__(ThermoCF,filename,*args)
        elif ext == 'DXF' and magic == 0xFFFF:
            from .Thermo import ThermoDXF
            return super(Datafile, cls).__new__(ThermoDXF,filename,*args)
        elif ext == 'SD':
            from .AgilentUV import AgilentDAD
            return super(Datafile, cls).__new__(AgilentDAD,filename,*args)
        elif ext == 'CH' and magic == 0x0233:
            from .AgilentUV import AgilentMWD
            return super(Datafile, cls).__new__(AgilentMWD,filename,*args)
        elif ext == 'UV' and magic == 0x0233:
            from .AgilentUV import AgilentCSDAD
            return super(Datafile, cls).__new__(AgilentCSDAD,filename,*args)
        elif ext == 'CSV':
            from .OtherFiles import CSVFile
            return super(Datafile, cls).__new__(CSVFile,filename,*args)
        else:
            return None
            #return super(Datafile, cls).__new__(cls,filename,*args)

    def __init__(self,filename,database=None,info=()):
        #info is of the form: [name,info,projid,fileid]
        self.filename = filename
        self.database = database

        #to decode the strings stored in the database into dictionarys
        #TODO: move this back into the database module
        def F(x):
            if x.find('\\') >= 0: return dict([i.split('\\') for i in x.split('|')])
            else: return {}

        #ways to initialize myself
        #1. using parameters passed to me
        if database is not None:
            self.name = info[0]
            self.info = F(info[1])
            self.fid = (info[2],info[3]) #(project_id, file_id)
        #2. from file info -> use this if not using the Aston GUI
        else:
            self.name, self.info = self._getInfoFromFile()
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
        import numpy as np
        if len(self.times) == 0: return np.array([])
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
        import numpy as np
        #load the data if it hasn't been already
        #TODO: this should cache only the times in case we're looking at GCMS data
        if self.times is None: self._cacheData()
        
        #scale and offset the data appropriately
        tme = np.array(self.times)
        if 'scale' in self.info:
            tme *= float(self.info['scale'])
        if 'offset' in self.info:
            tme += float(self.info['offset'])
        #return the time series
        return self._getTimeSlice(tme,st_time,en_time)

    def trace(self, ion=None, st_time=None, en_time=None):
        '''Returns an array, either time/ion filtered or not
        of chromatographic data.'''
        if self.data is None: self._cacheData()

        if type(ion) == str or type(ion) == unicode:
            ic = self._parseIonString(ion.lower())
        elif type(ion) == int or type(ion) == float:
            #if the ion is a number, do the straightforward thing
            ic = self._getIonTrace(ion)
        else:
            #all other cases, just return the total trace
            ic = self._getTotalTrace()

        if 'yscale' in self.info:
            ic *= float(self.info['yscale'])
        if 'yoffset' in self.info:
            ic += float(self.info['yoffset'])

        if 'remove noise' in self.info:
            #TODO: LOESS (local regression) filter
            pass

        if 'smooth' in self.info:
            if self.info['smooth'] == 'moving average':
                wnd = self.info['smooth window']
                ic = self._applyFxn(ic,'movingaverage',wnd)
            elif self.info['smooth'] == 'savitsky-golay':
                wnd = self.info['smooth window']
                sord = self.info['smooth order']
                ic = self._applyFxn(ic,'savitskygolay',wnd,sord)

        return self._getTimeSlice(ic,st_time,en_time)

    def _parseIonString(self,istr):
        #TODO: better error checking in here?
        import numpy as np
        from scipy.interpolate import interp1d

        #null case
        if istr.strip() == '': return np.zeros(len(self.times))
        
        #remove any parantheses or pluses around the whole thing
        if istr[0] in '+': istr = istr[1:]
        if istr[0] in '(' and istr[-1] in ')': istr = istr[1:-1]

        #invert it if preceded by a minus sign
        if istr[0] in '-': return -1.0*self._parseIonString(istr[1:])

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
                f = interp1d(t,y,bounds_error=False,fill_value=0.0)
                return f(self.times)
            else:
                args = istr[istr.find('(')+1:-1].split(';')
                ic = self._parseIonString(args[0])
                return self._applyFxn(ic,fxn,*args[1:])

        #have we simplified enough? is all of the tricky math gone?
        if set(istr).intersection(set('+-/*()')) == set():
            if istr.count(':') == 1:
                #contains an ion range
                ion = np.array([float(i) for i in istr.split(':')]).mean()
                tol = abs(float(istr.split(':')[0])-ion)
                return self._getIonTrace(ion,tol)
            elif all(i in '0123456789.' for i in istr):
                return self._getIonTrace(float(istr))
            elif istr == 't' or istr == 'time':
                tme = np.array(self.times)
                if 'scale' in self.info: tme *= float(self.info['scale'])
                if 'offset' in self.info: tme += float(self.info['offset'])
                return tme
            elif istr == 'x' or istr == 'tic':
                return self._getTotalTrace()
            elif istr == 'b' or istr == 'base':
                #TODO: create a baseline
                pass
            elif istr == 'coda':
                #Windig W: The use of the Durbin-Watson criterion for noise and background reduction of complex liquid chromatography/mass spectrometry data and a new algorithm to determine sample differences. Chemometrics and Intelligent Laboratory Systems. 2005, 77:206-214.
                pass
            elif istr == 'rnie':
                #Yunfei L, Qu H, and Cheng Y: A entropy-based method for noise reduction of LC-MS data. Analytica Chimica Acta 612.1 (2008)
                pass
            elif istr == 'wmsm':
                #Fleming C et al. Windowed mass selection method: a new data processing algorithm for LC-MS data. Journal of Chromatography A 849.1 (1999) 71-85.
                pass
            elif istr[0] == '!' and all(i in '0123456789.' for i in istr[1:]):
                return np.ones(len(self.times)) * float(istr[1:])
            elif istr == '!pi':
                return np.ones(len(self.times))*np.pi
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

    def _applyFxn(self,ic,fxn,*args):
        import numpy as np
        if fxn == 'fft':
            ic = np.abs(np.fft.hfft(ic)) / len(ic)
        elif fxn == 'abs':
            ic = np.abs(ic)
        elif fxn == 'sin':
            ic = np.sin(ic)
        elif fxn == 'cos':
            ic = np.cos(ic)
        elif fxn == 'tan':
            ic = np.tan(ic)
        elif fxn == 'd' or fxn == 'derivative':
            ic = np.gradient(ic)
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
                b = [[k**i for i in order_range] for k in range(-half_wind, half_wind+1)]
                m = np.linalg.pinv(b)
                m = m[0]
            # pad the signal at the extremes with
            # values taken from the signal itself
            firstvals = ic[0] - np.abs(ic[1:half_wind+1][::-1] - ic[0])
            lastvals = ic[-1] + np.abs(ic[-half_wind-1:-1][::-1] - ic[-1])
            y = np.concatenate((firstvals, ic, lastvals))
            ic = np.convolve(m, y, mode='valid')
        return ic

    def scan(self,time):
        import numpy as np
        if 'offset' in self.info:
            time = time-float(self.info['offset'])
        if 'scale' in self.info:
            time = time/float(self.info['scale'])
        try:
            return self.data[self.times.index(time)]
        except:
            idx = (np.abs(np.array(self.times)-time)).argmin()
            return self.data[idx]

    def mz_bounds(self):
        mz_min, mz_max = 100, 0
        for i in self.data:
            try:
                mz_min = min(min(i.keys()),mz_min)
                mz_max = max(max(i.keys()),mz_max)
            except: pass
        return mz_min, mz_max

    def shortFilename(self):
        import os.path as op
        return op.join(op.basename(op.dirname(self.filename)),op.basename(self.filename))
    
    def saveChanges(self):
        if self.fid[1] is not None:
            return self.database.updateFile(self)
        else:
            return False

    #The following function stubs should be filled out in the
    #subclasses that handle the raw datafiles.

    def _cacheData(self):
        self.times = []
        self.data = []

    def _getIonTrace(self,val,tol=0.5):
        import numpy as np
        if self.data is None: self._cacheData()
        return np.array([sum([i for ion,i in pt.items() \
            if ion >= val-tol and ion <= val+tol]) for pt in self.data])

    def _getOtherTrace(self,name):
        import numpy as np
        return np.zeros(len(self.times))

    def _getTotalTrace(self):
        import numpy as np
        if self.data is None: self._cacheData()
        return np.array([sum(i.values()) for i in self.data])

    def _getInfoFromFile(self):
        return '',{}
