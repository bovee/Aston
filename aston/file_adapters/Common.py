import re
import struct
from pandas import Series, DataFrame


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


class FileAdapter(object):
    def __init__(self, filename):
        self.rawdata = filename

    def data(self):
        return DataFrame()

    def total_trace(self, twin=None):
        return self.data().sum(axis=1)

    def named_trace(self, name, twin=None):
        return Series()

    def info(self):
        return {}

    def events(self, kind):
        return []
