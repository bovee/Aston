# -*- coding: utf-8 -*-

#    Copyright 2011-2013 Roderick Bovee
#
#    This file is part of Aston.
#
#    Aston is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Aston is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Aston.  If not, see <http://www.gnu.org/licenses/>.


"""

"""

import json
import zlib
import struct
import numpy as np
from scipy.sparse import coo_matrix
from scipy.interpolate import interp1d


class TimeSeries(object):
    def __init__(self, data, times, ions=[]):
        if data is not None:
            if len(data.shape) == 1:
                data = np.atleast_2d(data).T
                if ions == []:
                    ions = ['']
            assert times.shape[0] == data.shape[0]
            assert len(ions) == data.shape[1]
        self._rawdata = data
        self.times = times
        self.ions = ions

    def _slice_idxs(self, twin=None):
        """
        Returns a slice of the incoming array filtered between
        the two times specified. Assumes the array is the same
        length as self.data. Acts in the time() and trace() functions.
        """
        if twin is None:
            return 0, self._rawdata.shape[0]

        tme = self.times.copy()

        if twin[0] is None:
            st_idx = 0
        else:
            st_idx = (np.abs(tme - twin[0])).argmin()
        if twin[1] is None:
            en_idx = self._rawdata.shape[0]
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

    def twin(self, twin):
        st_idx, en_idx = self._slice_idxs(twin)
        return TimeSeries(self._rawdata[st_idx:en_idx], \
                          self.times[st_idx:en_idx], self.ions)

    def trace(self, val='TIC', tol=0.5, twin=None):
        st_idx, en_idx = self._slice_idxs(twin)

        if val == 'TIC' and 'TIC' not in self.ions:
            # if a TIC is being requested and we don't have
            # a prebuilt one, sum up the axes
            data = self._rawdata[st_idx:en_idx, :].sum(axis=1)
            #TODO: this fails for sparse matrices?
            #data = np.array(self._rawdata[st_idx:en_idx, :].sum(axis=0).T)[0]
        elif val == '!':
            # this is for peaks, where we return the first
            # ion by default; should be accessible from the
            # ions dialog box because !'s are stripped out
            data = self._rawdata[st_idx:en_idx, 0]
            val = self.ions[0]
        else:
            # depending on the val, find the rows differently
            if type(val) is int or type(val) is float:
                #FIXME: this doesn't track the new positions
                # in the array "ions" back the positions in
                # self.ions
                is_num = lambda i: type(i) is int or \
                  type(i) is float or type(i) is np.float32
                ions = np.array([i for i in self.ions if is_num(i)])
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
                data = self._rawdata[st_idx:en_idx, rows].sum(axis=1)
        return TimeSeries(data, self.times[st_idx:en_idx], [val])

    def scan(self, time, to_time=None):
        """
        Returns the spectrum from a specific time.
        """
        idx = (np.abs(self.times - time)).argmin()
        if to_time is None:
            if type(self._rawdata) == np.ndarray:
                ion_abs = self._rawdata[idx, :].copy()
            else:
                ion_abs = self._rawdata[idx, :].astype(float).toarray()[0]
            #return np.array(self.ions), ion_abs
            return np.vstack([np.array([float(i) for i in self.ions]), \
              ion_abs])
        else:
            en_idx = (np.abs(self.times - to_time)).argmin()
            idx, en_idx = min(idx, en_idx), max(idx, en_idx)
            if type(self._rawdata) == np.ndarray:
                ion_abs = self._rawdata[idx:en_idx + 1, :].copy()
            else:
                ion_abs = self._rawdata[idx:en_idx + 1, :].astype(float).toarray()[0]
            return np.vstack([np.array([float(i) for i in self.ions]), \
              ion_abs.sum(axis=0)])

    def get_point(self, trace, time):
        """
        Return the value of the trace at a certain time.
        """
        ts = self.trace(trace)
        f = interp1d(ts.times, ts.data.T, \
          bounds_error=False, fill_value=0.0)
        return f(time)[0]

    def as_2D(self):
        ext = (self.times[0], self.times[-1], min(self.ions), max(self.ions))
        if type(self._rawdata) == np.ndarray:
            grid = self._rawdata[:, np.argsort(self.ions)].transpose()
        else:
            data = self._rawdata[:, 1:].tocoo()
            data_ions = np.array([self.ions[i] for i in data.col])
            grid = coo_matrix((data.data, (data_ions, data.row))).toarray()
        return ext, grid

    def plot(self, show=False):
        """
        Plots the top trace in matplotlib.  Useful for data exploration on
        the commandline; not used in the PyQt gui.
        """
        import matplotlib.pyplot as plt
        plt.plot(self.times, self.y)
        if show:
            plt.show()

    def retime(self, new_times):
        return TimeSeries(self._retime(new_times), new_times, self.ions)

    def _retime(self, new_times, fill=0.0):
        if new_times.shape == self.times.shape:
            if np.all(np.equal(new_times, self.times)):
                return self._rawdata
        f = lambda d: interp1d(self.times, d, \
            bounds_error=False, fill_value=fill)(new_times)
        return np.apply_along_axis(f, 0, self._rawdata)

    def adjust_time(self, offset=0.0, scale=1.0):
        t = scale * self.times + offset
        return TimeSeries(self._rawdata, t, self.ions)

    def has_ion(self, ion):
        if ion in self.ions:
            return True
        try:  # in case ion is not a number
            if float(ion) in self.ions:
                return True
        except ValueError:
            pass
        return False

    def _apply_data(self, f, ts):
        """
        Convenience function for all of the math stuff.
        """
        if type(ts) == int or type(ts) == float:
            d = ts * np.ones(self._rawdata.shape[0])
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

    def __truediv__(self, ts):
        return self.__div__(ts)

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
        if ts is None:
            return self
        t_step = self.times[1] - self.times[0]
        b_time = min(self.times[0], ts.times[0] + \
                     (self.times[0] - ts.times[0]) % t_step)
        e_time = max(self.times[-1], ts.times[-1] + t_step - \
                     (ts.times[-1] - self.times[-1]) % t_step)
        t = np.arange(b_time, e_time, t_step)
        x0 = self._retime(t, fill=np.nan)
        x1 = ts._retime(t, fill=np.nan)
        data = np.hstack([x0, x1])
        ions = self.ions + ts.ions
        ts = TimeSeries(data, t, ions)
        return ts

    @property
    def y(self):
        return self.data.T[0]

    @property
    def data(self):
        if type(self._rawdata) == np.ndarray:
            return self._rawdata
        elif type(self._rawdata) == np.matrix:
            #TODO: something is initializing me with a matrix?
            # happens somewhere in the sparse decomposition code
            return self._rawdata.A
        else:
            return self._rawdata.astype(float).toarray()

    def compress(self):
        d = self.data.tostring()
        t = self.times.astype(float).tostring()
        lt = struct.pack('<L', len(t))
        i = json.dumps(self.ions).encode('utf-8')
        li = struct.pack('<L', len(i))
        try:  # python 2
            return buffer(zlib.compress(li + lt + i + t + d))
        except NameError:  # python 3
            return zlib.compress(li + lt + i + t + d)


def decompress_to_ts(zdata):
    data = zlib.decompress(zdata)
    li = struct.unpack('<L', data[0:4])[0]
    lt = struct.unpack('<L', data[4:8])[0]
    i = json.loads(data[8:8 + li].decode('utf-8'))
    t = np.fromstring(data[8 + li:8 + li + lt])
    d = np.fromstring(data[8 + li + lt:])

    return TimeSeries(d.reshape(len(t), len(i)), t, i)


def ts_func(f):
    """
    This wraps a function that would normally only accept an array
    and allows it to operate on a TimeSeries. Useful for applying
    numpy functions to TimeSeries.
    """
    def wrap_func(ts, *args):
        return TimeSeries(f(ts.y, *args), ts.times)
    return wrap_func
