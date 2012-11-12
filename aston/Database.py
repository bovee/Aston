"""
This module handles database access for Aston.
"""
#pylint: disable=C0103

import os
import struct
import sqlite3
import json
import zlib


class AstonDatabase(object):
    """
    This class acts as a interface to the aston.sqlite database
    that's created inside every working folder.
    """
    def __init__(self, database):
        self.database_path = database

        if not os.path.exists(database):
            # create a database file if one doesn't exist
            self.db = sqlite3.connect(database)
            c = self.db.cursor()
            c.execute('''CREATE TABLE prefs (key TEXT, value TEXT)''')
            c.execute('''CREATE TABLE objs (type TEXT,
                      id INTEGER PRIMARY KEY ASC, parent_id INTEGER,
                      name TEXT, info BLOB, data BLOB)''')
            self.db.commit()
            c.close()
        else:
            self.db = sqlite3.connect(database)
        self.objects = None

    def reload(self):
        #preload all the objects in the database
        c = self.db.cursor()
        c.execute('SELECT type, id, parent_id, info, data FROM objs')
        self.objects = []
        for i in c:
            self.objects.append(self._getObjFromRow(i))
        c.close()

    def getKey(self, key):
        c = self.db.cursor()
        c.execute('SELECT * FROM prefs WHERE key = ?', (key,))
        res = c.fetchone()
        c.close()

        if res is None:
            return self._getDefaultKey(key)
        else:
            return res[1]

    def setKey(self, key, val):
        c = self.db.cursor()
        c.execute('SELECT * FROM prefs WHERE key = ?', (key,))
        if c.fetchone() is not None:
            c.execute('UPDATE prefs SET value=? WHERE key=?', (val, key))
        else:
            c.execute('INSERT INTO prefs (value,key) VALUES (?,?)', \
                      (val, key))
        self.db.commit()
        c.close()

    def updateObject(self, obj):
        c = self.db.cursor()
        c.execute('''UPDATE objs SET type=?, parent_id=?, name=?,
                  info=?, data=? WHERE id=?''', \
                  self._getRowFromObj(obj) + (obj.db_id,))
        self.db.commit()
        c.close()

    def addObject(self, obj):
        if self.objects is None:
            self.reload()
        c = self.db.cursor()
        result = c.execute('''INSERT INTO objs (type, parent_id, name,
                           info, data) VALUES (?,?,?,?,?)''', \
                           self._getRowFromObj(obj))
        obj.db_id = result.lastrowid
        self.db.commit()
        c.close()
        self.objects.append(obj)

    def deleteObject(self, obj):
        c = self.db.cursor()
        c.execute('DELETE FROM objs WHERE id=?', (obj.db_id,))
        self.db.commit()
        c.close()
        del self.objects[self.objects.index(obj)]

    def getChildren(self, db_id=None):
        if self.objects is None:
            self.reload()
        return [obj for obj in self.objects if obj.parent_id == db_id]

    def getObjectsByClass(self, cls):
        if self.objects is None:
            self.reload()
        return [obj for obj in self.objects if obj.db_type == cls]

    def getObjectByID(self, db_id):
        if self.objects is None:
            self.reload()

        for obj in self.objects:
            if obj.db_id == db_id:
                return obj
        return None

    def getObjectByName(self, name, type=None):
        pass

    def _getRowFromObj(self, obj):
        try:  # python 2/3 code options
            pack = lambda r: buffer(zlib.compress(json.dumps(r)))
            pack([])  # have to force the call here
        except NameError:
            pack = lambda r: zlib.compress(json.dumps(r).encode('utf-8'))
        info = pack(obj.info)
        if obj.type in ['peak', 'spectrum']:
            data = pack(obj.rawdata)
        else:
            data = obj.rawdata
        return (obj.type, obj.parent_id, obj.get_info('name'), info, data)

    def _getObjFromRow(self, row):
        if row is None:
            return None

        def unpack(r):
            try:  # TODO: this try is for testing; remove
                return json.loads(zlib.decompress(r).decode('utf-8'))
            except:
                return None
        #unpack = lambda r: \
        #  json.loads(zlib.decompress(r).decode('utf-8'))
        info = unpack(row[3])
        otype = str(row[0])
        if otype in ['peak', 'spectrum']:
            data = unpack(row[4])
        else:
            data = str(row[4])
        args = (row[1], row[2], info, data)
        if otype == 'file':
            from aston.Datafile import Datafile
            return Datafile(self, *args)
        elif otype == 'peak':
            from aston.Features import Peak
            return Peak(self, *args)
        elif otype == 'spectrum':
            from aston.Features import Spectrum
            return Spectrum(self, *args)
        elif otype == 'method':
            from aston.Features import Method
            return Method(self, *args)
        elif otype == 'compound':
            from aston.Features import Compound
            return Compound(self, *args)
        else:
            return DBObject(otype, self, *args)

    def _getDefaultKey(self, key):
        if key == 'main_cols':
            return json.dumps(['name'])
        return ''


