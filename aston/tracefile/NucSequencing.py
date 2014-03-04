"""
For fun, some common 'chromatogram' formats used in DNA sequencing.

"""
from aston.tracefile.TraceFile import TraceFile


class AB1File(TraceFile):
    ext = ('AB1', 'ABI')
    mgc = '4142'


class StandardChromatogramFormat(TraceFile):
    ext = 'SCF'
    mgc = '2E73'
