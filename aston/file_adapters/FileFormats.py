#File types from http://en.wikipedia.org/wiki/Mass_spectrometry_data_format
#and http://www.amdis.net/What_is_AMDIS/AMDIS_Detailed/amdis_detailed.html
#TODO: .ABI | DNA Chromatogram format
#TODO: .FID | Bruker instrument data format
#TODO: .LRP | Shrader/GCMate
#TODO: .MS  | Varian Saturn Files
#TODO: .MS  | HP Benchtop and MS Engines
#TODO: .MS  | Finnigan (GCQ,INCOS and ITDS formats) also *.MI & *.DAT
#TODO: .MSF | Bruker
#TODO: .PKL | MassLynx associated format
#TODO: .RAW | Micromass MassLynx directory format
#TODO: .RAW | PerkinElmer TurboMass file format
#TODO: .SCF | "Standard Chromatogram Format" for DNA
#      http://staden.sourceforge.net/manual/formats_unix_2.html
#TODO: .SMS | Saturn SMS
#TODO: .WIFF| ABI/Sciex (QSTAR and QTRAP instrument) format
#TODO: .YEP | Bruker instrument data format

import os
import binascii


def file_adaptors():
    from aston.file_adapters.AgilentMS \
      import AgilentMS, AgilentMSMSScan
    from aston.file_adapters.Thermo \
      import ThermoCF, ThermoDXF
    from aston.file_adapters.Bruker import BrukerMSMS
    from aston.file_adapters.AgilentUV \
      import AgilentDAD, AgilentMWD, AgilentMWD2, \
            AgilentCSDAD, AgilentCSDAD2
    from aston.file_adapters.OtherFiles \
      import AgilentFID, CSVFile
    from aston.file_adapters.Waters import WatersAutospec
    from aston.file_adapters.NetCDF import NetCDF
    from aston.file_adapters.Inficon import InficonHapsite
    return [AgilentMS, AgilentMSMSScan, BrukerMSMS, \
      ThermoCF, ThermoDXF, AgilentDAD, AgilentMWD, AgilentMWD2, \
      AgilentCSDAD, AgilentCSDAD2, AgilentFID, CSVFile, \
      WatersAutospec, NetCDF, InficonHapsite]

    #for cls_str in dir(fl):
    #    cls = fl.__dict__[cls_str]
    #    if hasattr(cls, '__base__'):
    #        if cls.__base__ == aston.Datafile.Datafile:
    #            pass


def ftype_to_class(ftype):
    for cls in file_adaptors():
        if cls.__name__ == ftype:
            return cls
    return None


def ext_to_classtable():
    lookup = {}
    for cls in file_adaptors():
        if cls.mgc is None:
            lookup[cls.ext] = cls.__name__
        elif type(cls.mgc) == tuple:
            for mgc in cls.mgc:
                lookup[cls.ext + '.' + mgc] = cls.__name__
        else:
            lookup[cls.ext + '.' + cls.mgc] = cls.__name__
    return lookup


def get_magic(filename):
    ext = os.path.splitext(filename)[1].upper()[1:]

    #guess the file type
    try:
        f = open(filename, mode='rb')
        magic = binascii.b2a_hex(f.read(2)).decode('ascii').upper()
        f.close()
    except IOError:
        magic = None

    return ext, magic
