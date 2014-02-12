#from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import Table, Column, Integer, ForeignKey, UnicodeText, \
                       Boolean, Unicode
from sqlalchemy.orm import mapper, deferred
from aston.database import Base, JSONDict, AstonFrameBinary
from aston.peaks.Peak import Peak

peaks = Table('peaks', Base.metadata,
              Column('_peak_id', Integer, primary_key=True),
              Column('_plot_id', Integer, ForeignKey('plots._plot_id')),
              Column('name', UnicodeText),
              Column('vis', Boolean, default=True),
              Column('color', Unicode(16), default=u'auto'),
              Column('hints', JSONDict),
              Column('primary_mz', UnicodeText),
              Column('trace', AstonFrameBinary),
              Column('baseline', AstonFrameBinary)
              )

#parent and children properties declared in aston.peak.Peak
#TODO: move them here somehow?

DBPeak = mapper(Peak, peaks, properties={
    'trace': deferred(peaks.c.trace),
    'baseline': deferred(peaks.c.baseline),
})

#mapper(Peak, peaks, properties={
#})

#@property
#def parent(self):
#    return self.plot

#children = []

#def set_peak(self, trace, baseline=None):
#    """
#    Store data in a newly created DBPeak.
#    """
#    self.trace = trace.reset_index().values
#    self.mz = ','.join(str(i) for i in trace.columns)
#    if baseline is not None:
#        self.baseline = baseline.reset_index().values

#def contains(self, x, y):
#    x = (x - self.plot.x_offset) / self.plot.x_scale
#    y = (y - self.plot.y_offset) / self.plot.y_scale
#    return super(DBPeak, self).contains(x, y)
