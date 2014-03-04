import os.path as op
from sqlalchemy import Column, Integer, UnicodeText, Unicode, ForeignKey
from sqlalchemy.orm import relationship
from aston.database import Base, JSONDict
from aston.database.User import Group
from aston.tracefile.TraceFile import TraceFile


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

    @property
    def _parent(self):
        return self.project

    _children = []


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
