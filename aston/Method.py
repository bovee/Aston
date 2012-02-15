# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import sqlite3
import json
import zlib

class MethodDatabase(object):
    def __init__(self,database):
        self.database_path = database
        
        if not os.path.exists(database): 
            # create a database file if one doesn't exist
            self.db = sqlite3.connect(database)
            c = self.db.cursor()
            c.execute('''CREATE TABLE methods (m_id INTEGER PRIMARY KEY,
                      name TEXT, rev TEXT, type TEXT, info TEXT)''')
            self.db.commit()
            c.close()
        else:
            self.db = sqlite3.connect(database)

        #read in all of the files
        c = self.db.cursor()
        c.execute('''SELECT name, rev, info, m_id FROM methods''')
        lst = c.fetchall()
        c.close()
        self.methods = [Method(*lst) for i in lst]

class Method(object):
    def __init__(self, name, rev, info=None, m_id = None):
        self.name = name
        self.rev = rev
        self.info = info
        self.m_id = m_id
