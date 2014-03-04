import os
from sqlalchemy import Column, Integer, Unicode, UnicodeText, Enum, \
                       Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship, reconstructor
from sqlalchemy.orm.session import object_session
from aston.database.models import Base, JSONDict
from aston.database.models.Method import Method
from aston.database.models.Peak import Peak, PeakGroup
from aston.database.models.User import Group
from aston.tracefile.Common import TraceFile


class DBTrace(Base):
    __tablename__ = 'traces'
    cgram_id = Column(Integer, primary_key=True)
    name = Column(UnicodeText)
    #method_id = Column(Integer, ForeignKey('methods.method_id'))
    #method = relationship(Method)
    group_id = Column(Integer, ForeignKey('groups.group_id'))
    group = relationship(Group)
    project_id = Column(Integer, ForeignKey('projects.project_id'))
    peaks = relationship(Peak)
    peakgroups = relationship(PeakGroup)
    location = Column(Unicode(255))
    file_type = Column(Unicode(32))  # TODO: make this an Enum and populate it
    date_create = Column(DateTime)
    run_type = Column(Enum('sample', 'standard', 'blank'))  # sample, standard, etc
    other = Column(JSONDict)
    #http://docs.sqlalchemy.org/en/rel_0_7/orm/extensions/mutable.html

    def __init__(self, filename='', ftype=None, path=''):
        self.filename = filename
        if ftype is not None:
            self.file_type = ftype
        else:
            pass  # get file_type from file?
        self._datapath = path

    @reconstructor
    def init_on_load(self):
        self._datapath = object_session(self).execute( \
          'select value from prefs where key="data_directory"').first()[0]

    def trace(self, istr, twin=None):
        basepath = os.path.join(self._datapath, self.filename)
        fadp = FileAdapter(basepath, self.file_type)
        return fadp.trace(istr, twin=twin)

    def load_info_from_file(self):
        # load info into me, saving all the other stuff
        # that doesn't fit my data model into "other"
        basepath = os.path.join(self._datapath, self.filename)
        fadp = FileAdapter(basepath, self.file_type)
        d = fadp.info()
        self.name = d.pop('name', '')
        self.date_create = d.pop('date_create', None)
        self.run_type = d.pop('run_type', None)
        self.other = d
        #TODO: self.method =
        #TODO: other method details
        #TODO: self.instrument =

    def as_json(self):
        d = {}
        for prop in ['name', 'date_create', 'run_type']:
            d[prop] = getattr(self, prop)

        # add a couple things not in the dictionary or
        # improperly formatted
        d['file_type'] = self.file_type
        d['filename'] = os.path.join(os.path.basename( \
              os.path.dirname(self.filename)), os.path.basename(self.filename))
        d['date_create'] = d['date_create'].isoformat(' ')
        return d

    @property
    def children(self):
        return self.peaks + self.pkgps

    @property
    def parent(self):
        return self.project


class Project(Base):
    __tablename__ = 'projects'
    project_id = Column(Integer, primary_key=True)
    name = Column(Unicode(255))
    traces = relationship('DBTrace', backref='project')
    #TODO: parent_project

    @property
    def children(self):
        #TODO: also return child projects
        return self.chromatograms

    @property
    def parent(self):
        #TODO: could also be another project?
        return None
