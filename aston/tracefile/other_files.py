import numpy as np
# from pandas import read_csv
from aston.trace import Chromatogram
from aston.tracefile import TraceFile


class CSVFile(TraceFile):
    '''
    Reads in a *.CSV. Assumes that the first line is the header and
    that the file is comma delimited.
    '''
    mime = 'text/csv'
    traces = ['#']
    # TODO: use pandas to make this much better?
    # TODO: determine traces to list

    @property
    def data(self):
        delim = ','
        try:  # TODO: better, smarter error checking than this
            with open(self.filename, 'r') as f:
                lns = f.readlines()
                ions = [float(i) for i in lns[0].split(delim)[1:]]
                data = np.array([np.fromstring(ln, sep=delim)
                                 for ln in lns[1:]])
                return Chromatogram(data[:, 1:], data[:, 0], ions)
        except Exception:
            return Chromatogram()


def write_csv(filename, df, info=None, delimiter=','):
    with open(filename, 'w') as f:
        # write out columns
        f.write('Time' + delimiter)
        f.write(delimiter.join(str(i) for i in df.data.columns.tolist()))

        # write out the rest, scan by scan
        for scan in df.scans():
            f.write('\n ' + str(df.name) + delimiter)
            f.write(delimiter.join(str(i) for i in scan.abn.tolist()))
