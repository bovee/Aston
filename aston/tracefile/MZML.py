import re
import zlib
import base64
from xml.etree import ElementTree
import numpy as np
from pandas import DataFrame, Series
from aston.tracefile.TraceFile import TraceFile


def t_to_min(x):
    """
    Convert XML 'xs: duration type' to decimal minutes, e.g.:
    t_to_min('PT1H2M30S') == 62.5
    """
    g = re.match('PT(?:(.*)H)?(?:(.*)M)?(?:(.*)S)?', x).groups()
    return sum(0 if g[i] is None else float(g[i]) * 60. ** (1 - i) \
                for i in range(3))


#class mzXML(TraceFile):
class mzXML(object):
    ext = 'MZXML'
    traces = ['#ms']

    ns = {'m': 'http://sashimi.sourceforge.net/schema_revision/mzXML_2.1'}

    @property
    def data(self):
        # get all the scans under the root node
        r = ElementTree.parse(self.filename).getroot()
        s = r.findall('*//m:scan', namespaces=self.ns)

        for scn in s:
            #scn.get('peaksCount')
            # extract out the actual scan data
            pks = scn.find('m:peaks', namespaces=self.ns)
            dtype = {'32': '>f4', '64': '>f8'}.get(pks.get('precision'))
            d = np.frombuffer(base64.b64decode(pks.text), dtype)
            mz = d[::2]
            abn = d[1::2]

    def total_trace(self, twin=None):
        #TODO: use twin
        #TODO: only get the scans with totIonCurrent; if none found
        # calculate from the data

        r = ElementTree.parse(self.filename).getroot()
        s = r.findall('*//m:scan', namespaces=self.ns)
        d = np.array([float(i.get('totIonCurrent')) for i in s])
        t = np.array([t_to_min(i.get('retentionTime')) for i in s])
        return Series(d, t, name='TIC')


class mzML(TraceFile):
    ext = 'MZML'
    traces = ['#ms']

    @property
    def data(self):
        r = ElementTree.parse(self.filename).getroot()
        s = r.findall('*//{http://psi.hupo.org/ms/mzml}spectrumList/')
        d = None
        data = zlib.decompress(base64.b64decode(d))
        return DataFrame()


def write_mzxml(df, info=None, precision='f'):
    """
    Precision is either f or d.
    """
    for r in df.values:
        df.columns
        pass


def write_mzml(df, info=None):
    pass
