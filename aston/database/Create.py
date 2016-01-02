import os
import os.path as op
from collections import Counter
from aston.tracefile.Common import file_type, tfclasses
from aston.database.File import Project, Run, Analysis
from aston.database.Palette import Palette
from aston.database.User import User, Group


def read_directory(path, db, group=None):
    # TODO: update with group also for permissions support
    ftype_to_cls = {tf.__name__: tf for tf in tfclasses()}

    # create blank project
    if db.execute('SELECT 1 FROM projects WHERE name = ""').scalar() is None:
        p = Project(name='', directory=op.abspath(path))
        if group is not None:
            p.group = group
        db.add(p)

    for fold, dirs, files in os.walk(path):
        # for some reason, the scanning code at the end of this loop
        # doesn't always work?
        if '/_' in fold or '/.' in fold:
            continue

        curpath = op.relpath(fold, path).split(op.sep)

        # extract a run name
        try:
            runname = [i for i in curpath if
                       i.endswith(('.d', '.D', '.raw', '.RAW'))][-1]
        except IndexError:
            runname = ''

        # extract a project name
        if curpath[0] == op.curdir or curpath[0] == runname:
            projname = ''
            projpath = op.abspath(path)
        else:
            projname = curpath[0]
            projpath = op.abspath(op.join(path, projname))

        for filename in files:
            # deal with CH files for each wavelength; merge
            if filename.upper().endswith('.CH'):
                ufn = filename.upper()
                if (ufn.startswith('MWD') and ufn != 'MWD1A.CH') or \
                   (ufn.startswith('DAD') and ufn != 'DAD1A.CH'):
                    continue

            # figure out if this is a chromatography file
            ftype = file_type(op.join(fold, filename))
            if ftype is None:
                continue

            tf = ftype_to_cls[ftype](op.join(fold, filename))
            tf.info['filename'] = op.relpath(op.join(fold, filename), path)
            add_analysis(db, projname, projpath, runname, tf, group)

    db.commit()
    db.flush()
    # TODO: maybe give names to runs without them here?


def add_analysis(db, projname, projpath, runname, tf, group=None):
    # find the project; if it doesn't exist, create it
    project = db.query(Project).filter_by(name=projname).first()
    if project is None:
        project = Project(name=projname, directory=projpath)
        if group is not None:
            project.group = group
        db.add(project)

    # find the run; if it doesn't exist, create it
    if runname == '':
        runpath = tf.info['filename']
    else:
        path = tf.info['filename'].split(op.sep)
        runpath = op.sep.join(path[:path.index(runname) + 1])
    runpath = op.relpath(op.abspath(runpath), projpath)
    run = db.query(Run).filter_by(path=runpath).first()
    if run is None:
        run = Run(name=runname, path=runpath, project=project)
        db.add(run)

    # TODO: filter by md5hash also to weed out uniques
    # TODO: also use md5hash to update filenames of moved files
    analpath = op.relpath(op.abspath(tf.info['filename']), projpath)
    analysis = db.query(Analysis).filter_by(path=analpath).first()
    if analysis is None:
        # add this analysis into the database
        info = tf.info.copy()
        analysis = Analysis(path=analpath, filetype=info['filetype'],
                            run=run)
        if run.name == '':
            run.name = op.split(info['filename'])[1]
        del info['filename'], info['filetype']

        # add in list of traces
        other_traces = ','.join(a.trace for a in run.analyses
                                if a.trace is not None)
        other_traces = Counter(i.rstrip('0123456789') for
                               i in other_traces.split(','))
        analysis.trace = ','.join(i if i not in other_traces
                                  else i + str(other_traces[i] + 1)
                                  for i in tf.traces)

        # TODO: add trace info in
        db.add(analysis)

        # update info in the containing run
        if 'name' in info:
            run.name = info['name']
            del info['name']
        if run.info is not None:
            run.info.update(info)
        else:
            run.info = info


def simple_auth(db):
    s = 'SELECT 1 FROM groups WHERE groupname = ""'
    if db.execute(s).scalar() is None:
        def_group = Group(groupname='')
        db.add(def_group)
        db.add(User(username='', groups=[def_group], prefs={}))
        db.add(Palette(name='', group=def_group))
        db.commit()
    else:
        def_group = db.query(Group).filter_by(groupname='').first()
    return def_group
