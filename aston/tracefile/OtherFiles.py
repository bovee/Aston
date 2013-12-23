import numpy as np
from pandas import DataFrame
from aston.tracefile.Common import TraceFile


class CSVFile(TraceFile):
    '''
    Reads in a *.CSV. Assumes that the first line is the header and
    that the file is comma delimited.
    '''
    ext = 'CSV'
    #TODO: use pandas to make this much better

    @property
    def data(self):
        delim = ','
        try:  # TODO: better, smarter error checking than this
            with open(self.filename, 'r') as f:
                lns = f.readlines()
                ions = [float(i) for i in lns[0].split(delim)[1:]]
                data = np.array([np.fromstring(ln, sep=delim) \
                                 for ln in lns[1:]])
                return DataFrame(data[:, 1:], data[:, 0], ions)
        except:
            return DataFrame()
