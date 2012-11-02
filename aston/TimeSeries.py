"""

"""

import numpy as np


class TimeSeries(object):
    def __init__(self, data=None, times=np.array([]), ions=[]):
        self.data = data
        self.times = times
        self.ions = ions
        self.scale, self.offset = 1.0, 0.0

    def _slice_idxs(self, twin=None):
        """
        Returns a slice of the incoming array filtered between
        the two times specified. Assumes the array is the same
        length as self.data. Acts in the time() and trace() functions.
        """
        if twin is None:
            return 0, self.data.shape[0]

        tme = self.times.copy()
        if self.scale is not None:
            tme *= self.scale
        if self.offset is not None:
            tme += self.offset

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
        #scale and offset the data appropriately
        if self.scale is not None:
            tme *= self.scale
        if self.offset is not None:
            tme += self.offset
        #return the time series
        return tme

    def len(self, twin=None):
        st_idx, en_idx = self._slice_idxs(twin)
        return en_idx - st_idx

    def trace(self, val='TIC', tol=0.5, twin=None):
        st_idx, en_idx = self._slice_idxs(twin)

        # if a TIC is being requested and we don't have
        # a prebuilt one, sum up the axes and return it
        if val == 'TIC' and 'TIC' not in self.ions:
            return self.time(twin), \
              self.data[st_idx:en_idx, :].sum(axis=1)

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
            return self.time(twin), \
              np.zeros(en_idx - st_idx) * np.nan
        else:
            return self.time(twin), \
              self.data[st_idx:en_idx, rows].sum(axis=1)

    def scan(self, time):
        """
        Returns the spectrum from a specific time.
        """
        if self.offset is not None:
            time -= self.offset
        if self.scale is not None:
            time /= self.scale

        times = self.times.copy()
        idx = (np.abs(times - time)).argmin()
        if type(self.data) == np.ndarray:
            ion_abs = self.data[idx, :].copy()
        else:
            ion_abs = self.data[idx, :].astype(float).toarray()[0]

        return np.array(self.ions), ion_abs
