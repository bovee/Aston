'''This module handles database access for Aston.'''
#pylint: disable=C0103

import os
import sqlite3
import json
import zlib

class AstonDatabase(object):
    """This class acts as a interface to the aston.sqlite database
    that's created inside every working folder."""
    def __init__(self, database):
        self.database_path = database
        print database
        
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
    
    def updateFileList(self, path):
        from aston.Datafile import Datafile
        import os
        import struct
        '''Makes sure the database is in sync with the file system.'''
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
                ext = os.path.splitext(filename)[1].upper()
                try:
                    f = open(os.path.join(fold, filename), mode='rb')
                    magic = struct.unpack('>H', f.read(2))[0]
                    f.close()
                except struct.error:
                    magic = 0
                except IOError:
                    ext = ''

                #TODO:.BAF : Bruker instrument data format
                #TODO:.FID : Bruker instrument data format
                #TODO:.PKL : MassLynx associated format
                #TODO:.RAW : Micromass MassLynx directory format
                #TODO:.WIFF: ABI/Sciex (QSTAR and QTRAP instrument) format
                #TODO:.YEP : Bruker instrument data format
                #TODO:.RAW : PerkinElmer TurboMass file format
                if ext == '.MS' and magic == 0x0132:
                    ftype = 'AgilentMS'
                elif ext == '.BIN' and magic == 513:
                    ftype = 'AgilentMSMSProf'
                elif ext == '.BIN' and magic == 257:
                    ftype = 'AgilentMSMSScan'
                elif ext == '.CF' and magic == 0xFFFF:
                    ftype = 'ThermoCF'
                elif ext == '.DXF' and magic == 0xFFFF:
                    ftype = 'ThermoDXF'
                elif ext == '.SD':
                    ftype = 'AgilentDAD'
                elif ext == '.CH' and magic == 0x0233:
                    ftype = 'AgilentMWD'
                elif ext == '.UV' and magic == 0x0233:
                    ftype = 'AgilentCSDAD'
                elif ext == '.CSV':
                    ftype = 'CSVFile'
                else:
                    ftype = None
                
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
            info = {'s-file-type':datafiles[fn], 'traces':'TIC'}
            obj = Datafile(self, None, None, info, fn)
            obj._updateInfoFromFile()
            self.addObject(obj)
        
        #TODO: update old database entries with new metadata

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
            return ''
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
        c.execute('DELETE FROM objs WHERE id=?',(obj.db_id,))
        self.db.commit()
        c.close()
        del self.objects[self.objects.index(obj)]
    
    def getChildren(self, db_id=None):
        if self.objects is None:
            self.reload()
        return [obj for obj in self.objects if obj.parent_id == db_id]
        ## for some reason the following code crashes
        #c = self.db.cursor()
        #if db_id is None:
        #    c.execute('''SELECT type, id, parent_id, info, data
        #                 FROM objs WHERE parent_id IS NULL''')
        #else:
        #    c.execute('''SELECT type, id, parent_id, info, data
        #                 FROM objs WHERE parent_id IS ?''',(db_id,))
        #objs = []
        #for i in c:
        #    objs.append(self._getObjFromRow(i))
        #c.close()
        #return objs

    def getObjectsByClass(self, cls):
        if self.objects is None:
            self.reload()
        return [obj for obj in self.objects if obj.db_type == cls]
    
    def getObjectByID(self, db_id):
        if self.objects is None:
            self.reload()
            
        objs = []
        for obj in self.objects:
            if obj.db_id == db_id:
                return obj
        return None
        ## for some reason the following code crashes
        #if db_id is None:
        #    return None
        #c = self.db.cursor()
        #c.execute('''SELECT type, id, parent_id, info, data
        #             FROM objs WHERE id IS ?''',(db_id,))
        #res = c.fetchone()
        #if res is None:
        #    obj = None
        #else:
        #    obj = self._getObjFromRow(res)
        #c.close()
        #return obj
    
    def getObjectByName(self, name, type=None):
        pass
    
    def _getRowFromObj(self, obj):
        info = buffer(zlib.compress(json.dumps(obj.info)))
        if obj.type in ['peak','spectrum']:
            data = buffer(zlib.compress(json.dumps(obj.rawdata)))
        else:
            data = obj.rawdata
        return (obj.type, obj.parent_id, obj.getInfo('name'), info , data)

    def _getObjFromRow(self, row):
        if row is None:
            return None
        info = json.loads(zlib.decompress(row[3]))
        if row[0] in ['peak','spectrum']:
            data = json.loads(zlib.decompress(row[4]))
        else:
            data = str(row[4])
        args = (row[1], row[2], info, data)
        if row[0] == 'file':
            from aston.Datafile import Datafile
            return Datafile(self, *args)
        elif row[0] == 'peak':
            from aston.Features import Peak
            return Peak(self, *args)
        elif row[0] == 'spectrum':
            from aston.Features import Spectrum
            return Spectrum(self, *args)
        else:
            return DBObject(row[0], self, *args)

class DBObject(object):
    'Master class for peaks, features, and datafiles.'
    def __init__(self, db_type='none', db=None, db_id=None, parent_id=None, \
                     info=None, data=None):
        self.db_type = db_type
        self.db = db
        self.db_id = db_id
        self.parent_id = parent_id
        self.type = db_type
        if info is None:
            self.info = {'name':''}
        else:
            self.info = info
        self.rawdata = data
            
    def getInfo(self, fld):
        if fld not in self.info.keys():
            self._loadInfo(fld)
        
        if fld in self.info.keys():
            if self.info[fld] != '':
                return self.info[fld]
        return self._calcInfo(fld)
    
    def setInfo(self, fld, key):
        self.info[fld] = key
 
    def delInfo(self, fld):
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
        '''Save any changes to the database.'''
        if self.db is None:
            return
        
        if self.db_id is not None:
            #update object
            self.db.updateObject(self)
        else:
            #create object
            self.db.addObject(self)

    #override in subclasses
    def _loadInfo(self, fld):
        pass

    def _calcInfo(self, fld):
        return ''
