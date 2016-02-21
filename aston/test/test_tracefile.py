from aston.tracefile import TraceFile

DXF_FILE = './test_data/b3_alkanes.dxf'
MS_FILE = './test_data/carotenoid_extract.d/MSD1.MS'
UV_FILE = './test_data/carotenoid_extract.d/dad1.uv'


def test_thermo_dxf():
    df = TraceFile(DXF_FILE)
    assert df.info['filetype'] == 'application/vnd-thermo-dxf'
    assert df.info['d13c_std'] == '-43.411'
    assert df.info['d18o_std'] == '0.0'
    assert len(df.events()) > 0
    assert len(df.data) == 14292
    assert df.data.columns == [44, 45, 46]


def test_agilent_ms():
    df = TraceFile(MS_FILE)
    assert df.info['filetype'] == 'application/vnd-agilent-chemstation-ms'
    assert df.info['m-name'] == 'RJBBARUA.M'
    assert df.info['name'] == 'MHL 7M F7'

    data = df.data
    assert data.shape == (2534, 4801)
    assert min(data.columns) == 100.1
    assert max(data.columns) == 999.6


def test_agilent_uv():
    df = TraceFile(UV_FILE)
    assert df.info['filetype'] == 'application/vnd-agilent-chemstation-dad2'

    data = df.data
    assert data.shape == (6744, 300)
    assert min(data.columns) == 200.0
    assert max(data.columns) == 798.0
