import struct
import json
import zlib
import numpy as np
import scipy.io.wavfile
import scipy.signal
import scipy.sparse
from scipy.interpolate import interp1d
from aston.spectra import Scan


class Trace(object):
    def __init__(self, data, index=None, name=''):
        # TODO: reenable this without having to import from pandas
        # if isinstance(data, Series):
        #     self.values = data.values
        #     self.index = data.index.values
        #     self.name = data.name
        if index is not None:
            self.values = np.array(data)
            self.index = np.array(index)
            self.name = name
        else:
            # need either one pandas.Series or two np.arrays
            raise TypeError('Trace initialized improperly.')

    @property
    def shape(self):
        return self.values.shape

    def copy(self):
        return Trace(self.values.copy(), self.index.copy(), self.name)

    def __len__(self):
        return self.index.shape[0]

    def __getitem__(self, index):
        v, i = self.values[index], self.index[index]
        if type(v) is np.ndarray:
            return Trace(v, i, self.name)
        else:
            return v

    def plot(self, style='-', color='k', scale=False, label=None, ax=None):
        if ax is None:
            import matplotlib.pyplot as plt
            ax = plt.gca()

        if scale:
            # normalize data to 0 to 1
            y = (self.values - np.min(self.values)) / np.max(self.values)
        else:
            y = self.values

        if label is None:
            label = self.name

        ax.plot(self.index, y, c=color, ls=style, label=label)

    def twin(self, twin):
        st_idx, en_idx = _slice_idxs(self, twin)
        return self[st_idx:en_idx]

    def as_text(self, width=80, height=20):
        raise NotImplementedError
        # break s.index into width chunks
        # find max and min of each chunk along with start and stop?

    def get_point(self, time, interp_method=None):
        # TODO: add more interpolation methods
        if len(self.index) < 2:
            return np.nan
        f = interp1d(self.index, self.values,
                     bounds_error=False, fill_value=0.0)
        return f(time)

    def adjust_time(self, offset=0.0, scale=1.0):
        adjs = self.copy()
        adjs.index = adjs.index * scale + offset
        adjs.__class__ = Trace
        return adjs

    def _retime(self, new_times, fill=0.0):
        # this is not exposed because it returns a raw numpy array
        from scipy.interpolate import interp1d
        if new_times.shape == self.shape[0]:
            if np.all(np.equal(new_times, self.index)):
                return self

        def f(d):
            return interp1d(self.index, d,
                            bounds_error=False, fill_value=fill)(new_times)
        return np.apply_along_axis(f, 0, self.values)

    def _apply_data(self, f, ts, reverse=False):
        """
        Convenience function for all of the math stuff.
        """
        # TODO: needs to catch np numeric types?
        if isinstance(ts, (int, float)):
            d = ts * np.ones(self.shape[0])
        elif ts is None:
            d = None
        elif np.array_equal(ts.index, self.index):
            d = ts.values
        else:
            d = ts._retime(self.index)

        if not reverse:
            new_data = np.apply_along_axis(f, 0, self.values, d)
        else:
            new_data = np.apply_along_axis(f, 0, d, self.values)
        return Trace(new_data, self.index, name=self.name)

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

    # TODO: this should happen in place?
    def __iadd__(self, ts):
        return self._apply_data(lambda x, y: x + y, ts)

    def __isub__(self, ts):
        return self._apply_data(lambda x, y: x - y, ts)

    def __imul__(self, ts):
        return self._apply_data(lambda x, y: x * y, ts)

    def __idiv__(self, ts):
        return self._apply_data(lambda x, y: x / y, ts)

    def __radd__(self, ts):
        return self._apply_data(lambda x, y: x + y, ts, reverse=True)

    def __rsub__(self, ts):
        return self._apply_data(lambda x, y: x - y, ts, reverse=True)

    def __rmul__(self, ts):
        return self._apply_data(lambda x, y: x * y, ts, reverse=True)

    def __rdiv__(self, ts):
        return self._apply_data(lambda x, y: x / y, ts, reverse=True)

    def __neg__(self):
        return self._apply_data(lambda x, y: -x, None)

    def __abs__(self):
        return self._apply_data(lambda x, y: abs(x), None)

    def compress(self):
        i = self.index.astype(np.float32).tostring()
        li = struct.pack('<L', len(i))
        c = json.dumps([self.name]).encode('utf-8')
        lc = struct.pack('<L', len(c))
        v = self.values.astype(np.float64).tostring()
        try:  # python 2
            return buffer(zlib.compress(lc + li + c + i + v))
        except NameError:  # python 3
            return zlib.compress(lc + li + c + i + v)


