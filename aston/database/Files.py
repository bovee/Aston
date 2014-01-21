from sqlalchemy import Column, Integer, UnicodeText, Unicode, ForeignKey
from sqlalchemy.orm import relationship
from aston.database import Base, JSONDict


class Project(Base):
    __tablename__ = 'projects'
    _project_id = Column(Integer, primary_key=True)
    _group_id = Column(Integer)
    runs = relationship('Run', backref='project')
    name = Column(Unicode(255))


class Run(Base):
    __tablename__ = 'runs'
    _run_id = Column(Integer, primary_key=True)
    _group_id = Column(Integer)
    _project_id = Column(Integer, ForeignKey('projects._project_id'))
    analyses = relationship('Analysis', backref='run')
    name = Column(Unicode(255))
    path = Column(UnicodeText)
    #method_id = Column(Integer)
    #other = Column(JSONDict)

    def plot_trace(self, trace, ax=None):
        pass


class Analysis(Base):
    __tablename__ = 'analyses'
    _analysis_id = Column(Integer, primary_key=True)
    _run_id = Column(Integer, ForeignKey('runs._run_id'))
    path = Column(UnicodeText)
    filetype = Column(Unicode(32))
    trace = Column(Unicode(32))
    other = Column(JSONDict)
