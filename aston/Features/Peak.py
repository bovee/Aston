import numpy as np
from aston.Database import DBObject
import aston.Math.Peak as peakmath
from aston.Features.Spectrum import Spectrum

class Peak(DBObject):
    def __init__(self, *args, **kwargs):
        super(Peak, self).__init__('peak', *args, **kwargs)

    @property
    def data(self):
        return np.array(self.rawdata)
    
    def _calcInfo(self, fld):
        if fld == 'p-s-area':
            return str(peakmath.area(self.data))
        elif fld == 'p-s-length':
            return str(peakmath.length(self.data))
        elif fld == 'p-s-height':
            return str(peakmath.height(self.data))
        elif fld == 'p-s-time':
            return str(peakmath.time(self.data))
        elif fld == 'p-s-pwhm':
            return str(peakmath.length(self.data, pwhm=True))
        elif fld == 'p-s-pkcap':
            prt = self.getParentOfType('file')
            if prt is None:
                return ''
            t = float(prt.getInfo('s-peaks-en')) - \
                float(prt.getInfo('s-peaks-st'))
            return str(t / peakmath.length(self.data) + 1)
 
    def contains(self,x,y):
        return peakmath.contains(self.data, x, y)
    
    def createSpectrum(self, method=None):
        prt = self.getParentOfType('file')
        time = peakmath.time(self.data)
        if method is None:
            data = prt.scan()
        info = {'sp-time':str(time)}
        return Spectrum(self.db, None, self.db_id, info, data)

    def changePeakType(self,new_type):
        #http://www.scipy.org/Cookbook/FittingData
        pass

class GaussianPeak(Peak):
    def __init__(self, *args, **kwargs):
        super(Peak, self).__init__('peak', *args, **kwargs)

    @property
    def data(self):
        #gaussian parameters: st_t, en_t, points, t, base, height, width
        st_t, en_t, pts, t, spc, y0, h, w = self.rawdata
        
        gauss = lambda t : y0 + h*np.exp(-(t-x)**2/(2*w**2))
        x = np.linspace(st_t,en_t,pts)
        g_line = gauss(x)
        return g_line
