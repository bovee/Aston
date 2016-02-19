from aston.spectra.isotopes import delta13C_Santrock


def test_delta13c():
    r45sam, r46sam = 1.1399413, 1.5258049
    d13cstd = -43.411
    r45std, r46std = 1.1331231, 1.4058630
    d13c = delta13C_Santrock(r45sam, r46sam, d13cstd, r45std, r46std,
                    ks='Isodat', d18ostd=-21.097)
    assert abs(d13c - (-40.30)) < 0.002
