import numpy as np
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

    def plot(self, style='2d', color=None, ax=None):
        #styles: 2d, colors, otherwise interpret as trace?
        if ax is None:
            import matplotlib.pyplot as plt
            plt.plot()
        else:
            pass

    def as_2d(self):
        """
        Returns two matrices, one of the data and the other of
        the times and trace corresponding to that data.

        Useful for making two-dimensional "heat" plots.
        """
        ions = self.columns
        ext = (self.index[0], self.index[-1], min(ions), max(ions))
        grid = self.values[:, np.argsort(self.columns)].transpose()
        return ext, grid

    def as_sound(self):
        pass

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
