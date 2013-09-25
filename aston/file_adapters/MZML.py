import zlib
import base64
from xml.etree import ElementTree
from pandas import DataFrame
from aston.file_adapters.Common import FileAdapter


class mzXML(FileAdapter):
    ext = 'MZXML'
    mgc = None


class mzML(FileAdapter):
    ext = 'MZML'
    mgc = None

    def data(self):
        r = ElementTree.parse(self.rawdata).getroot()
        s = r.findall('*//{http://psi.hupo.org/ms/mzml}spectrumList/')
        d = None
        data = zlib.decompress(base64.b64decode(d))
        return DataFrame()
