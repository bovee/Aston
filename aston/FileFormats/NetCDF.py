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
        tme = f.variables['scan_acquisition_time'].data / 60.
        tic = f.variables['total_intensity'].data
        return TimeSeries(tic, tme, ['TIC'])

    def _cache_data(self):
        if self.data is not None:
            return
        f = NetCDFFile(open(self.rawdata, 'rb'))
        t = f.variables['scan_acquisition_time'].data / 60.

        ## this is half the speed of the following code
        #ions = list(set(f.variables['mass_values'].data))
        #cols = np.array([ions.index(i) for i in \
        #                 f.variables['mass_values'].data])

        #TODO: slow; there has to be a way to vectorize this more?
        ions = np.array(list(set(f.variables['mass_values'].data)))
        rcols = f.variables['mass_values'].data
        cols = np.empty(rcols.shape, dtype=int)
        for i, ion in enumerate(ions):
            cols[rcols == ion] = i

        vals = f.variables['intensity_values'].data
        rowst = np.add.accumulate(f.variables['point_count'].data)
        rowst = np.insert(rowst, 0, 0)

        data = scipy.sparse.csr_matrix((vals, cols, rowst), \
          shape=(len(t), len(ions)), dtype=float)
        self.data = TimeSeries(data, t, ions)


def write_netcdf(dt, filename):
    #f = NetCDFFile(filename, 'w')
    #f.createVariable('scan_acquisition_time', ??, ??)
    #f.createVariable('point_count', ??, ??)
    #f.createVariable('mass_values', ??, ??)
    #f.createVariable('intensity_values', ??, ??)

    raise NotImplementedError
