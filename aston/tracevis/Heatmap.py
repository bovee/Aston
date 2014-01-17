import numpy as np


def as_2d(df):
    """
    Returns two matrices, one of the data and the other of
    the times and trace corresponding to that data.

    Useful for making two-dimensional "heat" plots.
    """
    ions = df.columns
    ext = (df.index[0], df.index[-1], min(ions), max(ions))
    grid = df.values[:, np.argsort(df.columns)].transpose()
    return ext, grid
