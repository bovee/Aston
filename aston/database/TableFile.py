import os
import os.path as op
from slqalchemy import Column, Integer, UnicodeText, Unicode, ForeignKey
#from sqlalchemy.orm import relationship
from aston.tracefile.Common import file_type, tfclasses
from aston.database import Base, JSONDict


class Project(Base):
    __tablename__ = 'projects'
    project_id = Column(Integer, primary_key=True)
    group_id = Column(Integer)
    name = Column(Unicode(255))


class Run(Base):
    __tablename__ = 'runs'
    run_id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.project_id'))
    group_id = Column(Integer)
    name = Column(Unicode(255))
    #method_id = Column(Integer)
    other = Column(JSONDict)


class Analysis(Base):
    __tablename__ = 'analyses'
    analysis_id = Column(Integer, primary_key=True)
    filename = Column(UnicodeText)
    file_type = Column(Unicode(32))
    trace = Column(Unicode(32))


def read_directory(path):
    ftype_to_cls = {tf.__name__: tf for tf in tfclasses()}

    for fold, dirs, files in os.walk(path):
        # determine names of group and run for files in this directory
        curpath = op.relpath(fold, path).split(op.sep)
        runname = [i for i in curpath if i.lower().endswith('.d')][-1]
        runpath = op.sep.join(curpath[:curpath.index(runname)])
        if curpath[0] == op.curdir or curpath[0] == runname:
            projname = ''
        else:
            projname = curpath[0]

        for filename in files:
            # deal with CH files for each wavelength; merge
            if filename.upper().endswith('.CH'):
                ufn = filename.upper()
                if (ufn.startswith('MWD') and ufn != 'MWD1A.CH') or \
                   (ufn.startswith('DAD') and ufn != 'DAD1A.CH'):
                    continue
            ftype = file_type(op.join(fold, filename))
            if ftype is None:
                continue

            tf = ftype_to_cls[ftype](op.join(fold, filename))
            tf.info['filename'] = op.relpath(op.join(fold, filename), path)
            #print(tf.info)
            #print(tf.traces)
        for d in dirs:
            if d.startswith('.') or d.startswith('_'):
                dirs.remove(d)
