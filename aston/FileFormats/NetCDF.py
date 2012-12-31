from scipy.io.netcdf import NetCDFFile
from aston.Datafile import Datafile


class NetCDF(Datafile):
    ext = 'CDF'
    mgc = '4344'

    def _cache_data(self):
        if self.data is not None:
            return
        f = NetCDFFile(open(self.rawdata, 'rb'))
        pass


write_netcdf(dt):
    raise NotImplementedError
