#from io import StringIO
import numpy as np
from aston.trace.trace import Chromatogram
from aston.tracefile.netcdf import write_netcdf


def test_write_netcdf():
    d = np.array([[0.1, 0.2, 0.1, 0.1],
                  [0.5, 0.6, 0.5, 0.4]]).T
    t = np.array([0, 1, 2, 3])
    df = Chromatogram(d, t, ['A', 'B'])
    #f_obj = StringIO()
    write_netcdf('test.cdf', df)
