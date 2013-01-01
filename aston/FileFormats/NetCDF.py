import numpy as np
import scipy.sparse
from scipy.io.netcdf import NetCDFFile
from aston.Datafile import Datafile
from aston.TimeSeries import TimeSeries


class NetCDF(Datafile):
    ext = 'CDF'
    mgc = '4344'

    def _total_trace(self, twin=None):
        f = NetCDFFile(open(self.rawdata, 'rb'))
        tme = f.variables['scan_acquisition_time'].data
        tic = f.variables['total_intensity'].data
        return TimeSeries(tic, tme, ['TIC'])

    def _cache_data(self):
        if self.data is not None:
            return
        f = NetCDFFile(open(self.rawdata, 'rb'))
        t = f.variables['scan_acquisition_time'].data
        ions = list(set(f.variables['mass_values'].data))

        #FIXME: the below doesn't work
        #try building the entire 'cols' at once
        #and building up 'rowst' using accumulate (or equiv in Py2)
        pos = 0
        cols = np.empty(f.variables['mass_values'].shape[0])
        rowst = np.empty(len(t) + 1, dtype=int)
        rowst[0] = 0
        for r, num_pt in enumerate(f.variables['point_count']):
            mz = f.variables['mass_values'].data[pos:pos + num_pt]
            cols[pos:pos + num_pt] = np.array([ions.index(i) for i in mz])
            rowst[r + 1] = pos
            pos += num_pt
        print(rowst)
        vals = f.variables['intensity_values'].data
        data = scipy.sparse.csr_matrix((vals, cols, rowst), \
          shape=(len(t), len(ions)), dtype=float)
        return TimeSeries(data, t, ions)


def write_netcdf(dt):
    raise NotImplementedError
