from scipy.optimize import root


def delta13C(r45sam, r46sam, d13cstd, r45std, r46std):
    """
    Given the measured isotope signals of a sample and a
    standard and the delta-13C of that standard, calculate
    the delta-13C of the sample.

    Algorithm from Santrock, Studley & Hayes 1985 Anal. Chem.
    """
    # function for calculating 17R from 18R
    A, K = 0.5164, 0.0092
    c17 = lambda r: K * r ** A

    rcpdb, rosmow = 0.011237, 0.002005

    #known delta values for the ref peak
    r13std = (d13cstd / 1000. + 1) * rcpdb
    r18std = (0 / 1000. + 1) * rosmow  # approx. shouldn't affect results much

    #determine the correction factors
    c45 = r13std + 2 * c17(r18std)
    c46 = c17(r18std) ** 2 + 2 * r13std * c17(r18std) + 2 * r18std

    #correct the voltage ratios to ion ratios
    r45 = (r45sam / r45std) * c45
    r46 = (r46sam / r46std) * c46

    rf = lambda r18: -3 * c17(r18) ** 2 + 2 * r45 * c17(r18) + 2 * r18 - r46
    r18 = root(rf, r18std).x[0]
    r13 = r45 - 2 * c17(r18)
    print(r13)
    return 1000 * (r13 / rcpdb - 1)
