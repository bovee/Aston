from collections import OrderedDict
import numpy as np
from scipy.optimize import fsolve

# using 23.5 as a default d18o assuming no fractionation
# during combustion; actual combustion produces values
# lower than this. See Schumacher et al 2008 Atm Chem & Phys Dis


def delta13c_constants():
    """
    Constants for calculating delta13C values from ratios.
    From website of Verkouteren & Lee 2001 Anal. Chem.
    """
    # possible values for constants (from NIST)
    cst = OrderedDict()
    cst['Craig'] = {'S13': 0.0112372, 'S18': 0.002079,
                    'K': 0.008333, 'A': 0.5}
    cst['IAEA'] = {'S13': 0.0112372, 'S18': 0.00206716068,
                   'K': 0.0091993, 'A': 0.5}
    cst['Werner'] = {'S13': 0.0112372, 'S18': 0.0020052,
                     'K': 0.0093704, 'A': 0.516}
    cst['Santrock'] = {'S13': 0.0112372, 'S18': 0.0020052,
                       'K': 0.0099235, 'A': 0.516}
    cst['Assonov'] = {'S13': 0.0112372, 'S18': 0.0020052,
                      'K': 0.0102819162, 'A': 0.528}
    cst['Assonov2'] = {'S13': 0.0111802, 'S18': 0.0020052,
                       'K': 0.0102819162, 'A': 0.528}
    cst['Isodat'] = {'S13': 0.0111802, 'S18': 0.0020052,
                     'K': 0.0099235, 'A': 0.516}
    return cst


def delta13c_craig(r45sam, r46sam, d13cstd, r45std, r46std,
                   ks='Craig', d18ostd=23.5):
    """
    Algorithm from Craig 1957.

    From the original Craig paper, we can set up a pair of equations
    and solve for d13C and d18O simultaneously:

        d45 * r45 = r13 * d13
                  + 0.5 * r17 * d18
        d46 = r13 * ((r17**2 + r17 - r18) / a) * d13
            + 1 - 0.5 * r17 * ((r13**2 + r13 - r18) / a) * d18
        where a = r18 + r13 * r17 and b = 1 + r13 + r17
    """
    # the constants for the calculations
    # originally r13, r17, r18 = 1123.72e-5, 759.9e-6, 415.8e-5
    k = delta13c_constants()[ks]

    # TODO: not clear why need to multiply by 2?
    r13, r18 = k['S13'], 2 * k['S18']
    r17 = 2 * (k['K'] * k['S18'] ** k['A'])
    a = (r18 + r13 * r17) * (1. + r13 + r17)

    # the coefficients for the calculations
    eqn_mat = np.array([[r13, 0.5 * r17],
                        [r13 * ((r17 ** 2 + r17 - r18) / a),
                         1 - 0.5 * r17 * ((r13 ** 2 + r13 - r18) / a)]])

    # precalculate the d45 and d46 of the standard versus PDB
    r45d45std = (eqn_mat[0, 0] * d13cstd + eqn_mat[0, 1] * d18ostd)
    d46std = eqn_mat[1, 0] * d13cstd + eqn_mat[1, 1] * d18ostd

    # calculate the d45 and d46 of our sample versus PDB
    # in r45d45, r45 of PDB = r13 + r17 of PDB
    r45d45 = 1000. * (r45sam / r45std - 1.) * \
        (r13 + r17 + 0.001 * r45d45std) + r45d45std
    d46 = 1000. * (r46sam / r46std - 1.) * (1. + 0.001 * d46std) + d46std

    # solve the system of equations
    x = np.linalg.solve(eqn_mat, np.array([r45d45, d46]))
    return x[0]


def delta13c_santrock(r45sam, r46sam, d13cstd, r45std, r46std,
                      ks='Santrock', d18ostd=23.5):
    """
    Given the measured isotope signals of a sample and a
    standard and the delta-13C of that standard, calculate
    the delta-13C of the sample.

    Algorithm from Santrock, Studley & Hayes 1985 Anal. Chem.
    """
    k = delta13c_constants()[ks]

    # function for calculating 17R from 18R
    def c17(r):
        return k['K'] * r ** k['A']
    rcpdb, rosmow = k['S13'], k['S18']

    # known delta values for the ref peak
    r13std = (d13cstd / 1000. + 1) * rcpdb
    r18std = (d18ostd / 1000. + 1) * rosmow

    # determine the correction factors
    c45 = r13std + 2 * c17(r18std)
    c46 = c17(r18std) ** 2 + 2 * r13std * c17(r18std) + 2 * r18std

    # correct the voltage ratios to ion ratios
    r45 = (r45sam / r45std) * c45
    r46 = (r46sam / r46std) * c46

    def rf(r18):
        return -3 * c17(r18) ** 2 + 2 * r45 * c17(r18) + 2 * r18 - r46
    # r18 = scipy.optimize.root(rf, r18std).x[0]  # use with scipy 0.11.0
    r18 = fsolve(rf, r18std)[0]
    r13 = r45 - 2 * c17(r18)
    return 1000 * (r13 / rcpdb - 1)


def delta13c_brand(r45sam, r46sam, d13cstd, r45std, r46std):
    """
    Linear simplification from Brand et al. 2010 Pure Appl Chem
    """
    # d13C = d45 + 2 * 0.035168 * (d45 - d46)
    raise NotImplementedError
