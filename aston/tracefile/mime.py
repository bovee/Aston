import binascii
from glob import glob
import inspect
from importlib import import_module
import mimetypes
import os
import os.path as op

from aston.cache import cache


# File types from http://en.wikipedia.org/wiki/Mass_spectrometry_data_format
# and http://www.amdis.net/What_is_AMDIS/AMDIS_Detailed/amdis_detailed.html
# TODO: .FID | Bruker instrument data format
# TODO: .LRP | Shrader/GCMate
# TODO: .MS  | Varian Saturn Files
# TODO: .MS  | HP Benchtop and MS Engines
# TODO: .MS  | Finnigan (GCQ,INCOS and ITDS formats) also *.MI & *.DAT
# TODO: .MSF | Bruker
# TODO: .PKL | MassLynx associated format
# TODO: .RAW | Micromass MassLynx directory format
# TODO: .RAW | PerkinElmer TurboMass file format
# TODO: .SMS | Saturn SMS
# TODO: .WIFF| ABI/Sciex (QSTAR and QTRAP instrument) format
# TODO: .YEP | Bruker instrument data format

mimes = """
image/png	png	8950
application/fasta   fa,fasta,fna,faa                3E
text/csv            csv                             *
application/mzxml	mzxml	*
application/mzml	mzml	*
application/netcdf  cdf                             4344
application/fcs     fcs,lmd                         46435333
application/vnd-sequencing-ab1	ab1,abi	4142
application/vnd-sequencing-scf	scf	2E73
application/vnd-agilent-chemstation-pump	lpmp1.reg	0233
application/vnd-agilent-chemstation-fraction	lafc1fd.reg	0233
application/vnd-agilent-chemstation-flowinject	acqres.reg	0233
application/vnd-agilent-chemstation-lcstat	lcdiag.reg	0233
application/vnd-agilent-chemstation-flowinject	acqres.reg	0233
application/vnd-agilent-masshunter-pump	cappump.cd	*
application/vnd-agilent-masshunter-temp	tcc1.cd	*
application/vnd-agilent-masshunter-acqmethod	acq_method.xml	*
application/vnd-agilent-masshunter-sampleinfo	sample_info.xml	*
application/vnd-agilent-masshunter-msmsscan  bin          0101
application/vnd-agilent-masshunter-dad  sd          *
application/vnd-agilent-chemstation-fid	ch	0238
application/vnd-agilent-chemstation-fid2	ch	0331
application/vnd-agilent-chemstation-ms  ms          0132
application/vnd-agilent-chemstation-mwd  ch          0233
application/vnd-agilent-chemstation-mwd2  ch          0331
application/vnd-agilent-chemstation-dad  uv          0233
application/vnd-agilent-chemstation-dad2  uv          0331
application/vnd-bruker-msms  ami          *
application/vnd-bruker-baf  baf          2400
application/vnd-inficon-hapsite  hps          0403
application/vnd-sciex-wiff	wiff	D0CF
application/vnd-thermo-cf  cf          FFFF
application/vnd-thermo-dxf  dxf          FFFF
application/vnd-thermo-raw  raw          01A1
application/vnd-waters-autospec  idx          *
"""


def get_mimetype(filename, magic_all):
    ft_magic = {}
    ft_ext = {}
    for line in mimes.strip('\n').split('\n'):
        mime, ext, magic = line.split()
        if magic != '*':
            for m in magic.split(','):
                ft_magic[m] = mime

        if ext != '*':
            for e in ext.split(','):
                ft_ext[e] = mime

    # TODO: maybe do some kind of ranking?
    # need to allow multiple filetypes for common magic/extensions
    for i in [4, 2, 1]:
        magic = binascii.b2a_hex(magic_all[:i]).decode('ascii').upper()
        if magic in ft_magic:
            return ft_magic[magic]

    if filename is not None:
        ext = os.path.splitext(filename)[1].lower()[1:]
        if ext in ft_ext:
            return ft_ext[ext]

    return mimetypes.guess_type(filename)[0]


@cache(maxsize=1)
def tfclasses():
    """
    A mapping of mimetypes to every class for reading data files.
    """
    # automatically find any subclasses of TraceFile in the same
    # directory as me
    classes = {}
    mydir = op.dirname(op.abspath(inspect.getfile(get_mimetype)))
    tfcls = {"<class 'aston.tracefile.TraceFile'>",
             "<class 'aston.tracefile.ScanListFile'>"}
    for filename in glob(op.join(mydir, '*.py')):
        name = op.splitext(op.basename(filename))[0]
        module = import_module('aston.tracefile.' + name)
        for clsname in dir(module):
            cls = getattr(module, clsname)
            if hasattr(cls, '__base__'):
                if str(cls.__base__) in tfcls:
                    classes[cls.mime] = cls
    return classes
