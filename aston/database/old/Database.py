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
from aston.timeseries.TimeSeries import decompress_to_ts
from aston.spectra.Spectrum import decompress_to_spec
from aston.file_adapters.FileFormats import ftype_to_class


class AstonDatabase(object):
    """
    This class acts as a interface to the aston.sqlite database
    that's created inside every working folder.
    """
    def __init__(self, database):
        self.database_path = database

        self.db = self
        if database is None:
            self._db = None
        elif not os.path.exists(database):
            # create a database file if one doesn't exist
            self._db = sqlite3.connect(database)
            c = self._db.cursor()
            c.execute('''CREATE TABLE prefs (key TEXT, value TEXT)''')
            c.execute('''CREATE TABLE objs (type TEXT,
                      id INTEGER PRIMARY KEY ASC, parent_id INTEGER,
                      name TEXT, info BLOB, data BLOB)''')
            self._db.commit()
            c.close()
        else:
            self._db = sqlite3.connect(database)
        self.dbtype = None
        self._children = None
        self._curs = None
        self._enter_depth = 0

        self._table = None

    def __enter__(self):
        self._enter_depth += 1
        if self._curs is None:
            self._curs = self._db.cursor()

    def __exit__(self, type, value, traceback):
        self._enter_depth -= 1
        if self._enter_depth == 0:
            self._db.commit()
            self._curs.close()
            self._curs = None

    def _get_curs(self):
        if self._curs is not None:
            return self._curs
        else:
            return self._db.cursor()

    def _close_curs(self, c, write=False):
        if self._curs is None:
            if write:
                self._db.commit()
            c.close()

    def get_children(self, obj):
        if self._db is None:
            return []
        c = self._get_curs()
        if obj is self:
            c.execute('SELECT type, id, info, data FROM objs ' + \
                      'WHERE parent_id IS NULL')
        else:
            c.execute('SELECT type, id, info, data FROM objs ' + \
                      'WHERE parent_id = ?', (obj.db_id,))
        children = []
        for row in c:
            row_obj = self._get_obj_from_row(row, obj)
            children.append(row_obj)
        self._close_curs(c)
        return children

    @property
    def children(self):
        if self._children is None:
            self._children = self.get_children(self)
        return self._children

    def children_of_type(self, cls=None):
        if self._children is None:
            self._children = self.get_children(self)
        child_list = []
        for child in self._children:
            if child.db_type == cls or cls is None:
                child_list.append(child)
            child_list += child.children_of_type(cls=cls)
        return child_list

    def start_child_mod(self, parent, add_c=None, del_c=None):
        if parent is None or self._table is None:
            return
        pidx = self._table._obj_to_index(parent)
        if add_c is not None:
            if len(add_c) > 0:
                row = len(parent._children)
                self._table.beginInsertRows(pidx, row, row + len(add_c) - 1)
        if del_c is not None:
            for obj in del_c:
                row = parent._children.index(obj)
                self._table.beginRemoveRows(pidx, row, row)

    def end_child_mod(self, parent, add_c=None, del_c=None):
        if parent is None or self._table is None:
            return
        if add_c is not None:
            if len(add_c) > 0:
                self._table.endInsertRows()
        if del_c is not None:
            for _ in del_c:
                self._table.endRemoveRows()

    def all_keys(self):
        c = self._db.cursor()
        c.execute('SELECT key, value FROM prefs')
        p = c.fetchall()
        c.close()
        return dict(p)

    def get_key(self, key, dflt=''):
        if self._db is None:
            return dflt
        c = self._get_curs()
        c.execute('SELECT value FROM prefs WHERE key = ?', (key,))
        res = c.fetchone()
        if self._curs is None:
            c.close()
        if res is None:
            return dflt
        else:
            if type(dflt) == bool:
                # automatically make this a boolean
                return res[0] == 'T'
            else:
                return res[0]

    def set_key(self, key, val):
        if self._db is None:
            return
        c = self._get_curs()
        c.execute('SELECT * FROM prefs WHERE key = ?', (key,))
        if c.fetchone() is not None:
            c.execute('UPDATE prefs SET value=? WHERE key=?', (val, key))
        else:
            c.execute('INSERT INTO prefs (value,key) VALUES (?,?)', \
                      (val, key))
        self._close_curs(c, write=True)

    def save_object(self, obj):
        c = self._get_curs()
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
        self._close_curs(c, write=True)

    def delete_object(self, obj):
        c = self._get_curs()
        c.execute('DELETE FROM objs WHERE id=?', (obj.db_id,))
        self._close_curs(c, write=True)

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
        if obj.parent is self:
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
            from aston.peaks.Peak import Peak
            return Peak(**args)
        elif otype == 'spectrum':
            from aston.spectra.Spectrum import Spectrum
            return Spectrum(**args)
        elif otype == 'method':
            from aston.features.Other import Method
            return Method(**args)
        elif otype == 'compound':
            from aston.features.Other import Compound
            return Compound(**args)
        else:
            from aston.features.DBObject import DBObject
            return DBObject(**args)


class AstonMethodDB(AstonDatabase):
    def _getDefaultKey(self, key):
        if key == 'main_cols':
            return json.dumps(['name'])
        return ''
