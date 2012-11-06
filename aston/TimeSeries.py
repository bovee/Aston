"""

"""
import numpy as np
from scipy.interpolate import interp1d


class TimeSeries(object):
    def __init__(self, data=None, times=np.array([]), ions=[]):
        if data is not None:
            if len(data.shape) == 1:
                data = np.atleast_2d(data).T
            assert times.shape[0] == data.shape[0]
            assert len(ions) == data.shape[1]
        self.data = data
        self.times = times
        self.ions = ions

    def _slice_idxs(self, twin=None):
        """
        Returns a slice of the incoming array filtered between
        the two times specified. Assumes the array is the same
        length as self.data. Acts in the time() and trace() functions.
        """
        if twin is None:
            return 0, self.data.shape[0]

        tme = self.times.copy()

        if twin[0] is None:
            st_idx = 0
        else:
            st_idx = (np.abs(tme - twin[0])).argmin()
        if twin[1] is None:
            en_idx = self.data.shape[0]
        else:
            en_idx = (np.abs(tme - twin[1])).argmin() + 1
        return st_idx, en_idx

    def time(self, twin=None):
        """
        Returns an array with all of the time points at which
        data was collected
        """
        st_idx, en_idx = self._slice_idxs(twin)
        tme = self.times[st_idx:en_idx].copy()
        #return the time series
        return tme

    def len(self, twin=None):
        st_idx, en_idx = self._slice_idxs(twin)
        return en_idx - st_idx

    def trace(self, val='TIC', tol=0.5, twin=None):
        st_idx, en_idx = self._slice_idxs(twin)

        if val == 'TIC' and 'TIC' not in self.ions:
            # if a TIC is being requested and we don't have
            # a prebuilt one, sum up the axes
            data = self.data[st_idx:en_idx, :].sum(axis=1)
        else:
            # depending on the val, find the rows differently
            if type(val) is int or type(val) is float:
                ions = np.array([i for i in self.ions \
                if type(i) is int or type(i) is float])
                rows = np.where(np.abs(ions - val) < tol)[0]
            elif val in self.ions:
                rows = np.array([self.ions.index(val)])
            else:
                rows = []

            # if no rows, return an array of NANs
            # otherwise, return the data
            if len(rows) == 0:
                data = np.zeros(en_idx - st_idx) * np.nan
            else:
                data = self.data[st_idx:en_idx, rows].sum(axis=1)
        return TimeSeries(data, self.times, [val])

    def scan(self, time):
        """
        Returns the spectrum from a specific time.
        """
        times = self.times.copy()
        idx = (np.abs(times - time)).argmin()
        if type(self.data) == np.ndarray:
            ion_abs = self.data[idx, :].copy()
        else:
            ion_abs = self.data[idx, :].astype(float).toarray()[0]
        return np.array(self.ions), ion_abs

    def retime(self, new_times):
        return TimeSeries(self._retime(self.data), new_times, self.ions)

    def _retime(self, new_times):
        if new_times == self.times:
            return self.data
        else:
            f = lambda d: interp1d(self.times, d, \
              bounds_error=False, fill_value=0.0)(new_times)
            return np.apply_along_axis(f, 0, self.data)

    def apply_fxn(self, f):
        import inspect
        try:
            nargs = inspect.getargspec(f)
        except TypeError:
            #it's probably a Scipy fxn, so default to just
            #passing in the data (no times)
            nargs = 1
        if nargs == 1:
            new_data = np.apply_along_axis(f, 0, self.data)
            print new_data[0]
            return TimeSeries(new_data, self.times, self.ions)
        else:
            d = np.vstack(self.times, self.data.T)
            nd = np.array([f(*i) for i in d])
            return TimeSeries(nd[:, 0], nd[:, 1:], self.ions)

    def _apply_data(self, f, ts):
        """
        Convenience function for all of the math stuff.
        """
        if type(ts) == int or type(ts) == float:
            d = ts * np.ones(self.data.shape[0])
        elif ts is None:
            d = None
        elif all(ts.times == self.times):
            d = ts.data[:, 0]
        else:
            d = ts._retime(self.times)[:, 0]

        new_data = np.apply_along_axis(f, 0, self.data, d)
        return TimeSeries(new_data, self.times, self.ions)

    def __add__(self, ts):
        return self._apply_data(lambda x, y: x + y, ts)

    def __sub__(self, ts):
        return self._apply_data(lambda x, y: x - y, ts)

    def __mul__(self, ts):
        return self._apply_data(lambda x, y: x * y, ts)

    def __div__(self, ts):
        return self._apply_data(lambda x, y: x / y, ts)

    def __reversed(self):
        raise NotImplementedError

    def __iadd__(self, ts):
        return self._apply_data(lambda x, y: x + y, ts)

    def __isub__(self, ts):
        return self._apply_data(lambda x, y: x - y, ts)

    def __imul__(self, ts):
        return self._apply_data(lambda x, y: x * y, ts)

    def __idiv__(self, ts):
        return self._apply_data(lambda x, y: x / y, ts)

    def __neg__(self):
        return self._apply_data(lambda x, y: -x, None)

    def __abs__(self):
        return self._apply_data(lambda x, y: abs(x), None)

    def __and__(self, ts):
        #TODO: merge the ions together if they're the same
        data = np.hstack([self.data, ts._retime(self.times)])
        ions = self.ions + ts.ions
        ts = TimeSeries(data, self.times, ions)
        return ts
