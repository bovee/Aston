import numpy as np
import scipy.io.wavfile
import scipy.signal
from pandas import Series, DataFrame


class AstonSeries(Series):
    def plot(self, color=None, ax=None):
        pass


class AstonFrame(DataFrame):
    def twin(self, st_t, en_t):
        """
        Time window
        """
        if st_t is None:
            st_idx = 0
        else:
            st_idx = (np.abs(self.index - st_t)).arg_min()

        if en_t is None:
            en_idx = -1
        else:
            en_idx = (np.abs(self.index - en_t)).arg_min()

        return self[st_idx:en_idx]

    def trace(self, name='tic', twin=None):
        pass

    def plot(self, style='heatmap', color=None, ax=None):
        #styles: 2d, colors, otherwise interpret as trace?
        if ax is None:
            import matplotlib.pyplot as plt
            ax = plt.gca()

        if style == 'heatmap':
            ions = self.columns
            ext = (self.index[0], self.index[-1], min(ions), max(ions))
            grid = self.values[:, np.argsort(self.columns)].transpose()
            pass
        elif style == 'colors':
            pass
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
        #TODO: option for averaging spectra instead of summing?
        # "aggfunc"
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
        return np.vstack([self.columns, mz_abn])
