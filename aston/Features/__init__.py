#pylint: disable=C0103
class Feature(object):
    '''This class is used for interacting with peak shapes
    or spectra.'''
    def __init__(self,data,ids=None,*args):
        self._data = data
        #ids = (feature_id,compound_id,file_id)
        if ids is None:
            self.ids = [None,None,None]
        else:
            self.ids = list(ids)
        self.cls = 'Feature'

    def data_for_export(self):
        return self._data

#convenience of being able to import these without specifying the file
from aston.Features.Peak import Peak
from aston.Features.Compound import Compound
from aston.Features.Spectrum import Spectrum
