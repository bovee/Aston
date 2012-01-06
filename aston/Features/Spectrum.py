from aston.Features import Feature

class Spectrum(Feature):
    def __init__(self,data,ids=None,*args,**kwargs):
        if 'time' in kwargs:
            self.time = kwargs['time']
        super(Spectrum,self).__init__(data,ids,*args,**kwargs)
        self.cls = 'Spectrum'

    @property
    def data(self):
        return self._data

