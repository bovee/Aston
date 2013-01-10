from scipy.optimize import root


def delta13C_Craig(r45sam, r46sam, d13cstd, r45std, r46std):
    """
    Algorithm from Craig 1957; see Brand et al 2010 for more info.
    """
    raise NotImplementedError
    d18o = -22
    d13C = 1.0676 * (r45sam / r45std - 1) - 0.0338 * d18o
    return d13C


def delta13C(r45sam, r46sam, d13cstd, r45std, r46std):
    """
    Given the measured isotope signals of a sample and a
    standard and the delta-13C of that standard, calculate
    the delta-13C of the sample.

    Algorithm from Santrock, Studley & Hayes 1985 Anal. Chem.
    """
    # possible values for constants (from NIST)
    cst = {'Craig': {'S13': 0.0112372, 'S17': 0.00037995,
                     'S18': 0.002079, 'K': 0.008333,
                     'A': 0.5},
           'IAEA': {'S13': 0.0112372, 'S17': 0.000378866601,
                    'S18': 0.00206716068, 'K': 0.0091993,
                    'A': 0.5},
           'Werner': {'S13': 0.0112372, 'S17': 0.0003799,
                      'S18': 0.0020052, 'K': 0.0093704,
                      'A': 0.516},
           'Santrock': {'S13': 0.0112372, 'S17': 0.0004023261,
                        'S18': 0.0020052, 'K': 0.0099235,
                        'A': 0.516},
           'Assonov': {'S13': 0.0112372, 'S17': 0.000386913,
                       'S18': 0.0020052, 'K': 0.0102819162,
                       'A': 0.528},
           'Assonov2': {'S13': 0.0111802, 'S17': 0.000386913,
                        'S18': 0.0020052, 'K': 0.0102819162,
                        'A': 0.528}}
    k = cst['Santrock']

    # function for calculating 17R from 18R
    c17 = lambda r: k['K'] * r ** k['A']

    rcpdb, rosmow = k['S13'], k['S18']

    # approx. shouldn't affect results much
    d18ostd = -21.097

    #known delta values for the ref peak
    r13std = (d13cstd / 1000. + 1) * rcpdb
    r18std = (d18ostd / 1000. + 1) * rosmow

    #determine the correction factors
    c45 = r13std + 2 * c17(r18std)
    c46 = c17(r18std) ** 2 + 2 * r13std * c17(r18std) + 2 * r18std
    print(c45, c46)

    #correct the voltage ratios to ion ratios
    r45 = (r45sam / r45std) * c45
    r46 = (r46sam / r46std) * c46
    print(r45, r46)

    rf = lambda r18: -3 * c17(r18) ** 2 + 2 * r45 * c17(r18) + 2 * r18 - r46
    r18 = root(rf, r18std).x[0]
    r13 = r45 - 2 * c17(r18)
    print(r18, r13)
    return 1000 * (r13 / rcpdb - 1)


def delta13C_Brand(r45sam, r46sam, d13cstd, r45std, r46std):
    d13C = d45 + 2 * 0.035168 * (d45 - d46)
    raise NotImplementedError
