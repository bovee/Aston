#from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import Table, Column, Integer, ForeignKey, UnicodeText, \
                       Boolean, Unicode
from sqlalchemy.orm import mapper, deferred, relationship
from aston.database import Base, JSONDict, AstonFrameBinary
from aston.peaks.Peak import Peak, PeakComponent

#parent and children properties declared in aston.peak.Peak
#TODO: move them here somehow?

pkcomponents = Table('peakcomponents', Base.metadata,
                     Column('_peakcomponent_id', Integer, primary_key=True),
                     Column('_peak_id', Integer, ForeignKey('peaks._peak_id')),
                     Column('info', JSONDict),
                     Column('_trace', AstonFrameBinary),
                     Column('baseline', AstonFrameBinary)
                     )

DBPeakComponent = mapper(PeakComponent, pkcomponents, properties={
    '_trace': deferred(pkcomponents.c._trace),
    'baseline': deferred(pkcomponents.c.baseline),
})

peaks = Table('peaks', Base.metadata,
              Column('_peak_id', Integer, primary_key=True),
              Column('_plot_id', Integer, ForeignKey('plots._plot_id')),
              Column('name', UnicodeText),
              Column('info', JSONDict),
              Column('vis', Boolean, default=True),
              Column('color', Unicode(16), default=u'auto'),
              )

DBPeak = mapper(Peak, peaks, properties={
    'components': relationship(DBPeakComponent),
})
