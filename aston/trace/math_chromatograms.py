import numpy as np
from aston.trace import Trace
from aston.trace.math_traces import movingaverage


def molmz(df, noise=10000):
    """
    The mz of the molecular ion.
    """
    d = ((df.values > noise) * df.columns).max(axis=1)
    return Trace(d, df.index, name='molmz')


def mzminus(df, minus=0, noise=10000):
    """
    The abundances of ions which are minus below the molecular ion.
    """
    mol_ions = ((df.values > noise) * df.columns).max(axis=1) - minus
    mol_ions[np.abs(mol_ions) < 0] = 0
    d = np.abs(np.ones(df.shape) * df.columns -
               (mol_ions[np.newaxis].T * np.ones(df.shape))) < 1
    d = (df.values * d).sum(axis=1)
    return Trace(d, df.index, name='m-' + str(minus))


def basemz(df):
    """
    The mz of the most abundant ion.
    """
    # returns the
    d = np.array(df.columns)[df.values.argmax(axis=1)]
    return Trace(d, df.index, name='basemz')


def coda(df, window, level):
    """
    CODA processing from Windig, Phalp, & Payne 1996 Anal Chem
    """
    # pull out the data
    d = df.values

    # smooth the data and standardize it
    smooth_data = movingaverage(d, df.index, window)[0]
    stand_data = (smooth_data - smooth_data.mean()) / smooth_data.std()

    # scale the data to have unit length
    scale_data = d / np.sqrt(np.sum(d ** 2, axis=0))

    # calculate the "mass chromatographic quality" (MCQ) index
    mcq = np.sum(stand_data * scale_data, axis=0) / np.sqrt(d.shape[0] - 1)

    # filter out ions with an mcq below level
    good_ions = [i for i, q in zip(df.columns, mcq) if q >= level]
    return good_ions
