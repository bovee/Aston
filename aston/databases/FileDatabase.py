import os
from datetime import datetime
from PyQt4 import QtCore
from aston.databases.Database import AstonDatabase
from aston.file_adapters.FileFormats import ftype_to_class
from aston.file_adapters.FileFormats import ext_to_classtable
from aston.file_adapters.FileFormats import get_magic


class AstonFileDatabase(AstonDatabase):
    def __init__(self, *args, **kwargs):
        super(AstonFileDatabase, self).__init__(*args, **kwargs)
        #TODO: only conditionally run this (if MULTIPROCESSING)
        #mp = self.get_key('multiprocessing', dflt=True)
        #if self.get_key('db_reload_on_open', dflt=True):  # and not mp:
        #    self.update_file_list()

    def update_file_list(self):
        #extract a list of files from the database
        c = self._db.cursor()
        c.execute('SELECT id, data FROM objs WHERE type="file"')
        n_to_id = {i[1]: i[0] for i in c}

        remove = self.get_key('db_remove_deleted', dflt=False)
        for dbid, obj in self.files_to_update(self.database_path, n_to_id, \
                                              remove):
            if obj is None:
                c.execute('DELETE FROM files WHERE id=?', (dbid,))
            else:
                obj.parent = self
        self._db.commit()
        c.close()

    def files_to_update(self, path, name_to_dbid, remove=False):
        """
        Makes sure the database is in sync with the file system.
        """

        ext2ftype = ext_to_classtable()
        dnames = set(name_to_dbid.keys())

        #TODO: this needs to run in a separate thread
        #extract a list of lists of file names in my directory
        foldname = os.path.dirname(path)
        if foldname == '':
            foldname = os.curdir
        datafiles = []
        for fold, dirs, files in os.walk(foldname):
            for filename in files:
                ext, magic = get_magic(os.path.join(fold, filename))

                #TODO: this MWD stuff is kludgy and will probably break
                if ext == 'CH':
                    if filename[:3].upper() == 'MWD':
                        filename = 'mwd1A.ch'
                    elif filename[:3].upper() == 'DAD':
                        filename = 'dad1A.ch'

                ftype = None
                if magic is not None:
                    ftype = ext2ftype.get(ext + '.' + magic, None)
                if ftype is None:
                    ftype = ext2ftype.get(ext, None)

                #if it's a supported file, add it in
                if ftype is not None:
                    fn = os.path.join(fold, filename)
                    datafiles.append(fn)
                    if fn in dnames:
                        #TODO: update old database entries with new metadata
                        # if the metadata has changed
                        #yield (name_to_dbid[fn], new_obj)
                        pass
                    else:
                        # update dnames, so we won't find *.CH multiple times
                        if filename in ['mwd1A.ch', 'dad1A.ch']:
                            dnames.update([fn])
                        #TODO: generate projects and project_ids based on
                        # folder names?
                        fdate = datetime.fromtimestamp(os.path.getctime(fn))
                        fdate = fdate.replace(microsecond=0).isoformat(' ')
                        name = os.path.splitext(os.path.basename(fn))[0]
                        info = {'s-file-type': ftype, 'traces': \
                                'TIC', 'name': name, 'r-date': fdate}
                        obj = ftype_to_class(info['s-file-type'])(info, fn)
                        obj._update_info_from_file()
                        yield (None, obj)
                        #obj.db, obj._parent = self, self
                        #obj.parent = self
                        #self.save_object(obj)
            for d in dirs:
                if d.startswith('.') or d.startswith('_'):
                    dirs.remove(d)

        #compare the two lists -> remove deleted files from the database
        if remove:
            for fn in dnames.difference(set(datafiles)):
                yield (name_to_dbid[fn], None)


class LoadFilesThread(QtCore.QThread):
    file_updated = QtCore.pyqtSignal(object, object)

    def __init__(self, file_db):
        super(LoadFilesThread, self).__init__()
        self.file_db = file_db
        c = file_db._db.cursor()
        c.execute('SELECT id, data FROM objs WHERE type="file"')
        self.name_to_dbid = {i[1]: i[0] for i in c}
        c.close()
        self.remove = file_db.get_key('db_remove_deleted', dflt=False)

    def run(self):
        db_path = self.file_db.database_path
        changed_files = self.file_db.files_to_update(db_path, \
                                        self.name_to_dbid, self.remove)
        for dbid, file_obj in changed_files:
            self.file_updated.emit(dbid, file_obj)
        self.file_updated.emit(None, None)
