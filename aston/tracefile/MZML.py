import zlib
import base64
from xml.etree import ElementTree
from pandas import DataFrame
from aston.tracefile.Common import TraceFile


class mzXML(TraceFile):
    ext = 'MZXML'


class mzML(TraceFile):
    ext = 'MZML'

    @property
    def data(self):
        r = ElementTree.parse(self.filename).getroot()
        s = r.findall('*//{http://psi.hupo.org/ms/mzml}spectrumList/')
        d = None
        data = zlib.decompress(base64.b64decode(d))
        return DataFrame()
