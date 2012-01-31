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

flds = {
    # aston specific information
        'name':'Name',
        'vis':'Vis?',
        'traces':'Traces',
    # method information
        'm':'Method Name', #e.g. RJBPROT. strip out *.M suffix
        'm-type':'Chromatography Type',
        'm-col':'Column Name',
        'm-col-type':'Column Phase',
        'm-col-dim':'Column Dimensions (mm x mm)',
        'm-col-part-size':'Column Particle Size (µ)',
        'm-len':'Run Length (min)',
        'm-inj-size':'Injection Size (µl)',
        'm-tmp':'Temperature (°C)', #type = time-dict
        'm-prs':'Pressure (kbar)', #type = time-dict
        'm-flw':'Flow (µl/min)', #type = time-dict
        'm-slv':'Solvent/Carrier', #Solvent A
        'm-slv-B':'Solvent B',
        'm-slv-B-per':'% Solvent B', #type = time-dict
        'm-slv-C':'Solvent C',
        'm-slv-B-per':'% Solvent C', #type = time-dict
        'm-slv-D':'Solvent D',
        'm-slv-B-per':'% Solvent D', #type = time-dict
        'm-uv':'UV Wavelengths',
        'm-ms-int-mode':'MS Interface Mode',
        'm-y-units':'Units',
    # run information
        'r-filename':'File Name',
        'r-smp':'Sample', #e.g. BSA
        'r-smp-conc':'Sample Concentration', #e.g. 5 mg/ml
        'r-date':'Date',
        'r-opr':'Operator',
        'r-type':'Type', #sample, standard, etc.
        'r-vial-pos':'Vial Position',
        'r-seq-num':'Sequence Number',
        'r-inst':'Instrument',
    # information generated in the program ("statistics")
        's-file-type':'File Type',
        's-scans':'Scans',
        's-st-time':'Start Time (min)',
        's-en-time':'End Time (min)',
    # data transformations
        't-scale':'Scale',
        't-offset':'Offset',
        't-smooth':'Smoothing Method',
        't-smooth-order':'Smoothing Order',
        't-smooth-window':'Smoothing Window',
        't-remove-noise':'Noise Removal Method',
       }

#for time-dicts:
#blank = not regulated otherwise, it's a dict with at least one entry: S
#e.g. {'S':5,0:30,9:80,9.01:100,11:100}
