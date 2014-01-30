from sqlalchemy import Column, Integer, ForeignKey, Float
from aston.database import Base, JSONDict


class DBPeak(Base):
    __tablename__ = 'peaks'
    _peak_id = Column(Integer, primary_key=True)
    _trace_id = Column(Integer, ForeignKey('traces._trace_id'))
    time = Column(Float)  # start time/end time?
    int_hints = Column(JSONDict)  # integration hints
    baseline = Column(Integer)  # TODO: some reference to a baseline?

    @property
    def parent(self):
        return trace

    children = []
