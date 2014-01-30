# -*- coding: utf-8 -*-

from sqlalchemy import Column, Integer, UnicodeText, Unicode, \
                       ForeignKey, SmallInteger, Float
from sqlalchemy.orm import relationship
from aston.resources import cache
from aston.database import Base, JSONDict
from aston.database.File import Run
from aston.database.Peak import DBPeak
from aston.trace.Trace import AstonSeries
from aston.trace.Parser import parse_ion_string, tokens


class Palette(Base):
    __tablename__ = 'palettes'
    _palette_id = Column(Integer, primary_key=True)
    _group_id = Column(Integer)
    name = Column(Unicode(64))
    runs = relationship('PaletteRun', backref='palette')
    style = Column(JSONDict)  # TODO: include bounds in style?
    columns = Column(UnicodeText)


class PaletteRun(Base):
    __tablename__ = 'paletteruns'
    _paletterun_id = Column(Integer, primary_key=True)
    _palette_id = Column(Integer, ForeignKey('palettes._palette_id'))
    _run_id = Column(Integer, ForeignKey('runs._run_id'))
    run = relationship(Run)
    traces = relationship('Trace', backref='paletterun')
    #order?
    #stored? allow item to be deleted, but retained in table

    parent = None

    @property
    def children(self):
        return self.traces

    @cache(maxsize=8)
    def datafile(self, source):
        # find the data source
        for a in self.run.analyses:
            if source in [i.lstrip('#') for i in a.trace.split(',')]:
                return a.datafile

    def parse_source(self, istr, guess=True):
        traces_2d = ['ms', 'uv', 'irms']
        child_traces = [i.lstrip('#') for a in self.run.analyses \
                        for i in a.trace.split(',')]

        source = None
        # identify a data source, if present
        if '#' in istr:
            source = '#'.join(istr.split('#')[1:])
            istr = istr.split('#')[0]
        elif istr in child_traces or istr in traces_2d:
            source = istr
            istr = 'tic'
        elif istr in ['tic', 'x', ''] and 'fid' in child_traces:
            source = 'fid'
        elif guess:
            # still don't have a source; assume it's from the 2d traces
            for i in traces_2d:
                if i in child_traces:
                    source = i
                    break
        return istr, source

    def trace(self, istr, twin=None):
        istr, source = self.parse_source(istr)
        if source is None:
            return AstonSeries()

        # interpret tolerances
        if ':' in istr:
            st = float(istr.split(':')[0])
            en = float(istr.split(':')[1])
            tol = 0.5 * (en - st)
            istr = 0.5 * (en + st)
        elif u'±' in istr:
            tol = float(istr.split(u'±')[1])
            istr = float(istr.split(u'±')[0])
        else:
            tol = 0.5

        return self.datafile(source).trace(istr, tol, twin=twin)


class Trace(Base):
    __tablename__ = 'traces'
    _trace_id = Column(Integer, primary_key=True)
    _paletterun_id = Column(Integer, ForeignKey('paletteruns._paletterun_id'))
    peaks = relationship(DBPeak, backref='trace')
    vis = Column(SmallInteger, default=1)
    name = Column(UnicodeText, default=u'TIC')
    style = Column(Unicode(16))
    color = Column(Unicode(16))
    x_offset = Column(Float, default=0)
    x_scale = Column(Float, default=1)
    y_offset = Column(Float, default=0)
    y_scale = Column(Float, default=1)

    @property
    def parent(self):
        return self.paletterun

    @property
    def children(self):
        return self.peaks

    @property
    def source(self):
        for tk in tokens(self.name.lower()):
            _, source = self.paletterun.parse_source(tk, guess=False)
            if source is not None:
                break
        else:
            # we got nothing out of looping through all the traces;
            # give it something that doesn't exist and ask it to guess
            _, source = self.paletterun.parse_source('fake', guess=True)
        return source

    def scan(self, t, dt=None):
        source = self.source
        if source is None:
            #FIXME: still nothing, return blank scan object
            return
        else:
            # adjust the time appropriately
            t = (t - self.x_offset) / self.x_scale
            dt /= self.x_scale
            # find the scan
            scan = self.paletterun.datafile(source).scan(t, dt)
            scan.source = source
            return scan

    def trace(self, twin=None):
        #TODO: transform twin in native coordinates
        # get a trace given my name
        tr_resolver = self.paletterun.trace
        trace = parse_ion_string(self.name.lower(), tr_resolver, twin)
        # offset and scale trace
        trace = trace.adjust_time(offset=self.x_offset, scale=self.x_scale)
        trace = trace * self.y_offset + self.y_scale

        return trace

    def subtraces(self, method=None, twin=None):
        #self.paletterun.datafile(source)
        if method == 'coda':
            pass
        elif method == 'all':
            pass

    def plot(self, ax, twin=None):
        #TODO: need to pass color and style info on?
        trace = self.trace(twin)
        trace.plot(ax=ax)
