import os.path as op
from sqlalchemy import Column, Integer, UnicodeText, Unicode, ForeignKey
from sqlalchemy.orm import relationship
from aston.database import Base, JSONDict
from aston.tracefile.TraceFile import TraceFile


class Project(Base):
    __tablename__ = 'projects'
    _project_id = Column(Integer, primary_key=True)
    _group_id = Column(Integer)
    runs = relationship('Run', backref='project')
    name = Column(Unicode(255))
    directory = Column(UnicodeText)

    parent = None

    @property
    def children(self):
        return self.runs


class Run(Base):
    __tablename__ = 'runs'
    _run_id = Column(Integer, primary_key=True)
    _group_id = Column(Integer)
    _project_id = Column(Integer, ForeignKey('projects._project_id'))
    analyses = relationship('Analysis', backref='run')
    name = Column(Unicode(255))
    path = Column(UnicodeText)
    #method_id = Column(Integer)
    other = Column(JSONDict)

    @property
    def parent(self):
        return self.project

    @property
    def children(self):
        return self.analyses


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
    def parent(self):
        return self.run

    children = []

    @property
    def datafile(self):
        #TODO: use filetype
        return TraceFile(op.join(self.run.project.directory, self.path))
