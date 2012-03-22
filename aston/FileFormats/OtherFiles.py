from aston import Datafile
import os.path as op
import numpy as np

class CSVFile(Datafile.Datafile):
    '''
    Reads in a *.CSV. Assumes that the first line is the header and 
    that the file is comma delimited.
    '''
    def __init__(self,*args,**kwargs):
        super(CSVFile,self).__init__(*args,**kwargs)
        try:
            self.db
        except:
            print args

    def _cacheData(self): 
        delim = ','
        try: #TODO: better, smarter error checking than this
            with open(self.rawdata,'r') as f:
                lns = f.readlines()
                self.ions = [float(i) for i in lns[0].split(delim)[1:]]
                self.data = np.array( \
                    [np.fromstring(ln, sep=delim) for ln in lns[1:]])
        except:
            self.data = np.array([])
        print self.data
            
    def _updateInfoFromFile(self):
        d = {}
        d['name'] = op.splitext(op.basename(self.rawdata))[0]
        d['r-type'] = 'Sample'
        self.info.update(d)
