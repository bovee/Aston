import numbers
import numpy as np
from aston.tracefile.Common import tfclasses, file_type
from pandas import Series, DataFrame


class TraceFile(object):
    ext = None
    mgc = None

    def __init__(self, filename=None, ftype=None, data=None):
        self.filename = filename
        self.ftype = ''
        self._data = None

        # try to automatically change my class to reflect
        # whatever type of file I'm pointing at if not provided
        if type(self) is TraceFile:
            if data is not None:
                self._data = data

            if filename is None:
                return

            ftype = file_type(filename)

            if ftype is not None:
                # try to automatically subclass myself to provided type
                for cls in tfclasses():
                    if cls.__name__ == ftype:
                        self.__class__ = cls
                        self.ftype = ftype
        else:
            self.ftype = str(self.__class__)

    #TODO: define a private function for twin filtering in here

    @property
    def data(self):
        if self._data is not None:
            return self._data
        else:
            return DataFrame()

    def total_trace(self, twin=None):
        d = self.data.sum(axis=1)
        if twin is not None:
            return d[d.between(twin[0], twin[1])]
        else:
            return d

    def trace(self, name='', tol=0.5, twin=None):
        # this is the only string we handle; all others handled in subclasses
        if name in ['', 'X', 'TIC']:
            return self.total_trace(twin)

        # if the string is actually a number, handle that
        try:
            name = float(name)
        except TypeError:
            pass

        #TODO: check for '#' trace in self.traces

        # try to quickly extract the relevant trace
        if isinstance(name, numbers.Number):
            col_nums = self.data.columns.values.astype(float)
            cols = np.where(np.abs(col_nums - name) <= tol)[0]
            d = self.data[self.data.columns[cols]].sum(axis=1)
        elif name in self.data.columns:
            d = self.data[name]
        else:
            d = Series()

        # return the appropriate time window of the trace
        if twin is not None:
            return d[d.between(twin[0], twin[1])]
        else:
            return d

    def scan(self, time, to_time=None, aggfunc=np.sum):
        """
        Returns the spectrum from a specific time or range of times.
        """
        #FIXME: use aggfunc
        t = self.data.index.values
        idx = (np.abs(t - time)).argmin()
        if to_time is None:
            ion_abs = self.data.values[idx, :].copy()
            return np.vstack([self.data.columns, ion_abs])
        else:
            en_idx = (np.abs(t - to_time)).argmin()
            idx, en_idx = min(idx, en_idx), max(idx, en_idx)
            ion_abs = self.data.values[idx:en_idx + 1, :].copy()
            return np.vstack([self.data.columns, ion_abs.sum(axis=0)])

    @property
    def info(self):
        #TODO: add creation date and short name
        return {'filename': self.filename,
                'filetype': self.ftype}

    def events(self, name, twin=None):
        return []
