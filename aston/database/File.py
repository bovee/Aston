# -*- coding: utf-8 -*-

import os.path as op
from sqlalchemy import Column, Integer, UnicodeText, Unicode, ForeignKey
from sqlalchemy.orm import relationship
from aston.resources import cache
from aston.database import Base, JSONDict
from aston.database.User import Group
from aston.trace.Trace import AstonSeries
from aston.tracefile.TraceFile import TraceFile
from aston.trace.Parser import token_source
from aston.trace.MathFrames import molmz, mzminus, basemz


class Project(Base):
    __tablename__ = 'projects'
    _project_id = Column(Integer, primary_key=True)
    _group_id = Column(Integer, ForeignKey('groups._group_id'))
    group = relationship(Group)
    runs = relationship('Run', backref='project')
    name = Column(Unicode(255))
    directory = Column(UnicodeText)

    _parent = None

    @property
    def _children(self):
        return self.runs


class Run(Base):
    __tablename__ = 'runs'
    _run_id = Column(Integer, primary_key=True)
    _project_id = Column(Integer, ForeignKey('projects._project_id'))
    analyses = relationship('Analysis', backref='run')
    name = Column(Unicode(255))
    path = Column(UnicodeText)
    #method_id = Column(Integer)
    info = Column(JSONDict)
    #fake = Column(Binary????, default=None)
    #TODO: need some way to add in Aston-generated chromatograms
    # e.g. predictions, etc
    # save here? or save generating function here?

    @property
    def _parent(self):
        return self.project

    _children = []

    @cache(maxsize=8)
    def datafile(self, source):
        # find the data source
        for a in self.analyses:
            if source in [i.lstrip('#*') for i in a.trace.split(',')]:
                return a.datafile

    def avail_sources(self):
        return [i.lstrip('#*') for a in self.analyses \
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

            return df.trace(istr, tol, twin=twin)
            #try:
            #    return df.trace(istr, tol, twin=twin)
            #except ValueError:
            #    return None


class Analysis(Base):
    __tablename__ = 'analyses'
    _analysis_id = Column(Integer, primary_key=True)
    _run_id = Column(Integer, ForeignKey('runs._run_id'))
    path = Column(UnicodeText)
    filetype = Column(Unicode(32))
    trace = Column(UnicodeText)

    @property
    def name(self):
        return op.split(self.path)[1]

    @property
    def datafile(self):
        return TraceFile(op.join(self.run.project.directory, self.path),
                         self.filetype)
