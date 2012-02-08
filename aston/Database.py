'''This module handles database access for Aston.'''
#pylint: disable=C0103

import os
import sqlite3
import json
import zlib 

from aston.Datafile import Datafile
from aston.Features import Peak, Spectrum, Compound

class AstonDatabase():
    """This class acts as a interface to the aston.sqlite database
    that's created inside every working folder."""
    def __init__(self, database):
        self.database_path = database
        
        if not os.path.exists(database): 
            # create a database file if one doesn't exist
            self.db = sqlite3.connect(database)
            c = self.db.cursor()
            c.execute('''CREATE TABLE prefs (key TEXT, value TEXT)''')
            c.execute('''CREATE TABLE projects (project_id INTEGER PRIMARY
                      KEY ASC, project_name TEXT)''')
            c.execute('''CREATE TABLE files (file_id INTEGER PRIMARY KEY
                      ASC, project_id INTEGER, file_name TEXT, info TEXT)''')
            c.execute('''CREATE TABLE features (ft_id INTEGER PRIMARY KEY
                      ASC, cmpd_id INTEGER, file_id INTEGER, ident TEXT,
                      type TEXT, verts BLOB)''')
            c.execute('''CREATE TABLE compounds (cmpd_id INTEGER PRIMARY
                      KEY ASC, cmpd_name TEXT, type TEXT)''')
            self.db.commit()
            c.close()
        else:
            self.db = sqlite3.connect(database)

        #update the file database (might be slow?)
        self.updateFileList()

        #read in all of the files
        c = self.db.cursor()
        c.execute('''SELECT file_name,info,project_id,
                  file_id FROM files''')
        lst = c.fetchall()
        c.close()
        self.files = [Datafile(i[0], self, i[1:4]) for i in lst]

    def updateFileList(self):
        '''Makes sure the database is in sync with the file system.'''
        #TODO: this needs to run in a separate thread
        #extract a list of lists of file names in my directory
        foldname = os.path.dirname(self.database_path)
        if foldname == '':
            foldname = os.curdir
        fnames = []
        for fold, _, files in os.walk(foldname): 
            for fn in files:
                #TODO: this MWD stuff is kludgy and will probably break
                if fn[:3].upper() == 'MWD' and \
                    fn[-3:].upper() == '.CH': fn = 'mwd1A.ch'
                if fn[:3].upper() == 'DAD' and \
                    fn[-3:].upper() == '.CH': fn = 'dad1A.ch'
                fnames.append(os.path.join(fold, fn))

        #extract a list of files from the database
        c = self.db.cursor()
        c.execute('SELECT file_name FROM files')
        dnames = set([i[0] for i in c])

        #compare the two lists -> remove deleted files from the database
        #TODO: this should only flag files as being bad, not delete them
        #from the database.
        for fn in dnames.difference(set(fnames)):
            c.execute('DELETE FROM files WHERE file_name=?',(fn,))
            self.db.commit()

        #add the new files into the database
        #TODO: generate projects and project_ids based on folder names?
        for fn in set(fnames).difference(dnames):
            dfl = Datafile(fn, None)
            if dfl is not None:
                info_str = json.dumps(dfl.info)
                c.execute('''INSERT INTO files (file_name,info)
                  VALUES (?,?)''', (fn, info_str))
                self.db.commit()
        c.close()
        
    def getKey(self, key):
#        c = self.db.cursor()
#        c.execute('''SELECT * FROM prefs WHERE key = ?''',(key,))
#        c.close()
#        return c[0]
        pass

    def setKey(self, key, val):
