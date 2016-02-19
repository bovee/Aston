import numpy as np
import scipy.sparse
from scipy.io.netcdf import NetCDFFile
from aston.trace.trace import Chromatogram, Trace
from aston.tracefile import TraceFile


class NetCDF(TraceFile):
    mime = 'application/netcdf'
    traces = ['#ms']

    def total_trace(self, twin=None):
        f = NetCDFFile(open(self.filename, 'rb'))
        tme = f.variables['scan_acquisition_time'].data / 60.
        tic = f.variables['total_intensity'].data
        return Trace(tic, tme, name='TIC')

    @property
    def data(self):
        f = NetCDFFile(open(self.filename, 'rb'))
        t = f.variables['scan_acquisition_time'].data / 60.

        # this is half the speed of the following code
        # ions = list(set(f.variables['mass_values'].data))
        # cols = np.array([ions.index(i) for i in \
        #                  f.variables['mass_values'].data])

        # TODO: slow; there has to be a way to vectorize this more?
        ions = np.array(list(set(f.variables['mass_values'].data)))
        rcols = f.variables['mass_values'].data
        cols = np.empty(rcols.shape, dtype=int)
        for i, ion in enumerate(ions):
            cols[rcols == ion] = i

        vals = f.variables['intensity_values'].data
        rowst = np.add.accumulate(f.variables['point_count'].data)
        rowst = np.insert(rowst, 0, 0)

        data = scipy.sparse.csr_matrix((vals, cols, rowst),
                                       shape=(len(t), len(ions)), dtype=float)
        return Chromatogram(data.todense(), t, ions)


def write_netcdf(filename, df, info=None):
    # FIXME: still a lot of issues here
    if info is None:
        info = {}

    f = NetCDFFile(filename, 'w', version=1)

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

    # TODO: check that these do anything
    f.createDimension('instrument_number', 1)
    f.createDimension('range', 2)
    f.flush()

    f.dataset_completeness = 'C1'  # TODO: save peaks too? ('C1+C2')
    f.aia_template_revision = '1.0'
    f.ms_template_revision = '1.0.1'
    f.netcdf_revision = '2.3.2'
    f.languages = 'English'

    f.administrative_comments = 'none'
    f.dataset_origin = 'none'
    f.dataset_owner = ' '
    f.dataset_date_time_stamp = ' '
    f.flush()

    f.company_method_name = ' '
    f.pre_experiment_program_name = ' '
    f.post_experiment_program_name = ' '
    f.source_file_reference = ' '

    f.experiment_title = info.get('name', ' ')
    f.operator_name = info.get('operator', ' ')
    # TODO: wrong format for injection_date_time_stamp
    # example: 20141027123030-0500
    f.injection_date_time_stamp = info.get('date', ' ')
    f.company_method_id = info.get('method', ' ')
    f.sample_name = info.get('sample', ' ')
    f.flush()

    f.sample_id_comments = 'none'
    f.sample_id = 'none'
    f.sample_name = 'none'
    f.sample_type = 'none'
    f.sample_injection_volume = 'none'
    f.sample_amount = 'none'
    f.flush()

    f.retention_unit = 'Seconds'

    # TODO: need to merge this back into access method
    if hasattr(df.values, 'todense'):
        scan_locs = (df.values != 0).todense()
    else:
        scan_locs = df.values != 0

    f.createVariable('error_log', 'c', ('error_number', '_64_byte_string'))

    f.createDimension('scan_number', len(df.index))
    v = f.createVariable('scan_acquisition_time', '>d', ('scan_number',))
    v[:] = 60. * df.index.astype('d')
    v = f.createVariable('total_intensity', '>d', ('scan_number',))
    v[:] = df.values.sum(axis=1).astype('d').flatten()
    v = f.createVariable('point_count', '>i', ('scan_number',))
    v[:] = np.sum(scan_locs, axis=1).astype('i').flatten()
    f.flush()

    f.createDimension('point_number', np.sum(scan_locs))
    stretch_t = np.resize(df.index, df.values.T.shape).T
    v = f.createVariable('mass_values', '>f', ('point_number',))
    v[:] = stretch_t[scan_locs]
    v = f.createVariable('intensity_values', '>f', ('point_number',))
    if hasattr(df.values, 'todense'):
        v[:] = df.values.todense()[scan_locs]
    else:
        v[:] = df.values[scan_locs]

    # TODO: check that these do anything
    # f.createVariable('time_values', 'd', ('point_number',))
    v = f.createVariable('resolution', 'd', ('scan_number',))
    v[:] = -9999
    f.createVariable('actual_scan_number', 'i', ('scan_number',))
    v[:] = -9999
    f.createVariable('scan_index', 'i', ('scan_number',))
    v[:] = np.cumsum(np.sum(scan_locs, axis=1).astype('i'))
    f.createVariable('mass_range_min', 'd', ('scan_number',))
    v[:] = np.min(stretch_t[scan_locs]) * np.ones(stretch_t.shape[0])
    v = f.createVariable('mass_range_max', 'd', ('scan_number',))
    v[:] = np.max(stretch_t[scan_locs]) * np.ones(stretch_t.shape[0])
    v = f.createVariable('a_d_sampling_rate', 'd', ('scan_number',))
    v[:] = -9999
    v = f.createVariable('a_d_coaddition_factor', 'h', ('scan_number',))
    v[:] = -9999
    v = f.createVariable('flag_count', 'i', ('scan_number',))
    v[:] = 0
    f.createVariable('inter_scan_time', 'd', ('scan_number',))
    v[0] = 0
    v[1:] = np.diff(df.index.astype('d'))
    f.createVariable('scan_duration', 'd', ('scan_number',))
    v[:] = 1
    v = f.createVariable('time_range_min', 'd', ('scan_number',))
    v[:] = -9999
    v = f.createVariable('time_range_max', 'd', ('scan_number',))
    v[:] = -9999

    inst_tup = ('instrument_number', '_32_byte_string')
    f.createVariable('instrument_serial_no', 'c', inst_tup)
    f.createVariable('instrument_fw_version', 'c', inst_tup)
    f.createVariable('instrument_app_version', 'c', inst_tup)
    f.createVariable('instrument_os_version', 'c', inst_tup)
    f.createVariable('instrument_sw_version', 'c', inst_tup)
    f.createVariable('instrument_comments', 'c', inst_tup)
    f.createVariable('instrument_model', 'c', inst_tup)
    f.createVariable('instrument_name', 'c', inst_tup)
    f.createVariable('instrument_id', 'c', inst_tup)
    f.createVariable('instrument_mfr', 'c', inst_tup)

    f.close()
