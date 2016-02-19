'''
Classes that can open chromatographic files and return
info from them or Traces/Chromatograms.
'''

import re
import struct

import numpy as np

from aston.trace import Chromatogram, Trace
from aston.tracefile.mime import get_mimetype, tfclasses


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
            # p_type = h[0]
            p_rec_type = rec_type
    except EOFError:
        rec_len = f.tell() - 6 - len(rec_type) - rec_off
        f.seek(rec_off)
        yield p_rec_type, f.read(rec_len)


class TraceFile(object):
    mime = ''  # mimetype to associate file with (in tracefile.mime)

    # traces is a list of possible traces:
    # each item may start with a * indicating a events
    # a # indicating a 2d trace or nothing indicating a single trace name
    traces = []

    def __init__(self, filename=None, ftype=None, data=None):
        self.filename = filename
        self.ftype = ''
        self._data = None

        # try to automatically change my class to reflect
        # whatever type of file I'm pointing at if not provided
        if type(self) is TraceFile:
            if data is not None:
                self._data = data

            if filename is None:
                return

            with open(filename, mode='rb') as f:
                magic = f.read(4)

            ftype = get_mimetype(filename, magic)

            if ftype is not None:
                if ftype in tfclasses():
                    self.__class__ = tfclasses()[ftype]
                    self.ftype = ftype
        else:
            self.ftype = self.__class__.__name__

    @property
    def data(self):
        if self._data is not None:
            return self._data
        else:
            return Chromatogram()

    def scans(self):
        # TODO: decompose self.data into scans
        pass

    def total_trace(self, twin=None):
        return self.data.trace(twin=twin)

    # TODO: should this code be kept? (needs to be improved, if so)
    # def plot(self, name='', ax=None):
    #     if ax is None:
    #         import matplotlib.pyplot as plt
    #         ax = plt.gca()

    #     for t in self.traces:
    #         if t.startswith('#'):
    #             #self.trace(t[1:]).plot(ax=ax)
    #             self.trace('').plot(ax=ax)
    #         elif t.startswith('*'):
    #             #TODO: plot events
    #             pass
    #         else:
    #             self.trace(t).plot(ax=ax)

    #     #TODO: colors?
    #     #TODO: plot 2d/colors

    def trace(self, name='', tol=0.5, twin=None):
        if isinstance(name, (int, float, np.float32, np.float64)):
            name = str(name)
        else:
            name = name.lower()

        # name of the 2d trace, if it exists
        if any(t.startswith('#') for t in self.traces):
            t2d = [t[1:] for t in self.traces if t.startswith('#')][0]

            # clip out the starting 'MS' if present
            if name.startswith(t2d):
                name = name[len(t2d):]
        else:
            t2d = ''

        # this is the only string we handle; all others handled in subclasses
        if name in ['tic', 'x', '']:
            return self.total_trace(twin)
        elif name in self.traces:
            return self._trace(name, twin)
        elif t2d != '':
            # this file contains 2d data; find the trace in that
            return self.data.trace(name, tol, twin)
        else:
            return Trace()

    def scan(self, t, dt=None, aggfunc=None):
        """
        Returns the spectrum from a specific time or range of times.
        """
        return self.data.scan(t, dt, aggfunc)

    @property
    def info(self):
        # TODO: add creation date and short name
        return {'filename': self.filename,
                'filetype': self.ftype}

    def events(self, name, twin=None):
        # TODO: check for '*' trace in self.traces
        return []

    def subscan(self, name, t, mz):
        """
        Returns a spectra linked to both a time and mz, e.g.
        the daughter scan in an MSMS or a MS scan from a GC-GC.
        """
        pass

    def subscans(self, name, twin=None):
        """
        Returns a list of times with subscans and their associated mzs.

        Preliminary idea:
        If all points in self.data have subscans, return True.
        """
        # example: [0.1], [147, 178]
        return [], []

    def md5hash(self):
        # TODO: calculate md5hash of this file
        # to be used for determining if files in db are unique
        raise NotImplementedError


class ScanListFile(TraceFile):
    def scans(self, twin=None):
        return []

    # TODO: is there a point in creating a data property here? (for heatmaps?)
    # TODO: if so, then need better binning code...

    def total_trace(self, twin=None):
        if twin is None:
            twin = (-np.inf, np.inf)
        times, y = [], []
        for s in self.scans(twin):
            t = float(s.name)
            if t < twin[0]:
                continue
            if t > twin[1]:
                break
            times.append(t)
            y.append(sum(s.abn))
        return Trace(y, times, name='tic')

    def trace(self, name='', tol=0.5, twin=None):
        if twin is None:
            twin = (-np.inf, np.inf)
        if name in {'tic', 'x', ''}:
            return self.total_trace(twin)
        times, y = [], []
        for s in self.scans(twin):
            t = float(s.name)
            if t < twin[0]:
                continue
            if t > twin[1]:
                break
            times.append(t)
            # TODO: this can be vectorized with numpy?
            y.append(sum(j for i, j in zip(s.x, s.abn)
                         if np.abs(i - name) < tol))
        return Trace(y, times, name=name)

    def scan(self, t, dt=None, aggfunc=None):
        # TODO: use aggfunc
        prev_s = None
        bin_scans = []
        for s in self.scans():
            if float(s.name) > t:
                if float(prev_s.name) - t < float(s.name) - t:
                    if dt is None:
                        return prev_s
                    else:
                        bin_scans.append(prev_s)
                elif dt is None:
                    return s
                bin_scans.append(s)
                if float(s.name) > t + dt:
                    break
            prev_s = s
        # merge bin_scans and return
        # FIXME
        pass
