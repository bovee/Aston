import os
import os.path as op
from aston.tracefile.Common import file_type, tfclasses
from aston.database.File import Project, Run, Analysis


def read_directory(path, db):
    #TODO: update with group also for permissions support
    ftype_to_cls = {tf.__name__: tf for tf in tfclasses()}

    # create blank project
    if db.execute('SELECT 1 FROM projects WHERE name = ""').scalar() is None:
        db.add(Project(name='', directory=op.abspath(path)))

    for fold, dirs, files in os.walk(path):
        curpath = op.relpath(fold, path).split(op.sep)

        # extract a run name
        try:
            runname = [i for i in curpath if i.endswith(('.d', '.D'))][-1]
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
            add_analysis(db, projname, projpath, runname, tf)

        # make sure we're not scanning folders starting with . or _
        for d in dirs:
            if d.startswith(('.', '_')):
                dirs.remove(d)
    db.commit()
    db.flush()
    #TODO: maybe give names to runs without them here?


def add_analysis(db, projname, projpath, runname, tf):
    # find the project; if it doesn't exist, create it
    project = db.query(Project).filter_by(name=projname).first()
    #print(db.query(Project._project_id).filter_by(name=projname).all())
    if project is None:
        project = Project(name=projname, directory=projpath)
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

    #TODO: filter by md5hash also to weed out uniques
    #TODO: also use md5hash to update filenames of moved files
    analpath = op.relpath(op.abspath(tf.info['filename']), projpath)
    analysis = db.query(Analysis).filter_by(path=analpath).first()
    if analysis is None:
        # add this analysis into the database
        info = tf.info.copy()
        analysis = Analysis(path=analpath, filetype=info['filetype'],
                            run=run)
        del info['filename'], info['filetype']
        analysis.trace = ','.join(tf.traces)
        #TODO: add trace info in
        db.add(analysis)

        # update info in the containing run
        if 'name' in info:
            run.name = info['name']
            del info['name']
        if run.other is not None:
            run.other.update(info)
        else:
            run.other = info


def setup_db(db):
    from aston.database.Palette import Palette
    db.add(Palette(name='Default', columns='["name"]'))
    db.commit()
    db.flush()
