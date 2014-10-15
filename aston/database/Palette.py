# -*- coding: utf-8 -*-

from sqlalchemy import Column, Integer, UnicodeText, Unicode, \
                       ForeignKey, SmallInteger, Float, Boolean
from sqlalchemy.orm import relationship
from aston.database import Base, JSONDict
from aston.database.File import Run
from aston.database.Peak import DBPeak
from aston.database.User import Group
from aston.trace.Trace import AstonSeries
from aston.trace.Events import plot_events
from aston.trace.Parser import parse_ion_string
from aston.trace.Parser import istr_type, istr_best_2d_source


class Palette(Base):
    __tablename__ = 'palettes'
    _palette_id = Column(Integer, primary_key=True)
    _group_id = Column(Integer, ForeignKey('groups._group_id'))
    group = relationship(Group)
    name = Column(Unicode(64))
    runs = relationship('PaletteRun', backref='palette')
    style = Column(JSONDict)  # TODO: include bounds in style?
    columns = Column(UnicodeText, default=u'name,vis,style,color')


class PaletteRun(Base):
    __tablename__ = 'paletteruns'
    _paletterun_id = Column(Integer, primary_key=True)
    _palette_id = Column(Integer, ForeignKey('palettes._palette_id'))
    _run_id = Column(Integer, ForeignKey('runs._run_id'))
    run = relationship(Run)
    plots = relationship('Plot', backref='paletterun')
    enabled = Column(Boolean, default=False)

    _parent = None

    @property
    def _children(self):
        return self.plots


class Plot(Base):
    __tablename__ = 'plots'
    _plot_id = Column(Integer, primary_key=True)
    _paletterun_id = Column(Integer, ForeignKey('paletteruns._paletterun_id'))
    peaks = relationship(DBPeak, backref='dbplot')
    vis = Column(SmallInteger, default=1)
    name = Column(UnicodeText, default=u'TIC')
    style = Column(Unicode(16), default=u'solid')
    color = Column(Unicode(16), default=u'auto')
    x_offset = Column(Float, default=0)
    x_scale = Column(Float, default=1)
    y_offset = Column(Float, default=0)
    y_scale = Column(Float, default=1)
    is_valid = True

    @property
    def _parent(self):
        return self.paletterun

    @property
    def _children(self):
        return self.peaks

    def name_type(self):
        return istr_type(self.name.lower())

    def scan(self, t, dt=None):
        source = istr_best_2d_source(self.name.lower(), \
                                     self.paletterun.run.avail_sources())
        if source is None:
            #FIXME: still nothing, return blank scan object
            return
        else:
            # adjust the time appropriately
            t = (t - self.x_offset) / self.x_scale
            if dt is not None:
                dt /= self.x_scale
            # find the scan
            scan = self.paletterun.run.datafile(source).scan(t, dt)
            scan.source = source
            return scan

    def trace(self, twin=None):
        #TODO: should we just handle events in parse_ion_string?
        name_type = istr_type(self.name.lower())
        #FIXME!!!!!
        if name_type == 'events':
            return AstonSeries()

        # get a trace given my name
        tr_resolver = self.paletterun.run.trace
        trace = parse_ion_string(self.name.lower(), tr_resolver, twin)

        if trace is None:
            self.is_valid = False
            return None
        else:
            self.is_valid = True

        # offset and scale trace
        trace = trace * self.y_scale + self.y_offset
        if type(trace) is AstonSeries:
            trace = trace.adjust_time(offset=self.x_offset, scale=self.x_scale)
        else:
            trace = AstonSeries([trace], [0], name=self.name.lower())

        return trace

    def frame(self, twin=None):
        #TODO: use twin
        source = istr_best_2d_source(self.name.lower(), \
                                     self.paletterun.run.avail_sources())
        return self.paletterun.run.datafile(source).data

    def subtraces(self, method=None, twin=None):
        #self.paletterun.datafile(source)
        if method == 'coda':
            pass
        elif method == 'all':
            pass

    def plot(self, ax, style, color, twin=None):
        name_type = istr_type(self.name.lower())
        label = self.paletterun.run.name + ' ' + self.name
        if name_type == 'events':
            df = self.paletterun.run.datafile(self.name.lower())
            evts = df.events(self.name.lower().lstrip('*'))
            plot_events(evts, color=color, ax=ax)
        elif style in {'heatmap', 'colors'}:
            #TODO: should only be on name_type == '2d' ?
            # need other ui changes first though
            self.frame(twin).plot(style=style, cmap=color, ax=ax)
        else:
            #TODO: should technically only be allowed on 1d plots
            trace = self.trace(twin)
            if trace is None:
                return
            ls = {'solid': '-', 'dash': '--', 'dot': ':', \
                  'dash-dot': '-.'}
            trace.plot(ax=ax, style=ls[style], color=color, label=label)
