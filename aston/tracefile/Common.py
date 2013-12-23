import os
import re
import binascii
import struct
import numbers
import numpy as np
from pandas import Series, DataFrame

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


def tfclasses():
    """
    A list of every TraceFile we support.
    """
    from aston.tracefile.AgilentMS import AgilentMS, AgilentMSMSScan
    from aston.tracefile.Thermo import ThermoCF, ThermoDXF
    from aston.tracefile.Bruker import BrukerMSMS
    from aston.tracefile.AgilentUV import AgilentDAD, AgilentMWD, \
            AgilentMWD2, AgilentCSDAD, AgilentCSDAD2
    from aston.tracefile.OtherFiles import AgilentFID, CSVFile
    from aston.tracefile.Waters import WatersAutospec
    from aston.tracefile.NetCDF import NetCDF
    from aston.tracefile.Inficon import InficonHapsite
    return [AgilentMS, AgilentMSMSScan, BrukerMSMS, \
      ThermoCF, ThermoDXF, AgilentDAD, AgilentMWD, AgilentMWD2, \
      AgilentCSDAD, AgilentCSDAD2, AgilentFID, CSVFile, \
      WatersAutospec, NetCDF, InficonHapsite]

    #for cls_str in dir(fl):
    #    cls = fl.__dict__[cls_str]
    #    if hasattr(cls, '__base__'):
    #        if cls.__base__ == aston.Datafile.Datafile:
    #            pass


def tfclasses_lookup():
    lookup = {}
    for cls in tfclasses():
        if cls.mgc is None:
            lookup[cls.ext] = cls.__name__
        elif type(cls.mgc) == tuple:
            for mgc in cls.mgc:
                lookup[cls.ext + '.' + mgc] = cls.__name__
        else:
            lookup[cls.ext + '.' + cls.mgc] = cls.__name__
    return lookup


def find_offset(f, search_str, hint=None):
    if hint is None:
        hint = 0
    f.seek(hint)
    regexp = re.compile(search_str)
    while True:
        d = f.read(len(search_str) * 200)
        srch = regexp.search(d)
        if srch is not None:
            foff = f.tell() - len(d) + srch.end()
            break
        if len(d) == len(search_str):  # no data read: EOF
            return None
        f.seek(f.tell() - len(search_str))
    return foff


def parse_c_serialized(f):
    """
    Reads in a binary file created by a C++ serializer (prob. MFC?)
    and returns tuples of (header name, data following the header).
    These are used by Thermo for *.CF and *.DXF files and by Agilent
    for new-style *.REG files.
    """
    #TODO: rewrite to use re library
    f.seek(0)
    try:
        p_rec_type = None
        while True:
            rec_off = f.tell()
            while True:
                if f.read(2) == b'\xff\xff':
                    h = struct.unpack('<HH', f.read(4))
                    if h[1] < 64 and h[1] != 0:
                        rec_type = f.read(h[1])
                        if rec_type[0] == 67:  # starts with 'C'
                            break
                if f.read(1) == b'':
                    raise EOFError
                f.seek(f.tell() - 2)
            if p_rec_type is not None:
                rec_len = f.tell() - 6 - len(rec_type) - rec_off
                f.seek(rec_off)
                yield p_rec_type, f.read(rec_len)
                f.seek(f.tell() + 6 + len(rec_type))
            p_rec_type, p_type = rec_type, h[0]
    except EOFError:
        rec_len = f.tell() - 6 - len(rec_type) - rec_off
        f.seek(rec_off)
        yield p_rec_type, f.read(rec_len)


class TraceFile(object):
    ext = None
    mgc = None

    def __init__(self, filename=None, ftype=None, data=None):
        self.filename = filename
        self.ftype = ''
        self._data = None

        if type(self) is TraceFile:
            if data is not None:
                self._data = data

            if filename is None:
                return

            if ftype is None:
                # guess my type and subclass myself
                ext = os.path.splitext(filename)[1].upper()[1:]
                try:
                    f = open(filename, mode='rb')
                    magic = binascii.b2a_hex(f.read(2)).decode('ascii').upper()
                    f.close()
                    ftype = tfclasses_lookup().get(ext + '.' + magic, None)
                except IOError:
                    ftype = None

                if ftype is None:
                    ftype = tfclasses_lookup().get(ext, None)

            if ftype is not None:
                # try to automatically subclass myself to provided type
                for cls in tfclasses():
                    if cls.__name__ == ftype:
                        self.__class__ = cls
                        self.ftype = ftype
        else:
            self.ftype = self.__class__

    @property
    def data(self):
        if self._data is not None:
            return self._data
        else:
            return DataFrame()

    def total_trace(self, twin=None):
        d = self.data.sum(axis=1)
        if twin is not None:
            return d[d.between(twin[0], twin[1])]
        else:
            return d

    def trace_names(self, named=True):
        if named:
            return []
        else:
            return self.data.columns

    def trace(self, name='', tol=0.5, twin=None):
        # this is the only string we handle; all others handled in subclasses
        if name in ['', 'X', 'TIC']:
            return self.total_trace(twin)

        # if the string is actually a number, handle that
        try:
            name = float(name)
        except TypeError:
            pass

        # try to quickly extract the relevant trace
        if isinstance(name, numbers.Number):
            col_nums = self.data.columns.values.astype(float)
            cols = np.where(np.abs(col_nums - name) <= tol)[0]
            d = self.data[self.data.columns[cols]].sum(axis=1)
        elif name in self.data.columns:
            d = self.data[name]
        else:
            d = Series()

        # return the appropriate time window of the trace
        if twin is not None:
            return d[d.between(twin[0], twin[1])]
        else:
            return d

    def scan(self, time, to_time=None, aggfunc=np.sum):
        """
        Returns the spectrum from a specific time or range of times.
        """
        #FIXME: use aggfunc
        t = self.data.index.values
        idx = (np.abs(t - time)).argmin()
        if to_time is None:
            ion_abs = self.data.values[idx, :].copy()
            return np.vstack([self.data.columns, ion_abs])
        else:
            en_idx = (np.abs(t - to_time)).argmin()
            idx, en_idx = min(idx, en_idx), max(idx, en_idx)
            ion_abs = self.data.values[idx:en_idx + 1, :].copy()
            return np.vstack([self.data.columns, ion_abs.sum(axis=0)])

    @property
    def info(self):
        #TODO: add creation date and short name
        return {'filename': self.filename,
                'filetype': self.ftype}

    def events(self, kind):
        return []