class AstonFileDatabase(AstonDatabase):
    def __init__(self, *args, **kwargs):
        super(AstonFileDatabase, self).__init__(*args, **kwargs)
        self.updateFileList(self.database_path)

    def updateFileList(self, path):
        """
        Makes sure the database is in sync with the file system.
        """
        from aston.FileFormats.FileFormats import guess_filetype
        from aston.Datafile import Datafile

        #TODO: this needs to run in a separate thread
        #extract a list of lists of file names in my directory
        foldname = os.path.dirname(path)
        if foldname == '':
            foldname = os.curdir
        datafiles = {}
        for fold, _, files in os.walk(foldname):
            for filename in files:
                #TODO: this MWD stuff is kludgy and will probably break
                if filename[:3].upper() == 'MWD' and \
                    filename[-3:].upper() == '.CH': filename = 'mwd1A.ch'
                if filename[:3].upper() == 'DAD' and \
                    filename[-3:].upper() == '.CH': filename = 'dad1A.ch'
                #guess the file type
                ext = os.path.splitext(filename)[1].upper()[1:]
                try:
                    f = open(os.path.join(fold, filename), mode='rb')
                    magic = struct.unpack('>H', f.read(2))[0]
                    f.close()
                except struct.error:
                    magic = 0
                except IOError:
                    ext = ''

                ftype = guess_filetype(ext, magic)

                #if it's a supported file, add it in
                if ftype is not None:
                    datafiles[os.path.join(fold, filename)] = ftype

        #extract a list of files from the database
        c = self.db.cursor()
        c.execute('SELECT data FROM objs WHERE type="file"')
        dnames = set([i[0] for i in c])
        c.close()

        #compare the two lists -> remove deleted files from the database
        #TODO: this should only flag files as being bad, not delete them
        #from the database.
        #for fn in dnames.difference(set(fnames)):
        #    c.execute('DELETE FROM files WHERE file_name=?',(fn,))
        #    self.db.commit()

        #add the new files into the database
        #TODO: generate projects and project_ids based on folder names?
        for fn in set(datafiles.keys()).difference(dnames):
            info = {'s-file-type': datafiles[fn], 'traces': 'TIC', \
              'name': os.path.splitext(os.path.basename(fn))[0]}
            obj = Datafile(self, None, None, info, fn)
            obj._update_info_from_file()
            self.addObject(obj)

        #TODO: update old database entries with new metadata

    def _getDefaultKey(self, key):
        if key == 'main_cols':
            return json.dumps(['name', 'vis', 'traces', 'r-filename'])
        return ''


class DBObject(object):
    """
    Master class for peaks, features, and datafiles.
    """
    def __init__(self, db_type='none', db=None, db_id=None, \
      parent_id=None, info=None, data=None):
        self.db_type = db_type
        self.db = db
        self.db_id = db_id
        self.parent_id = parent_id
        self.type = db_type
        if info is None:
            self.info = {'name': ''}
        else:
            self.info = info
        self.rawdata = data

    def get_info(self, fld):
        if fld not in self.info.keys():
            self._load_info(fld)

        if fld in self.info.keys():
            if self.info[fld] != '':
                return self.info[fld]
        return self._calc_info(fld)

    def set_info(self, fld, key):
        self.info[fld] = key

    def del_info(self, fld):
        for key in self.info.keys():
            if fld in key:
                del self.info[key]
        self.saveChanges()

    @property
    def parent(self):
        return self.db.getObjectByID(self.parent_id)

    @property
    def children(self):
        return self.db.getChildren(self.db_id)

    def getParentOfType(self, cls=None):
        prt = self.parent
        if cls is None:
            return prt
        while True:
            if prt is None:
                return None
            elif prt.db_type == cls:
                return prt
            prt = prt.parent

    def getAllChildren(self, cls=None):
        if len(self.children) == 0:
            return []
        child_list = []
        for child in self.children:
            if child.db_type == cls:
                child_list += [child]
            child_list += child.getAllChildren(cls)
        return child_list

    def saveChanges(self):
        """
        Save any changes in this object back to the database.
        """
        if self.db is None:
            return

        if self.db_id is not None:
            #update object
            self.db.updateObject(self)
        else:
            #create object
            self.db.addObject(self)

    #override in subclasses
    def _load_info(self, fld):
        pass

    def _calc_info(self, fld):
        return ''
