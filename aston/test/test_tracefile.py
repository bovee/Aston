from aston.tracefile import TraceFile

DXF_FILE = './data/test.dxf'


def test_thermo_dxf():
    df = TraceFile(DXF_FILE)
    assert len(df.events()) > 0
    assert df.data.columns == [44, 45, 46]
