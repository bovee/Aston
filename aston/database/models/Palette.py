from sqlalchemy import Column, Integer, Unicode, UnicodeText,  \
                       Boolean, ForeignKey
from sqlalchemy.orm import relationship
from aston.database.models import Base, JSONDict
from aston.database.models.User import Group
from aston.database.models.Trace import DBTrace


class Palette(Base):
    __tablename__ = 'palettes'
    palette_id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey('groups.group_id'))
    group = relationship(Group)
    name = Column(Unicode(255))
    graph_bounds = Column(UnicodeText)
    graph_style = Column(JSONDict)
    columns = Column(UnicodeText)

    def __init__(self, name, group_id):
        self.name = name
        self.group_id = group_id


class PaletteTrace(Base):
    """
    A palette is a list of chromatograms, active traces on those
    chromatograms, and preferences associated with that view.
    """
    __tablename__ = 'palette_traces'
    chview_id = Column(Integer, primary_key=True)
    view_id = Column(Integer, ForeignKey('palettes.palette_id'))
    view = relationship(Palette)
    cgram_id = Column(Integer, \
                             ForeignKey('traces.trace_id'))
    cgram = relationship(DBTrace)
    visible = Column(Boolean)
    transforms = Column(UnicodeText)  # sample, sample concentration
    traces = Column(UnicodeText)

    def __init__(self, trace_id, view_id):
        self.trace_id = trace_id
        self.view_id = view_id
        self.traces = 'TIC'
        self.visible = False

    def active_traces(self, n=None, twin=None):
        """
        Returns the TimeSeries corresponding to the mzs in self.traces.
        """
        mzs = [mz.strip() for mz in self.traces.split(',')]

        tss = []
        for mz in mzs[:n]:
            ts = self.cgram.trace(mz)
            ts.ions[0] = mz
            tss.append(ts)
        return tss
