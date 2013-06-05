import zlib
import base64
from xml.etree import ElementTree
from aston.features import Datafile


class mzXML(Datafile):
    ext = 'MZXML'
    mgc = None


class mzML(Datafile):
    ext = 'MZML'
    mgc = None

    def _cache_data(self):
        r = ElementTree.parse(self.rawdata).getroot()
        s = r.findall('*//{http://psi.hupo.org/ms/mzml}spectrumList/')
        d = None
        data = zlib.decompress(base64.b64decode(d))
        self.data = TimeSeries()

    def _update_info_from_file(self):
        self.info.update({'r-type': 'Sample'})
