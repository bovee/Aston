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

        if database is None:
            self.db = None
        elif not os.path.exists(database):
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
        self._children = None
        self._curs = None

    def __enter__(self):
        self._curs = self.db.cursor()

    def __exit__(self, type, value, traceback):
        self.db.commit()
        self._curs.close()
        self._curs = None

    def get_children(self, obj):
        if self.db is None:
            return []
        if self._curs is None:
            c = self.db.cursor()
        else:
            c = self._curs

        if obj is None:
            c.execute('SELECT type, id, info, data FROM objs ' + \
                      'WHERE parent_id IS NULL')
        else:
            c.execute('SELECT type, id, info, data FROM objs ' + \
                      'WHERE parent_id = ?', (obj.db_id,))
        children = []
        for row in c:
            row_obj = self._get_obj_from_row(row, obj)
            children.append(row_obj)
        if self._curs is None:
            c.close()
        return children

    @property
    def children(self):
        if self._children is None:
            self._children = self.get_children(None)
        return self._children

    def all_keys(self):
        c = self.db.cursor()
        c.execute('SELECT key, value FROM prefs')
        p = c.fetchall()
        c.close()
        return dict(p)

    def get_key(self, key, dflt=''):
        if self.db is None:
            return dflt
        if self._curs is None:
            c = self.db.cursor()
        else:
            c = self._curs
        c.execute('SELECT value FROM prefs WHERE key = ?', (key,))
        res = c.fetchone()
        if self._curs is None:
            c.close()
        if res is None:
            return dflt
        else:
            return res[0]

    def set_key(self, key, val):
        if self.db is None:
            return
        if self._curs is None:
            c = self.db.cursor()
        else:
            c = self._curs

        c.execute('SELECT * FROM prefs WHERE key = ?', (key,))
        if c.fetchone() is not None:
            c.execute('UPDATE prefs SET value=? WHERE key=?', (val, key))
        else:
            c.execute('INSERT INTO prefs (value,key) VALUES (?,?)', \
                      (val, key))

        if self._curs is None:
            self.db.commit()
            c.close()

    def save_object(self, obj):
        if self._curs is None:
            c = self.db.cursor()
        else:
            c = self._curs

        if obj.db_id is not None:
            # update
            c.execute('UPDATE objs SET type=?, parent_id=?, name=?, ' + \
                      'info=?, data=? WHERE id=?', \
                      self._get_row_from_obj(obj) + (obj.db_id,))
        else:
            # add
            res = c.execute('INSERT INTO objs (type, parent_id, name, ' + \
                            'info, data) VALUES (?,?,?,?,?)', \
                            self._get_row_from_obj(obj))
            obj.db_id = res.lastrowid

        if self._curs is None:
            self.db.commit()
            c.close()

    def delete_object(self, obj):
        if self._curs is None:
            c = self.db.cursor()
        else:
            c = self._curs

        c.execute('DELETE FROM objs WHERE id=?', (obj.db_id,))
        if obj in self._children:
            self._children.remove(obj)

        if self._curs is None:
            self.db.commit()
            c.close()

    #def getObjectsByClass(self, cls):
    #    if self.objects is None:
    #        self.reload()
    #    return [obj for obj in self.objects if obj.db_type == cls]

    def object_from_id(self, db_id, parent=None):
        if parent is None:
            parent = self
        for obj in parent.children:
            if obj.db_id == db_id:
                return obj
            subobj_id = self.object_from_id(db_id, obj)
            if subobj_id is not None:
                return subobj_id
        return None

    def _get_row_from_obj(self, obj):
        try:  # python 2/3 code options
            info = buffer(zlib.compress(json.dumps(obj.info)))
        except NameError:
            info = zlib.compress(json.dumps(obj.info).encode('utf-8'))
        if obj.db_type == 'peak':
            data = obj.rawdata.compress()
        elif obj.db_type == 'spectrum':
            data = obj.compress()
        else:
            data = obj.rawdata
        if obj.parent is None:
            pid = None
        else:
            pid = obj.parent.db_id
        return (obj.db_type, pid, obj.info['name'], info, data)

    def _get_obj_from_row(self, row, parent):
        # row = (type, id, info, data)
        if row is None:
            return None

        args = {}
        args['info'] = json.loads(zlib.decompress(row[2]).decode('utf-8'))
        otype = str(row[0])
        if otype == 'peak':
            args['data'] = decompress_to_ts(row[3])
        elif otype == 'spectrum':
            args['data'] = decompress_to_spec(row[3])
        else:
            args['data'] = str(row[3])
        args['parent'] = parent
        args['db'] = (self, row[1])
        if otype == 'file':
            return ftype_to_class(args['info']['s-file-type'])(**args)
        elif otype == 'peak':
            from aston.Features import Peak
            return Peak(**args)
        elif otype == 'spectrum':
            from aston.Features import Spectrum
            return Spectrum(**args)
        elif otype == 'method':
            from aston.Features import Method
            return Method(**args)
        elif otype == 'compound':
            from aston.Features import Compound
            return Compound(**args)
        else:
            from aston.Features import DBObject
            return DBObject(**args)


class AstonFileDatabase(AstonDatabase):
    def __init__(self, *args, **kwargs):
        super(AstonFileDatabase, self).__init__(*args, **kwargs)
        if self.get_key('db_reload_on_open', dflt='T') == 'T':
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
        if self.get_key('db_remove_deleted', dflt='False') == 'T':
            for fn in dnames.difference(set(datafiles.keys())):
                c.execute('DELETE FROM files WHERE file_name=?', (fn,))
            self.db.commit()
        c.close()

        #add the new files into the database
        #TODO: generate projects and project_ids based on folder names?
        with self:
            for fn in set(datafiles.keys()).difference(dnames):
                fdate = datetime.fromtimestamp(os.path.getctime(fn))
                fdate = fdate.replace(microsecond=0).isoformat(' ')
                name = os.path.splitext(os.path.basename(fn))[0]
                info = {'s-file-type': datafiles[fn], 'traces': 'TIC', \
                        'name': name, 'r-date': fdate}
                obj = ftype_to_class(info['s-file-type'])(info, fn)
                obj._update_info_from_file()
                self.save_object(obj)

        #TODO: update old database entries with new metadata


class AstonMethodDB(AstonDatabase):
    def _getDefaultKey(self, key):
        if key == 'main_cols':
            return json.dumps(['name'])
        return ''
