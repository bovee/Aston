import numpy as np
from aston.Database import DBObject
import aston.Math.Peak as peakmath
from aston.Features.Spectrum import Spectrum

class Peak(DBObject):
    def __init__(self, *args, **kwargs):
        super(Peak, self).__init__('peak', *args, **kwargs)
        
        if self.getInfo('p-model') == 'gaussian':
            #TODO: gaussian params should be stored in the database itself
            #and this "data" should only be generated upon conversion
            #into the gaussian "peak model."
            
            #gaussian parameters: st_t,en_t,points,t,base,height,width
            y0 = self.info['p-s-base'] #TODO: fix this
            t = self.info['p-s-time']
            h = self.info['p-s-height']
            w = self.info['p-s-pwhm']

            gauss = lambda t : y0 + h*np.exp(-(t-x)**2/(2*w**2))
            times = self.rawdata[:,0]
            self.data = np.array(gauss(times))
        else:
            self.data = np.array(self.rawdata)

    def time(self, st_time = None, en_time = None):
        pass
    
    def trace(self, ion=None):
        pass
    
    def _loadInfo(self, fld):
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
        
    def calcInfo(self, fld):
        if fld == 'p-s-pkcap':
            prt = self.getParentOfType('file')
            if prt is None:
                return ''
            t = float(prt.getInfo('s-peaks-en')) - \
                float(prt.getInfo('s-peaks-st'))
            return str(t / peakmath.length(self.data) + 1)
        else:
            return ''
 
    def contains(self,x,y):
        return peakmath.contains(self.data, x, y)
    
    def createSpectrum(self, method=None):
        prt = self.getParentOfType('file')
        time = peakmath.time(self.data)
        if method is None:
            data = prt.scan(time)
        info = {'sp-time':str(time)}
        return Spectrum(self.db, None, self.db_id, info, data)

    def setInfo(self, fld, key):
        if fld == 'p-model':
            pass #TODO: change the underlying data into the new model
            #http://www.scipy.org/Cookbook/FittingData
        super(Peak, self).setInfo(fld, key)
