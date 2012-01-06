# -*- coding: utf-8 -*-
class MethodDatabase(object):
    def __init__(self,database):
        #import os, sqlite3
        pass
# fields:
# 1. inst_type - HPLC, GC, etc
# 2. name - BARUA, RJBPROT.M, etc.
# 3. revision - version number of method - e.g. 1,2,3 or date
# 4. parameters -
# T, solv. % (A,B,C,D), flow rate, column type, mobile phase type
#
# opt. parameters: col. switches, main/bypass switches, rinses, inj. vol.
# 

class Method(object):
    def __init__(self,name):
        self.name = name
        self.mtPrms = {}

        self.name = "RJBPROT" #strip out *.M suffix
        self.mtPrms['col'] = 'Agilent Poroshell 300SB'
        self.mtPrms['col-type'] = 'RP'
        self.mtPrms['col-dim'] = '7.8,150' #mm x mm
        self.mtPrms['col-part-size'] = '5' #micron
        self.mtPrms['len'] = '11' #minutes
        self.mtPrms['inj-size'] = '5' #microliters
        self.mtPrms['tmp'] = '70' #deg C
        self.mtPrms['prs'] = '' #not regulated
        self.mtPrms['flw'] = '500' #ul/min
        self.mtPrms['slv-A'] = '100 H2O,0.1 formic'
        self.mtPrms['slv-B'] = '100 MeOH,0.1 formic'
        self.mtPrms['slv-B-per'] = 'S:5,0:30,9:80,9.01:100,11:100'
        #5% default %B, pre-run
        self.mtPrms['ms-int-mode'] = 'POS-ESI'

        #not a part of the method
        self.mtPrms['smp'] = '5 protein mix'
        self.mtPrms['smp-conc'] = '5 mg/ml'

flds = {
    # aston specific information
        'name':'Name',
        'vis':'Vis?',
        'traces':'Traces',
    # method information
        'm':'Method Name',
        'm-type':'Chromatography Type',
        'm-col':'Column Name',
        'm-col-type':'Column Phase',
        'm-col-dim':'Column Dimensions (mm x mm)',
        'm-col-part-size':'Column Particle Size (µ)',
        'm-len':'Run Length (min)',
        'm-inj-size':'Injection Size (µl)',
        'm-tmp':'Temperature (°C)',
        'm-prs':'Pressure (kbar)',
        'm-flw':'Flow (µl/min)',
        'm-slv':'Solvent/Carrier',
        'm-slv-B':'Solvent B',
        'm-slv-C':'Solvent C',
        'm-slv-D':'Solvent D',
        'm-uv':'UV Wavelengths',
        'm-ms-int-mode':'MS Interface Mode',
        'm-y-units':'Units',
    # run information
        'r-filename':'File Name',
        'r-smp':'Sample',
        'r-smp-conc':'Sample Concentration',
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
