import numpy as np
import scipy.sparse
from scipy.io.netcdf import NetCDFFile
from pandas import DataFrame, Series
from aston.tracefile.TraceFile import TraceFile


class NetCDF(TraceFile):
    ext = 'CDF'
    mgc = '4344'
    traces = ['#ms']

    def total_trace(self, twin=None):
        f = NetCDFFile(open(self.filename, 'rb'))
        tme = f.variables['scan_acquisition_time'].data / 60.
        tic = f.variables['total_intensity'].data
        return Series(tic, tme, name='TIC')

    @property
    def data(self):
        f = NetCDFFile(open(self.filename, 'rb'))
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
        return DataFrame(data.todense(), t, ions)


def write_netcdf(filename, df, info=None):
    #FIXME: still a lot of issues here
    if info is None:
        info = {}

    f = NetCDFFile(filename, 'w')

    f.createDimension('_2_byte_string', 2)
    f.createDimension('_4_byte_string', 4)
    f.createDimension('_8_byte_string', 8)
    f.createDimension('_16_byte_string', 16)
    f.createDimension('_32_byte_string', 32)
    f.createDimension('_64_byte_string', 64)
    f.createDimension('_128_byte_string', 128)
    f.createDimension('_255_byte_string', 255)
    f.createDimension('error_number', 1)
    f.flush()

    f.dataset_completeness = 'C1'  # TODO: save peaks too? ('C1+C2')
    f.netcdf_revision = '2.3.2'
    f.languages = 'English'
    f.flush()

    f.experiment_title = info.get('name', ' ')
    f.operator_name = info.get('operator', ' ')
    # TODO: wrong format for injection_date_time_stamp
    f.injection_date_time_stamp = info.get('date', ' ')
    f.company_method_id = info.get('method', ' ')
    f.sample_name = info.get('sample', ' ')
    f.flush()

    f.createDimension('scan_number', len(df.index))
    v = f.createVariable('scan_acquisition_time', '>d', ('scan_number',))
    v[:] = df.index.astype('d')
    v = f.createVariable('total_intensity', '>d', ('scan_number',))
    v[:] = df.sum(axis=1).astype('d')
    v = f.createVariable('point_count', '>i', ('scan_number',))
    v[:] = np.sum(df.values != 0, axis=1).astype('i')
    f.flush()

    f.createDimension('point_number', np.sum(df.values != 0))
    stretch_t = np.resize(df.index, df.values.T.shape).T
    v = f.createVariable('mass_values', '>f', ('point_number',))
    v[:] = stretch_t[df.values != 0]
    v = f.createVariable('intensity_values', '>f', ('point_number',))
    v[:] = df.values[df.values != 0]

    f.close()