#        c = self.db.cursor()
#        c.execute('''SELECT * FROM prefs WHERE key = ?''',(key,))
#        c.close()
#        return c[0]
        pass

    def updateFile(self, dt):
        '''Updates a file entry in the database.'''
        #TODO: return false if update fails
        info_str = json.dumps(dt.info)
        c = self.db.cursor()
        if dt.fid[0] is None:
            c.execute('''UPDATE files SET info=?,project_id=NULL 
              WHERE file_id = ?''', (info_str, dt.fid[1]))
        else:
            c.execute('''UPDATE files SET info=?,project_id=? 
              WHERE file_id = ?''', (info_str, dt.fid[0], dt.fid[1]))
        self.db.commit()
        c.close()
        return True

    def getFileByName(self, fname):
        '''Return a datafile object corresponding to fname.'''
        for dt in self.files:
            if fname.lower() == dt.getInfo('name').lower():
                return dt
        return None

    def getFileByID(self,file_id):
        '''Return a datafile object corresponding to file_id.'''
        for dt in self.files:
            if file_id == dt.fid[1]:
                return dt
        return None
        
    def getProjects(self):
        '''Returns a list of all projects in the database.'''
        c = self.db.cursor()
        c.execute('''SELECT project_id,project_name FROM projects''')
        lst = [[None, 'Unsorted']] + [list(i) for i in c.fetchall()]
        c.close()
        return lst

    def addProject(self, name, proj_id=None):
        '''Adds a project to the database.'''
        c = self.db.cursor()
        if proj_id is None:
            a = c.execute('''INSERT INTO projects (project_name) 
                      VALUES (?)''', (name,))
            self.db.commit()
            c.close()
            return a.lastrowid
        else:
            c.execute('''UPDATE projects SET project_name=?
                      WHERE project_id=?''', (name, proj_id))
            self.db.commit()
            c.close()
            return None

    def delProject(self, proj_id):
        '''Delete a project from the database.'''
        c = self.db.cursor()
        c.execute('''UPDATE files SET project_id = NULL
                  WHERE project_id = ?''',(proj_id,))
        c.execute('DELETE FROM projects WHERE project_id = ?', (proj_id,))
        self.db.commit()
        c.close()

    def getProjFiles(self, project_id):
        '''Returns the files associated with a specific project.'''
        return [i for i in self.files if i.fid[0] == project_id]

    def getCompounds(self, file_ids):
        '''Returns a list of compounds associated with the file_ids.'''
        c = self.db.cursor()
        c.execute('''SELECT DISTINCT c.cmpd_id,c.cmpd_name,c.type
                  FROM compounds as c, features as f
                  WHERE c.cmpd_id = f.cmpd_id AND f.file_id IN (''' + \
                  ','.join(['?' for i in file_ids]) + ')', file_ids)
        lst = [Compound('Unassigned', self, None, 'None')]
        for i in c:
            lst.append(Compound(i[1], self, i[0], i[2]))
        c.close()
        return lst

    def addCompound(self, cmpd):
        '''Add a compound to the database.'''
        #c.execute('''CREATE TABLE compounds (cmpd_id INTEGER PRIMARY
        #          KEY ASC, cmpd_name TEXT, type TEXT)''')
        c = self.db.cursor()
        if cmpd.cmpd_id is None:
            a = c.execute('''INSERT INTO compounds (cmpd_name,type)
                      VALUES (?,?)''',(cmpd.name, cmpd.cmpd_type))
            cmpd.cmpd_id = a.lastrowid
        else:
            c.execute('''UPDATE compounds SET cmpd_name=?, type=?
                      WHERE cmpd_id=?''',
                      (cmpd.name, cmpd.cmpd_type, cmpd.cmpd_id))
        self.db.commit()
        c.close()

    def delCompound(self, cmpd_id):
        '''Delete a compound from the database.'''
        #TODO: make it an option to move all underlying peaks to 'Unassigned'
        c = self.db.cursor()
        c.execute('DELETE FROM features WHERE cmpd_id = ?',(cmpd_id,))
        c.execute('DELETE FROM compounds WHERE cmpd_id = ?',(cmpd_id,))
        self.db.commit()
        c.close()

    def getFeats(self, cmpd_id):
        '''Return a list of features associated with a specific compound.'''
        c = self.db.cursor()
        if cmpd_id is None:
            c.execute('''SELECT verts,ident,type,ft_id,file_id
                         FROM features WHERE cmpd_id IS NULL''')
        else:
            c.execute('''SELECT verts,ident,type,ft_id,file_id
                         FROM features WHERE cmpd_id = ?''',(cmpd_id,))
        fts = []
        for i in c:
            verts = json.loads(zlib.decompress(i[0]))
            fts.append(self._makeFt(verts, i[2], i[1], (i[3], cmpd_id, i[4])))
        c.close()
        return fts
    
    def getFeatsByFile(self,file_id):
        '''Return a list of features associated with a specific file.'''
        c = self.db.cursor()
        c.execute('''SELECT verts,ident,type,ft_id,cmpd_id
                     FROM features WHERE file_id IS ?''',(file_id,))
        fts = []
        for i in c:
            verts = json.loads(zlib.decompress(i[0]))
            fts.append(self._makeFt(verts, i[2], i[1], (i[3], i[4], file_id)))
        c.close()
        return fts
    
    def _makeFt(self,verts,ft_type,ident,ids):
        #TODO: better way of doing this type-checking
        if ft_type == 'Peak':
            #ident is the ion or wavelength the peak was integrated over
            ft = Peak(verts, ids, ident)
        elif ft_type == 'Spectrum':
            ft = Spectrum(verts, ids)
        ft.dt = self.getFileByID(ids[2])
        return ft

    def addFeat(self, ft):
        '''Add a feature to the database or make a change 
        to an existing one.'''
        c = self.db.cursor()
        fdata = buffer(zlib.compress(json.dumps(ft.data_for_export()), 9))
        if isinstance(ft, Peak):
            ident = ft.ion
        else:
            ident = None
        if ft.ids[0] is None:
            a = c.execute('''INSERT INTO features (cmpd_id, file_id,
                  ident, type, verts) VALUES (?,?,?,?,?)''',
                  (ft.ids[1], ft.ids[2], ident, ft.cls, fdata))
            ft.ids[0] = a.lastrowid
        else:
            c.execute('''UPDATE features SET cmpd_id=?,file_id=?,ident=?,
                  type=?, verts=? WHERE ft_id=?''',
                  (ft.ids[1], ft.ids[2], ident, ft.cls, fdata, ft.ids[0]))
        self.db.commit()
        c.close()

    def delFeat(self, ft_id):
        '''Delete a feature from the database.'''
        c = self.db.cursor()
        c.execute('DELETE FROM features WHERE ft_id = ?',(ft_id,))
        self.db.commit()
        c.close()