class Chromatogram(object):
    def __init__(self, data=None, index=None, columns=None, yunits=None):
        self.yunits = yunits
        if data is None:
            self.values = np.array([])
            self.index = np.array([])
            self.columns = ['']
        # TODO: reenable this without having to import from pandas
        # elif isinstance(data, DataFrame):
        #     self.values = data.values
        #     self.index = data.index.values
        #     self.columns = data.columns.values
        elif index is not None:
            # TODO: handle sparse arrays
            if isinstance(data, list):
                self.values = np.array(data)
            else:
                self.values = data
            self.index = np.array(index)
            self.columns = columns
        else:
            # need either one pandas.Series or two np.arrays
            raise TypeError('Chromatogram initialized improperly.')

    @property
    def shape(self):
        return self.values.shape

    def copy(self):
        return Chromatogram(self.values.copy(), self.index.copy(),
                            self.columns.copy())

    def __len__(self):
        return self.index.shape[0]

    def __getitem__(self, key):
        if isinstance(key, tuple):
            # indexing on multiple dimensions
            # TODO: check that dimensions are in right order
            v = self.values[key]
            i = self.index[key[0]]
            c = self.columns[key[1]]
        else:
            if isinstance(key, np.ndarray):
                if len(key.shape) > 1:
                    # indexing with a boolean mask
                    raise NotImplementedError
            v, i = self.values[key], self.index[key]
            c = self.columns

        if len(c) == 1:
            if len(i) == 1:
                return v[0, 0]
            else:
                return Trace(v, i, name=c[0])
        else:
            return Chromatogram(v, i, c)

    @property
    def traces(self):
        """
        Decomposes the Chromatogram into a collection of Traces.

        Returns
        -------
        list
        """
        traces = []
        for v, c in zip(self.values.T, self.columns):
            traces.append(Trace(v, self.index, name=c))
        return traces

    def trace(self, name='tic', tol=0.5, twin=None):
        # TODO: aggfunc in here for tic and numeric
        st_idx, en_idx = _slice_idxs(self, twin)

        if isinstance(name, (int, float, np.float32, np.float64)):
            name = str(name)

        if name in ['tic', 'x', '']:
            data = self.values.sum(axis=1)
            name = 'tic'
        elif name == '!':
            data = self[:, 0]
            name = self.columns[0]
        elif set(name).issubset('1234567890.'):
            cols = np.genfromtxt(np.array(self.columns).astype(bytes))
            cols = np.abs(cols - float(name)) < tol
            if not np.any(cols):
                data = np.zeros(self.shape[0]) * np.nan
            elif isinstance(self.values, scipy.sparse.spmatrix):
                data = self.values[:, cols].toarray().sum(axis=1)
            else:
                data = self.values[:, cols].sum(axis=1)
        else:
            data = np.zeros(self.shape[0]) * np.nan
            name = ''

        # TODO: better way to coerce this into the right class?
        # TODO: use twin
        return Trace(data, index=self.index, name=name)

    def plot(self, style='heatmap', legend=False, cmap=None, ax=None):
        """
        Presents the AstonFrame using matplotlib.

        Parameters
        ----------
        style : {'heatmap', 'colors', ''}
        legend : bool, optional
        cmap: matplotlib.colors.Colormap, optional
        ax : matplotlib.axes.Axes, optional

        """
        # styles: 2d, colors, otherwise interpret as trace?
        if ax is None:
            import matplotlib.pyplot as plt
            ax = plt.gca()

        if style == 'heatmap':
            ions = self.columns
            ext = (self.index[0], self.index[-1], min(ions), max(ions))
            grid = self.values[:, np.argsort(self.columns)].transpose()
            if isinstance(self.values, scipy.sparse.spmatrix):
                grid = grid.toarray()
            img = ax.imshow(grid, origin='lower', aspect='auto',
                            extent=ext, cmap=cmap)
            if legend:
                ax.figure.colorbar(img)
        elif style == 'colors':
            # TODO: importing gaussian at the top leads to a whole
            # mess of dependency issues => fix somehow?
            from aston.peak.peak_models import gaussian
            from matplotlib.colors import ListedColormap

            wvs = np.genfromtxt(np.array(self.columns).astype(bytes))
            # wvs = self.columns.astype(float)

            # http://www.ppsloan.org/publications/XYZJCGT.pdf
            vis_filt = np.zeros((3, len(wvs)))
            vis_filt[0] = 1.065 * gaussian(wvs, x=595.8, w=33.33) + \
                0.366 * gaussian(wvs, x=446.8, w=19.44)
            vis_filt[1] = 1.014 * gaussian(np.log(wvs), x=np.log(556.3),
                                           w=0.075)
            vis_filt[2] = 1.839 * gaussian(np.log(wvs), x=np.log(449.8),
                                           w=0.051)
            if isinstance(self.values, scipy.sparse.spmatrix):
                xyz = np.dot(self.values.toarray(), vis_filt.T)
            else:
                xyz = np.dot(self.values.copy(), vis_filt.T)

            # http://www.brucelindbloom.com/index.html?Eqn_RGB_XYZ_Matrix.html
            xyz_rgb = [[3.2404542, -1.5371385, -0.4985314],
                       [-0.9692660, 1.8760108, 0.0415560],
                       [0.0556434, -0.2040259, 1.0572252]]
            xyz_rgb = np.array(xyz_rgb)
            rgb = np.dot(xyz_rgb, xyz.T).T

            # normalize
            rgb[rgb < 0] = 0
            rgb /= np.max(rgb)
            rgb = 1 - np.abs(rgb)

            # plot
            cmask = np.meshgrid(np.arange(rgb.shape[0]), 0)[0]
            ax.imshow(cmask, cmap=ListedColormap(rgb), aspect='auto',
                      extent=(self.index[0], self.index[-1], 0, 1))
            ax.yaxis.set_ticks([])
        else:
            if cmap is not None:
                color = cmap(0, 1)
            else:
                color = 'k'
            self.trace().plot(color=color, ax=ax)

    def as_sound(self, filename, speed=60, cutoff=50):
        """
        Convert AstonFrame into a WAV file.

        Parameters
        ----------
        filename : str
            Name of wavfile to create.
        speed : float, optional
            How much to speed up for sound recording, e.g. a value of 60
            will turn an hour-long AstonFrame into a minute-long sound clip.
        cutoff : float, optional
            m/z's under this value will be clipped out.
        """
        # make a 1d array for the sound
        def to_t(t):
            return (t - self.index[0]) / speed

        wav_len = int(to_t(self.index[-1]) * 60 * 44100)
        wav = np.zeros(wav_len)

        # create an artificial array to interpolate times out of
        tmask = np.linspace(0, 1, self.shape[0])

        # come up with a mapping from mz to tone
        min_hz, max_hz = 50, 1000
        min_mz, max_mz = min(self.columns), max(self.columns)

        def mz_to_wv(mz):
            """
            Maps a wavelength/mz to a tone.
            """
            try:
                mz = float(mz)
            except ValueError:
                return 100
            wv = (mz * (max_hz - min_hz) -
                  max_hz * min_mz + min_hz * max_mz) / (max_mz - min_mz)
            return int(44100 / wv)

        # go through each trace and map it into the sound array
        for i, mz in enumerate(self.columns):
            if float(mz) < cutoff:
                # clip out mz/wv below a certain threshold
                # handy if data has low level noise
                continue
            print(str(i) + '/' + str(self.shape[1]))
            inter_x = np.linspace(0, 1, wav[::mz_to_wv(mz)].shape[0])
            wav[::mz_to_wv(mz)] += np.interp(inter_x, tmask, self.values[:, i])

        # scale the new array and write it out
        scaled = wav / np.max(np.abs(wav))
        scaled = scipy.signal.fftconvolve(scaled, np.ones(5) / 5, mode='same')
        scaled = np.int16(scaled * 32767)
        scipy.io.wavfile.write(filename, 44100, scaled)

    def scans(self):
        for t in self.index:
            yield self.scan(t)

    def scan(self, t, dt=None, aggfunc=None):
        """
        Returns the spectrum from a specific time.

        Parameters
        ----------
        t : float
        dt : float
        """
        idx = (np.abs(self.index - t)).argmin()

        if dt is None:
            # only take the spectra at the nearest time
            mz_abn = self.values[idx, :].copy()
        else:
            # sum up all the spectra over a range
            en_idx = (np.abs(self.index - t - dt)).argmin()
            idx, en_idx = min(idx, en_idx), max(idx, en_idx)
            if aggfunc is None:
                mz_abn = self.values[idx:en_idx + 1, :].copy().sum(axis=0)
            else:
                mz_abn = aggfunc(self.values[idx:en_idx + 1, :].copy())
        if isinstance(mz_abn, scipy.sparse.spmatrix):
            mz_abn = mz_abn.toarray()[0]
        return Scan(self.columns, mz_abn)

    def compress(self):
        """
        Serializes the AstonFrame into a binary stream.

        Returns
        -------
        bytes
        """
        i = self.index.astype(np.float32).tostring()
        li = struct.pack('<L', len(i))
        c = json.dumps(self.columns).encode('utf-8')
        lc = struct.pack('<L', len(c))
        v = self.values.astype(np.float64).tostring()
        try:  # python 2
            return buffer(zlib.compress(lc + li + c + i + v))
        except NameError:  # python 3
            return zlib.compress(lc + li + c + i + v)


