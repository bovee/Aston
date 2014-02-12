import struct
import json
import zlib
import numpy as np
import scipy.io.wavfile
import scipy.signal
from pandas import Series, DataFrame
from aston.spectra.Scan import Scan


class AstonSeries(object):
    def __init__(self, data, index, name=''):
        if type(data) is Series:
            self.values = data.values
            self.index = data.index.values
            self.name = data.name
        else:
            self.values = np.array(data)
            self.index = np.array(index)
            self.name = name

    @property
    def shape(self):
        return self.values.shape

    def copy(self):
        return AstonSeries(self.values.copy(), self.index.copy(), self.name)

    def __getitem__(self, index):
        v, i = self.values[index], self.index[index]
        if type(v) is np.ndarray:
            return AstonSeries(v, i, self.name)
        else:
            return v

    def plot(self, style='-', color='k', scale=False, ax=None):
        if ax is None:
            import matplotlib.pyplot as plt
            ax = plt.gca()

        if scale:
            # normalize data to 0 to 1
            y = (self.values - np.min(self.values)) / np.max(self.values)
        else:
            y = self.values

        ax.plot(self.index, y, c=color, ls=style, label=self.name)

    def twin(self, twin):
        st_idx, en_idx = _slice_idxs(self, twin)
        return self[st_idx:en_idx]

    def as_text(self, width=80, height=20):
        raise NotImplementedError
        #break s.index into width chunks
        #find max and min of each chunk along with start and stop?

    def adjust_time(self, offset=0.0, scale=1.0):
        adjs = self.copy()
        adjs.index = adjs.index * scale + offset
        adjs.__class__ = AstonSeries
        return adjs

    def _retime(self, new_times, fill=0.0):
        from scipy.interpolate import interp1d
        if new_times.shape == self.shape[0]:
            if np.all(np.equal(new_times, self.index)):
                return self
        f = lambda d: interp1d(self.index, d, \
            bounds_error=False, fill_value=fill)(new_times)
        return np.apply_along_axis(f, 0, self.values)

    def _apply_data(self, f, ts):
        """
        Convenience function for all of the math stuff.
        """
        if isinstance(ts, (int, float)):
            d = ts * np.ones(self.shape[0])
        elif ts is None:
            d = None
        elif np.array_equal(ts.index, self.index):
            d = ts.values
        else:
            d = ts._retime(self.index)

        new_data = np.apply_along_axis(f, 0, self.values, d)
        return AstonSeries(new_data, self.index, name=self.name)

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

    def compress(self):
        d = self.values.tostring()
        t = self.index.astype(float).tostring()
        lt = struct.pack('<L', len(t))
        i = json.dumps([self.name]).encode('utf-8')
        lc = struct.pack('<L', len(i))
        try:  # python 2
            return buffer(zlib.compress(lc + lt + i + t + d))
        except NameError:  # python 3
            return zlib.compress(lc + lt + i + t + d)


