import os
import os.path as op
import binascii
import re
import struct
from itertools import product
from glob import glob
import inspect
from importlib import import_module

from aston.resources import cache

#File types from http://en.wikipedia.org/wiki/Mass_spectrometry_data_format
#and http://www.amdis.net/What_is_AMDIS/AMDIS_Detailed/amdis_detailed.html
#TODO: .FID | Bruker instrument data format
#TODO: .LRP | Shrader/GCMate
#TODO: .MS  | Varian Saturn Files
#TODO: .MS  | HP Benchtop and MS Engines
#TODO: .MS  | Finnigan (GCQ,INCOS and ITDS formats) also *.MI & *.DAT
#TODO: .MSF | Bruker
#TODO: .PKL | MassLynx associated format
#TODO: .RAW | Micromass MassLynx directory format
#TODO: .RAW | PerkinElmer TurboMass file format
#TODO: .SMS | Saturn SMS
#TODO: .WIFF| ABI/Sciex (QSTAR and QTRAP instrument) format
#TODO: .YEP | Bruker instrument data format


@cache(maxsize=1)
def tfclasses():
    """
    A list of every class for reading data files.
    """
    # automatically find any subclasses of TraceFile in the same
    # directory as me
    classes = []
    mydir = op.dirname(op.abspath(inspect.getfile(file_type)))
    tfcls = ("<class 'aston.tracefile.TraceFile.TraceFile'>",
             "<class 'aston.tracefile.TraceFile.ScanListFile'>")
    for filename in glob(op.join(mydir, '*.py')):
        name = op.splitext(op.basename(filename))[0]
        module = import_module('aston.tracefile.' + name)
        for clsname in dir(module):
            cls = getattr(module, clsname)
            if hasattr(cls, '__base__'):
                if str(cls.__base__) in tfcls:
                    classes.append(cls)
    return classes


@cache(maxsize=1)
def tfclasses_lookup():
    """
    Create a lookup table for determining what type a file might
    potentially be.
    """
    def mi(d):
        """
        Make something iterable, if it's not already (but not strings).
        """
        if isinstance(d, (tuple, list)):
            return d
        else:
            return (d,)

    # create the lookup table
    lookup = {}
    for cls in tfclasses():
        for mgc, ext, fnm in product(mi(cls.mgc), mi(cls.ext), mi(cls.fnm)):
            if mgc is None:
                if fnm is not None:
                    lookup[fnm] = cls.__name__
                else:
                    lookup[ext] = cls.__name__
            else:
                if fnm is not None:
                    lookup[fnm + '|' + mgc] = cls.__name__
                else:
                    lookup[ext + '|' + mgc] = cls.__name__
    return lookup


def file_type(filename):
    tflookup = tfclasses_lookup()

    # try to get extension and magic byte info
    fn = op.split(filename)[1].upper()
    ext = os.path.splitext(filename)[1].upper()[1:]
    try:  # TODO: replace with a 'with' statement?
        f = open(filename, mode='rb')
        magic = binascii.b2a_hex(f.read(2)).decode('ascii').upper()
        f.close()
        # some entries in tfclasses have a full file name to match
        if fn + '|' + magic in tflookup:
            ftype = tflookup[fn + '|' + magic]
        else:
            ftype = tflookup.get(ext + '|' + magic, None)
    except IOError:
        ftype = None

    if ftype is None:
        if fn in tflookup:
            ftype = tflookup[fn]
        else:
            ftype = tflookup.get(ext, None)
    return ftype


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
    # TODO: rewrite to use re library
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