def decompress(zdata):
    """
    Unserializes an AstonFrame.

    Parameters
    ----------
    zdata : bytes

    Returns
    -------
    Trace or Chromatogram

    """
    data = zlib.decompress(zdata)
    lc = struct.unpack('<L', data[0:4])[0]
    li = struct.unpack('<L', data[4:8])[0]
    c = json.loads(data[8:8 + lc].decode('utf-8'))
    i = np.frombuffer(data[8 + lc:8 + lc + li], dtype=np.float32)
    v = np.frombuffer(data[8 + lc + li:], dtype=np.float64)

    if len(c) == 1:
        return Trace(v, i, name=c[0])
    else:
        return Chromatogram(v.reshape(len(i), len(c)), i, c)


def _slice_idxs(df, twin=None):
    """
    Returns a slice of the incoming array filtered between
    the two times specified. Assumes the array is the same
    length as self.data. Acts in the time() and trace() functions.
    """
    if twin is None:
        return 0, df.shape[0]

    tme = df.index

    if twin[0] is None:
        st_idx = 0
    else:
        st_idx = (np.abs(tme - twin[0])).argmin()
    if twin[1] is None:
        en_idx = df.shape[0]
    else:
        en_idx = (np.abs(tme - twin[1])).argmin() + 1
    return st_idx, en_idx
