#    Copyright 2011-2013 Roderick Bovee
#
#    This file is part of Aston.
#
#    Aston is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Aston is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Aston.  If not, see <http://www.gnu.org/licenses/>.

"""
This module handles database access for Aston.
"""
#pylint: disable=C0103

import os
import sqlite3
import json
import zlib
from datetime import datetime
from aston.FileFormats.FileFormats import ftype_to_class
from aston.FileFormats.FileFormats import ext_to_classtable
from aston.FileFormats.FileFormats import get_magic
from aston.TimeSeries import decompress_to_ts
from aston.Features.Spectrum import decompress_to_spec


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

    def get_key(self, key, dflt=''):
        c = self.db.cursor()
        c.execute('SELECT * FROM prefs WHERE key = ?', (key,))
        res = c.fetchone()
        c.close()

        if res is None:
            return dflt
        else:
            return res[1]

    def set_key(self, key, val):
        c = self.db.cursor()
        c.execute('SELECT * FROM prefs WHERE key = ?', (key,))
        if c.fetchone() is not None:
            c.execute('UPDATE prefs SET value=? WHERE key=?', (val, key))
        else:
            c.execute('INSERT INTO prefs (value,key) VALUES (?,?)', \
                      (val, key))
        self.db.commit()
        c.close()

    def lazy_set_key(self, c, key, val):
        c.execute('SELECT * FROM prefs WHERE key = ?', (key,))
        if c.fetchone() is not None:
            c.execute('UPDATE prefs SET value=? WHERE key=?', (val, key))
        else:
            c.execute('INSERT INTO prefs (value,key) VALUES (?,?)', \
                      (val, key))

    def updateObject(self, obj):
        c = self.db.cursor()
        c.execute('''UPDATE objs SET type=?, parent_id=?, name=?,
                  info=?, data=? WHERE id=?''', \
                  self._getRowFromObj(obj) + (obj.db_id,))
        self.db.commit()
        c.close()

    def begin_lazy_op(self):
        if self.objects is None:
            self.reload()
        c = self.db.cursor()
        return c

    def end_lazy_op(self, c):
        self.db.commit()
        c.close()

    def lazy_delete(self, c, obj):
        c.execute('DELETE FROM objs WHERE id=?', (obj.db_id,))
        del self.objects[self.objects.index(obj)]

    def lazy_add(self, c, obj):
        result = c.execute('INSERT INTO objs \
          (type, parent_id, name, info, data) \
          VALUES (?,?,?,?,?)', self._getRowFromObj(obj))
        obj.db_id = result.lastrowid
        self.objects.append(obj)

    def add_objects(self, obj):
        """
        Convenience method so lazy methods don't need to be called.
        """
        c = self.begin_lazy_op()
        for o in obj:
            result = c.execute('''INSERT INTO objs (type, parent_id, name,
                            info, data) VALUES (?,?,?,?,?)''', \
                            self._getRowFromObj(o))
            o.db_id = result.lastrowid
        self.objects += obj
        self.end_lazy_op(c)

    def deleteObject(self, obj):
        c = self.db.cursor()
        if type(obj) == list:
            #qs = '(' + ','.join(['?'] * len(obj)) + ')'
            #c.execute('DELETE FROM objs WHERE id in ' + qs,
            #          [o.db_id for o in obj])
            for o in obj:
                c.execute('DELETE FROM objs WHERE id=?', (o.db_id,))
                del self.objects[self.objects.index(o)]
            self.db.commit()
        else:
            c.execute('DELETE FROM objs WHERE id=?', (obj.db_id,))
            del self.objects[self.objects.index(obj)]
        self.db.commit()
        c.close()

    @property
    def root(self):
        return self.getChildren()

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
            info = buffer(zlib.compress(json.dumps(obj.info)))
        except NameError:
            info = zlib.compress(json.dumps(obj.info).encode('utf-8'))
        if obj.type == 'peak':
            data = obj.rawdata.compress()
        elif obj.type == 'spectrum':
            data = obj.compress()
        else:
            data = obj.rawdata
        return (obj.type, obj.parent_id, obj.info['name'], info, data)

    def _getObjFromRow(self, row):
        if row is None:
            return None

        info = json.loads(zlib.decompress(row[3]).decode('utf-8'))
        otype = str(row[0])
        if otype == 'peak':
            data = decompress_to_ts(row[4])
        elif otype == 'spectrum':
            data = decompress_to_spec(row[4])
        else:
            data = str(row[4])
        args = (row[1], row[2], info, data)
        if otype == 'file':
            return ftype_to_class(info['s-file-type'])(self, *args)
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
            from aston.Features import DBObject
            return DBObject(otype, self, *args)


class AstonFileDatabase(AstonDatabase):
    def __init__(self, *args, **kwargs):
        super(AstonFileDatabase, self).__init__(*args, **kwargs)
        if self.get_key('db_reload_on_open', dflt='True') == 'True':
            self.update_file_list(self.database_path)

    def update_file_list(self, path):
        """
        Makes sure the database is in sync with the file system.
        """
        ext2ftype = ext_to_classtable()

        #TODO: this needs to run in a separate thread
        #extract a list of lists of file names in my directory
        foldname = os.path.dirname(path)
        if foldname == '':
            foldname = os.curdir
        datafiles = {}
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
                    datafiles[os.path.join(fold, filename)] = ftype
            for d in dirs:
                if d.startswith('.') or d.startswith('_'):
                    dirs.remove(d)

        #extract a list of files from the database
        c = self.db.cursor()
        c.execute('SELECT data FROM objs WHERE type="file"')
        dnames = set([i[0] for i in c])

        #compare the two lists -> remove deleted files from the database
        if self.get_key('db_remove_deleted', dflt='False') == 'True':
            for fn in dnames.difference(set(datafiles.keys())):
                c.execute('DELETE FROM files WHERE file_name=?', (fn,))
            self.db.commit()
        c.close()

        #add the new files into the database
        #TODO: generate projects and project_ids based on folder names?
        c = self.begin_lazy_op()
        for fn in set(datafiles.keys()).difference(dnames):
            fdate = datetime.fromtimestamp(os.path.getctime(fn))
            fdate = fdate.replace(microsecond=0).isoformat(' ')
            info = {'s-file-type': datafiles[fn], 'traces': 'TIC', \
              'name': os.path.splitext(os.path.basename(fn))[0], \
              'r-date': fdate}
            args = (None, None, info, fn)
            obj = ftype_to_class(info['s-file-type'])(self, *args)
            obj._update_info_from_file()
            self.lazy_add(c, obj)
        self.end_lazy_op(c)

        #TODO: update old database entries with new metadata


class AstonMethodDB(AstonDatabase):
    def _getDefaultKey(self, key):
        if key == 'main_cols':
            return json.dumps(['name'])
        return ''
