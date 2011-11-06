from .Datafile import Datafile

class CSVFile(Datafile):
    '''
    Reads in a *.CSV. Assumes that the first line is the header and 
    that the file is comma delimited.
    '''
    def __init__(self,*args,**kwargs):
        super(CSVFile,self).__init__(*args,**kwargs)

    def _cacheData(self): 
        delim = ','
        self.times = []
        self.data = []
        try:
            with open(self.filename,'r') as f:
                lns = f.readlines()
                hdrs = [float(i) for i in lns[0].split(delim)[1:]]
                for ln in lns[1:]:
                    self.times.append(float(ln.split(delim)[0]))
                    vals = [float(i) for i in ln.split(delim)[1:]]
                    self.data.append(dict(zip(hdrs,vals)))
        except:
            self.times = []
            self.data = []
            
    def _getInfoFromFile(self):
        import os.path as op
        name = op.splitext(op.basename(self.filename))[0]
        info = {}
        info['traces'] = 'TIC'
        info['type'] = 'Sample'
        info['data_type'] = 'CSV'
        return name,info
