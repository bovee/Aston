# -*- coding: utf-8 -*-

from sqlalchemy import Column, Integer, UnicodeText, Unicode, \
                       ForeignKey, SmallInteger, Float, Boolean
from sqlalchemy.orm import relationship
from aston.resources import cache
from aston.database import Base, JSONDict
from aston.database.File import Run
from aston.database.Peak import DBPeak
from aston.database.User import Group
from aston.trace.Trace import AstonSeries
from aston.trace.Parser import parse_ion_string
from aston.trace.Parser import istr_type, istr_best_2d_source, token_source
from aston.trace.MathFrames import molmz, mzminus, basemz


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
    #fake = Column(Binary????, default=None)
    #TODO: need some way to add in Aston-generated chromatograms
    # e.g. predictions, etc
    # save here? or save generating function here?

    _parent = None

    @property
    def _children(self):
        return self.plots

    @cache(maxsize=8)
    def datafile(self, source):
        # find the data source
        for a in self.run.analyses:
            if source in [i.lstrip('#*') for i in a.trace.split(',')]:
                return a.datafile

    def avail_sources(self):
        return [i.lstrip('#*') for a in self.run.analyses \
                for i in a.trace.split(',')]

    def trace(self, istr, twin=None):
        istr, source = token_source(istr, self.avail_sources())
        if source is None:
            return AstonSeries()

        df = self.datafile(source)
        if istr in {'coda', 'rnie', 'wmsm'}:
            #TODO: allow more complicated options to turn
            #AstonFrames into plotable AstonSeries

            #coda
            # Windig W: The use of the Durbin-Watson criterion for
            # noise and background reduction of complex liquid
            # chromatography/mass spectrometry data and a new algorithm
            # to determine sample differences. Chemometrics and
            # Intelligent Laboratory Systems. 2005, 77:206-214.

            #rnie
            # Yunfei L, Qu H, and Cheng Y: A entropy-based method
            # for noise reduction of LC-MS data. Analytica Chimica
            # Acta 612.1 (2008)

            #wmsm
            # Fleming C et al. Windowed mass selection method:
            # a new data processing algorithm for LC-MS data.
            # Journal of Chromatography A 849.1 (1999) 71-85.
            pass
        elif istr.startswith('m_'):
            if istr == 'm_':
                m = 0
            else:
                m = float(istr.split('_')[1])
            return mzminus(df.data, m)
        elif istr == 'molmz':
            return molmz(df.data)
        elif istr == 'basemz':
            return basemz(df.data)
        elif istr in {'r45std', 'r46std'}:
            #TODO: calculate isotopic data
            pass
            # calculate isotopic reference for chromatogram
            #if name == 'r45std':
            #    topion = 45
            #else:
            #    topion = 46
            #std_specs = [o for o in \
            #  self.children_of_type('peak') \
            #  if o.info['p-type'] == 'Isotope Standard']
            #x = [float(o.info['p-s-time']) for o in std_specs]
            #y = [o.area(topion) / o.area(44) for o in std_specs \
            #     if o.area(44) != 0]
            #if len(x) == 0 or len(y) == 0:
            #    return self._const(0.0, twin)

            #p0 = [y[0], 0]
            #errfunc = lambda p, x, y: p[0] + p[1] * x - y
            #try:
            #    p, succ = leastsq(errfunc, p0, args=(np.array(x), \
            #                                         np.array(y)))
            #except:
            #    p = p0
            #sim_y = np.array(errfunc(p, t, np.zeros(len(t))))
            #return TimeSeries(sim_y, t, [name])
        else:
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

            try:
                return df.trace(istr, tol, twin=twin)
            except ValueError:
                return None


class Plot(Base):
    __tablename__ = 'plots'
    _plot_id = Column(Integer, primary_key=True)
    _paletterun_id = Column(Integer, ForeignKey('paletteruns._paletterun_id'))
    peaks = relationship(DBPeak, backref='dbplot')
    vis = Column(SmallInteger, default=1)
    name = Column(UnicodeText, default=u'TIC')
    style = Column(Unicode(16), default=u'auto')
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
                                     self.paletterun.avail_sources())
        if source is None:
            #FIXME: still nothing, return blank scan object
            return
        else:
            # adjust the time appropriately
            t = (t - self.x_offset) / self.x_scale
            if dt is not None:
                dt /= self.x_scale
            # find the scan
            scan = self.paletterun.datafile(source).scan(t, dt)
            scan.source = source
            return scan

    def trace(self, twin=None):
        #TODO: should we just handle events in parse_ion_string?
        name_type = istr_type(self.name.lower())
        if name_type == 'events':
            return AstonSeries()

        # get a trace given my name
        tr_resolver = self.paletterun.trace
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
                                     self.paletterun.avail_sources())
        return self.paletterun.datafile(source).data

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
            #TODO: plot in here
            pass
        elif name_type == '1d' and style not in {'heatmap', 'colors'}:
            trace = self.trace(twin)
            if trace is None:
                return
            ls = {'solid': '-', 'dash': '--', 'dot': ':', \
                  'dash-dot': '-.'}
            trace.plot(ax=ax, style=ls[style], color=color, label=label)
        elif name_type == '2d':
            #TODO: use colors
            self.frame(twin).plot(style=style, ax=ax)
