import os
import sqlite3
import pickle

from aston.Datafile import Datafile
from aston.Peak import Peak, Compound
        
class AstonDatabase():
    """This class acts as a interface to the aston.sqlite database
    that's created inside every working folder."""
    def __init__(self,database):
        self.database_path = database
        
        if not os.path.exists(database): 
            # create a database file if one doesn't exist
            self.db = sqlite3.connect(database)
            c = self.db.cursor()
            c.execute('''CREATE TABLE prefs (key TEXT, value TEXT)''')
            c.execute('''CREATE TABLE projects (project_id INTEGER PRIMARY
                      KEY ASC, project_name TEXT)''')
            c.execute('''CREATE TABLE files (file_id INTEGER PRIMARY KEY
                      ASC, project_id INTEGER, name TEXT, file_name TEXT,
                      info TEXT)''')
            c.execute('''CREATE TABLE peaks (peak_id INTEGER PRIMARY KEY
                      ASC, cmpd_id INTEGER, file_id INTEGER, ion REAL,
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
        c.execute('''SELECT file_name,name,info,project_id,
                  file_id FROM files''')
        lst = c.fetchall()
        c.close()
        self.files = [Datafile(i[0],self,i[1:5]) for i in lst]

    def updateFileList(self):
        #TODO: this needs to run in a separate thread
        #extract a list of lists of file names in my directory
        foldname = os.path.dirname(self.database_path)
        if foldname == '': foldname = os.curdir
        fnames = []
        for fold,x,files in os.walk(foldname):
            for fn in files:
                #TODO: this MWD stuff is kludgy and will probably break
                if fn[:3].upper() == 'MWD' and fn[-3:].upper() == '.CH': fn = 'mwd1A.ch'
                if fn[:3].upper() == 'DAD' and fn[-3:].upper() == '.CH': fn = 'dad1A.ch'
                fnames.append(os.path.join(fold,fn))

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
        # F is a cleanup function for data going into the database
        F = lambda x: x.replace('|',':').replace('\\','/')
        for fn in set(fnames).difference(dnames):
            dfl = Datafile(fn,None)
            if dfl is not None:
                info_str = '|'.join([F(i)+'\\'+F(j) for i,j in dfl.info.items()])
                c.execute('''INSERT INTO files (name,file_name,info)
                    VALUES (?,?,?)''',
                    (dfl.name,fn,info_str))
                self.db.commit()
        c.close()

    def updateFile(self,dt):
        #TODO: return false if update fails
        F = lambda x: x.replace('|',':').replace('\\','/')
        info_str = '|'.join([F(i)+'\\'+F(j) for i,j in dt.info.items()])
        c = self.db.cursor()
        if dt.fid[0] is None:
            c.execute('UPDATE files SET name=?,info=?,project_id=NULL WHERE file_id = ?', (dt.name,info_str,dt.fid[1]))
        else:
            c.execute('UPDATE files SET name=?,info=?,project_id=? WHERE file_id = ?', (dt.name,info_str,dt.fid[0],dt.fid[1]))
        self.db.commit()
        c.close()
        return True

    def getFileByName(self,fname):
        for dt in self.files:
            if fname.lower() == dt.name.lower():
                return dt
        return None

    def getProjects(self):
        c = self.db.cursor()
        c.execute('''SELECT project_id,project_name FROM projects''')
        lst = [[None, 'Unsorted']] + [list(i) for i in c.fetchall()]
        c.close()
        return lst

    def addProject(self,name,proj_id=None):
        c = self.db.cursor()
        if proj_id is None:
            c.execute('INSERT INTO projects (project_name) VALUES (?)',(name,))
        else:
            c.execute('''UPDATE projects SET project_name=?
                      WHERE project_id=?''',(name,proj_id))
        self.db.commit()
        c.close()

    def delProject(self,proj_id):
        c = self.db.cursor()
        c.execute('UPDATE files SET project_id = NULL WHERE project_id = ?',(proj_id,))
        c.execute('DELETE FROM projects WHERE project_id = ?',(proj_id,))
        self.db.commit()
        c.close()

    def getProjFiles(self,project_id):
        return [i for i in self.files if i.fid[0] == project_id]

    def getCompounds(self, file_ids):
        c = self.db.cursor()
        c.execute('''SELECT DISTINCT c.cmpd_id,c.cmpd_name,c.type
                  FROM compounds as c, peaks as p
                  WHERE c.cmpd_id = p.cmpd_id AND p.file_id IN (''' + ','.join(['?' for i in file_ids]) + ')',
                 file_ids)
        lst = [Compound('Unassigned',self,None,'None')]
        for i in c:
            lst.append(Compound(i[1],self,i[0],i[2]))
        c.close()
        return lst

    def addCompound(self,cmpd):
        #c.execute('''CREATE TABLE compounds (cmpd_id INTEGER PRIMARY
        #          KEY ASC, cmpd_name TEXT, type TEXT)''')
        c = self.db.cursor()
        if cmpd.cmpd_id is None:
            a = c.execute('''INSERT INTO compounds (cmpd_name,type)
                      VALUES (?,?)''',(cmpd.name,cmpd.cmpd_type))
            cmpd.cmpd_id = a.lastrowid
        else:
            c.execute('''UPDATE compounds SET cmpd_name=?, type=?
                      WHERE cmpd_id=?''',
                      (cmpd.name,cmpd.cmpd_type,cmpd.cmpd_id))
        self.db.commit()
        c.close()

    def delCompound(self,cmpd_id):
        #TODO: make it an option to move all underlying peaks to 'Unassigned'
        c = self.db.cursor()
        #c.execute('UPDATE peaks SET cmpd_id = NULL WHERE cmpd_id = ?',(cmpd_id,))
        c.execute('DELETE FROM peaks WHERE cmpd_id = ?',(cmpd_id,))
        c.execute('DELETE FROM compounds WHERE cmpd_id = ?',(cmpd_id,))
        self.db.commit()
        c.close()

    def getPeaks(self,cmpd_id):
        c = self.db.cursor()
        if cmpd_id is None:
            c.execute('''SELECT verts,ion,type,peak_id,file_id
                      FROM peaks WHERE cmpd_id IS NULL''')
        else:
            c.execute('''SELECT verts,ion,type,peak_id,file_id
                      FROM peaks WHERE cmpd_id = ?''',(cmpd_id,))
        pks = []
        for i in c:
            try: #for Python2
                verts = pickle.loads(str(i[0]))
            except: #for Python3
                verts = pickle.loads(i[0])
            pks.append(Peak(verts,i[1],i[2],(i[3],cmpd_id,i[4])))
        #lst = c.fetchall()
        c.close()
        return pks

    def addPeak(self,pk):
        c = self.db.cursor()
        pverts = pickle.dumps(pk.verts)
        if pk.ids[0] is None:
            a= c.execute('''INSERT INTO peaks (cmpd_id, file_id, ion,
                  type, verts) VALUES (?,?,?,?,?)''',
                  (pk.ids[1],pk.ids[2],pk.ion,pk.peaktype,pverts))
            pk.ids[0] = a.lastrowid
        else:
            c.execute('''UPDATE peaks SET cmpd_id=?,file_id=?,ion=?,
                  type=?, verts=? WHERE peak_id=?''',
                  (pk.ids[1],pk.ids[2],pk.ion,pk.peaktype,pverts,pk.ids[0]))
        self.db.commit()
        c.close()

    def delPeak(self, peak_id):
        c = self.db.cursor()
        c.execute('DELETE FROM peaks WHERE peak_id = ?',(peak_id,))
        self.db.commit()
        c.close()
