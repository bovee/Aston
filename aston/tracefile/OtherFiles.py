import numpy as np
#from pandas import read_csv
from aston.trace.Trace import AstonFrame
from aston.tracefile.TraceFile import TraceFile


class CSVFile(TraceFile):
    '''
    Reads in a *.CSV. Assumes that the first line is the header and
    that the file is comma delimited.
    '''
    ext = 'CSV'
    traces = ['#']
    #TODO: use pandas to make this much better
    #TODO: determine traces to list

    @property
    def data(self):
        delim = ','
        try:  # TODO: better, smarter error checking than this
            with open(self.filename, 'r') as f:
                lns = f.readlines()
                ions = [float(i) for i in lns[0].split(delim)[1:]]
                data = np.array([np.fromstring(ln, sep=delim) \
                                 for ln in lns[1:]])
                return AstonFrame(data[:, 1:], data[:, 0], ions)
        except:
            return AstonFrame()


def write_csv(filename, df, info=None):
    pass
