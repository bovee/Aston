from aston.Math.Other import delta13C


def test_d13c():
    r45sam, r46sam = 1.1354, 1.4054
    d13cstd = -43.411
    r45std, r46std = 1.4432, 1.1646
    assert delta13C(r45sam, r46sam, d13cstd, r45std, r46std) == -44.0
