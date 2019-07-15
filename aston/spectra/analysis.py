import itertools
import re
from collections import Counter
import numpy as np

abn = {'-': {0.000548: 1},
       'C': {12: 1, 13.00335: 0.0108},
       'H': {1.00782504: 1, 2.01410178: 0.000115},
       'O': {15.99491461956: 1, 16.99913170: 0.00038, 17.9991610: 0.00205},
       'N': {14.0030740048: 1, 15.0001088982: 0.00369},
       'P': {30.97376163: 1},
       'F': {18.99840322: 1},
       'I': {126.904473: 1},
       'Si': {27.9769265325: 1, 28.976494700: 0.050778, 29.97377017: 0.033473},
       'S': {31.97207100: 1, 32.97145876: 0.0080, 33.96786690: 0.0452},
       'Cl': {34.96885268: 1, 36.96590259: 0.3196},
       'Br': {78.9183371: 1, 80.9162906: 0.9728}
       }


def mono_mass(formula):
    mass = 0
    for atom, count in re.findall('([A-Z][a-z]*)(\\d*)', formula):
        if count == '':
            count = 1
        else:
            count = float(count)
        # TODO: assumption is lowest mass isotope is most abundant
        mass += count * min(abn[atom].keys())
    return mass


def all_mass(formula):
    iso_dists = []
    for atom, count in re.findall('([A-Z][a-z]*)(\\d*)', formula):
        if count == '':
            count = 1
        else:
            count = int(count)
        # isotope combinations
        iso_list = list(itertools.product(atom, abn[atom].keys()))
        iso_dists.append(list(itertools.product(*(count * [iso_list]))))
        # itertools.product the result for all atoms to get overall isotope
        # distribution
        # use np.round to get low-resolution mass spectral data
    spec = Counter()
    # sum up everything with a Counter?
    for iso_dist in itertools.product(*iso_dists):
        iso_dist = [i for j in iso_dist for i in j]
        spec[np.round(sum(i[1] for i in iso_dist))] += \
            np.prod([abn[i][j] for i, j in iso_dist])


test = [(354.134499255997, 633504), (355.136551393827, 147822),
        (356.138919219861, 21550), (357.140369476609, 2544)]
test_form = 'C20H19NO5'

# for CO2
# 12 + 2 * 16 (44): abn['C'][12] * abn['O'][16] ** 2
# 12 + 16 + 17 (45): abn['C'][12] * abn['O'][16] * abn['O'][17]
# 12 + 2 * 17 (46):
# 12 + 16 + 18 (46):
# 12 + 17 + 18 (47):
# 12 + 2 * 18 (48):

# and repeat with 13's:

# for C3
# TODO: need coefficients for pascals triange in here
# 3 * 12 - abn['C'][12] ** 3
# 2 * 12 + 13 - comb(3, 1) * abn['C'][12] ** 2 * abn['C'][13.00335]
# 12 + 2 * 13 - comb(3, 2) * abn['C'][12] * abn['C'][13.00335] ** 2
# 3 * 13 - abn['C'][13.00335] ** 3