class AstonFrame(DataFrame):
    #def __new__(cls, *args, **kwargs):
    #    self = super(AstonFrame, cls).__new__(cls, *args, **kwargs)
    #    self.__class__ = AstonFrame
    #    return self

    def __getitem__(self, *args):
        ret = super(AstonFrame, self).__getitem__(self, *args)
        if type(ret) is DataFrame:
            ret.__class__ = AstonFrame
        return ret

    def trace(self, name='tic', tol=0.5, twin=None):
        #TODO: aggfunc in here for tic and numeric
        st_idx, en_idx = _slice_idxs(self, twin)

        if isinstance(name, (int, float, np.float32, np.float64)):
            name = str(name)

        if name in ['tic', 'x', '']:
            data = self.values.sum(axis=1)
            name = 'tic'
        elif name == '!':
            data = self[self.columns[0]].values
            name = self.columns[0]
        elif set(name).issubset('1234567890.'):
            cols = np.abs(self.columns.values - float(name)) < tol
            data = self.values[:, cols].sum(axis=1)
        else:
            data = np.zeros(self.shape[0]) * np.nan
            name = ''

        #TODO: better way to coerce this into the right class?
        #TODO: use twin
        return AstonSeries(data, index=self.index, name=name)

    def plot(self, style='heatmap', legend=False, color=None, ax=None):
        #styles: 2d, colors, otherwise interpret as trace?
        if ax is None:
            import matplotlib.pyplot as plt
            ax = plt.gca()

        if style == 'heatmap':
            ions = self.columns
            ext = (self.index[0], self.index[-1], min(ions), max(ions))
            grid = self.values[:, np.argsort(self.columns)].transpose()
            img = ax.imshow(grid, origin='lower', aspect='auto', \
                            extent=ext, cmap=color)
            if legend:
                ax.figure.colorbar(img)
        elif style == 'colors':
            from matplotlib.colors import ListedColormap
            gaussian = lambda wvs, x, w: np.exp(-0.5 * ((wvs - x) / w) ** 2)

            wvs = self.columns.values.astype(float)

            #http://www.ppsloan.org/publications/XYZJCGT.pdf
            vis_filt = np.zeros((3, len(wvs)))
            vis_filt[0] = 1.065 * gaussian(wvs, 595.8, 33.33) \
                        + 0.366 * gaussian(wvs, 446.8, 19.44)
            vis_filt[1] = 1.014 * gaussian(np.log(wvs), np.log(556.3), 0.075)
            vis_filt[2] = 1.839 * gaussian(np.log(wvs), np.log(449.8), 0.051)
            xyz = np.dot(self.values.copy(), vis_filt.T)

            #http://www.brucelindbloom.com/index.html?Eqn_RGB_XYZ_Matrix.html
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
            ax.imshow(cmask, cmap=ListedColormap(rgb), aspect='auto', \
                      extent=(self.index[0], self.index[-1], 0, 1))
            ax.yaxis.set_ticks([])
        else:
            self.trace().plot(color=color, ax=ax)

    def as_sound(self, filename, speed=60, cutoff=50):
        """
        Convert into a WAV file.
        """
        # make a 1d array for the sound
        to_t = lambda t: (t - self.index[0]) / speed
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
            except:
                return 100
            wv = (mz * (max_hz - min_hz) - max_hz * min_mz + min_hz * max_mz) \
                    / (max_mz - min_mz)
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

    def scan(self, t, dt=None, aggfunc=None):
        """
        Returns the spectrum from a specific time.
        """
        idx = (np.abs(self.index.values - t)).argmin()

        if dt is None:
            # only take the spectra at the nearest time
            mz_abn = self.values[idx, :].copy()
        else:
            # sum up all the spectra over a range
            en_idx = (np.abs(self.index.values - t - dt)).argmin()
            idx, en_idx = min(idx, en_idx), max(idx, en_idx)
            if aggfunc is None:
                mz_abn = self.values[idx:en_idx + 1, :].copy().sum(axis=0)
            else:
                mz_abn = aggfunc(self.values[idx:en_idx + 1, :].copy())
        return Scan(self.columns, mz_abn)

    def compress(self):
        d = self.values.tostring()
        t = self.index.values.astype(float).tostring()
        lt = struct.pack('<L', len(t))
        i = json.dumps(self.columns).encode('utf-8')
        lc = struct.pack('<L', len(i))
        try:  # python 2
            return buffer(zlib.compress(lc + lt + i + t + d))
        except NameError:  # python 3
            return zlib.compress(lc + lt + i + t + d)


def decompress(zdata):
    data = zlib.decompress(zdata)
    lc = struct.unpack('<L', data[0:4])[0]
    lt = struct.unpack('<L', data[4:8])[0]
    c = json.loads(data[8:8 + lc].decode('utf-8'))
    t = np.fromstring(data[8 + lc:8 + lc + lt])
    d = np.fromstring(data[8 + lc + lt:])

    if len(c) == 1:
        return AstonSeries(d, t, name=c[0])
    else:
        return AstonFrame(d.reshape(len(t), len(c)), t, c)


def _slice_idxs(df, twin=None):
    """
    Returns a slice of the incoming array filtered between
    the two times specified. Assumes the array is the same
    length as self.data. Acts in the time() and trace() functions.
    """
    if twin is None:
        return 0, df.shape[0]

    if type(df) is AstonFrame:
        tme = df.index.values
    else:
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
