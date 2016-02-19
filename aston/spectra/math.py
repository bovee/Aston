import numpy as np
from scipy.sparse import dia_matrix
from scipy.sparse import lil_matrix

# TODO: implementations of Stein & Scott 1994 algorithms


def find_spectrum_match(spec, spec_lib, method='euclidian'):
    """
    Find spectrum in spec_lib most similar to spec.
    """
    # filter out any points with abundance below 1 %
    # spec[spec / np.sum(spec) < 0.01] = 0
    # normalize everything to sum to 1
    spec = spec / np.max(spec)

    if method == 'dot':
        d1 = (spec_lib * lil_matrix(spec).T).sum(axis=1).A ** 2
        d2 = np.sum(spec ** 2) * spec_lib.multiply(spec_lib).sum(axis=1).A
        dist = d1 / d2
    elif method == 'euclidian':
        # st_spc = spectrum[np.newaxis, :].repeat(spec_lib.shape[0], axis=0)
        st_spc = dia_matrix((spec, [0]), shape=(len(spec), len(spec)))
        # calculate the residual sum of squares from spectrum to library
        dist_sp = spec_lib.multiply(spec_lib) - 2 * spec_lib.dot(st_spc)
        dist = dist_sp.sum(axis=1).A + np.sum(spec ** 2)
    return (dist.argmin(), dist.min())
