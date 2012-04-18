# -*- coding: utf-8 -*-
#TODO: for Python 3, remove all u' prefixes
aston_groups = {'m':'Method',
          'r':'Run',
          's':'Stats',
          't':'Transforms',
          'p':'Peaks',
          'sp':'Spectra'}

aston_fields = {
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
        'm-col-part-size':u'Column Particle Size (µ)',
        'm-len':'Run Length (min)',
        'm-inj-size':u'Injection Size (µl)',
        'm-tmp':u'Temperature (°C)', #type = time-dict
        'm-prs':'Pressure (kbar)', #type = time-dict
        'm-flw':u'Flow (µl/min)', #type = time-dict
        'm-slv':'Solvent/Carrier', #Solvent A
        'm-slv-B':'Solvent B',
        'm-slv-B-per':'% Solvent B', #type = time-dict
        'm-slv-C':'Solvent C',
        'm-slv-B-per':'% Solvent C', #type = time-dict
        'm-slv-D':'Solvent D',
        'm-slv-B-per':'% Solvent D', #type = time-dict
        'm-detect':'Detector Type',
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
        'r-d13c-std':u'Reference δ13C Value (‰)',
    # information generated in the program ("statistics")
        's-file-type':'File Type',
        's-scans':'Scans',
        's-st-time':'Start Time (min)',
        's-en-time':'End Time (min)',
        's-peaks':'# of Peaks',
        's-spectra':'# of Spectra',
        's-st-peaks':'First Peak RT (min)',
        's-en-peaks':'Last Peak RT (min)',
    # data transformations
        't-scale':'Scale',
        't-offset':'Offset',
        't-smooth':'Smoothing Method',
        't-smooth-order':'Smoothing Order',
        't-smooth-window':'Smoothing Window',
        't-remove-noise':'Noise Removal Method',
    # peak info
        'p-ion':'Peak Ion',
        'p-type':'Peak Type',
        'p-model':'Peak Model',
        'p-s-area':'Peak Area',
        'p-s-length':'Peak Width (min)',
        'p-s-height':'Peak Height',
        'p-s-time':'Peak Retention Time (min)',
        'p-s-pwhm':'Peak Width Half-Max (min)',
        'p-s-pkcap':'Peak Capacity (# Peaks)',
    #spectrum info
        'sp-type':'Spectrum Type',
        'sp-d13c':u'δ13C Value (‰)',
       }

#for time-dicts:
#blank = not regulated otherwise, it's a dict with at least one entry: S
#e.g. {'S':5,0:30,9:80,9.01:100,11:100}

aston_field_opts = {
    'r-type':['None','Sample','Standard'],
    'p-type':['None','Sample','Standard'],
    'p-model':['None','Normal','Lognormal','Exp Mod Normal','Lorentzian'],
    'sp-type':['None','Sample','Standard','Isotope Standard'],
    't-smooth':['None','Moving Average','Savitsky-Golay'],
    't-remove-noise':['None'],
    'm-type':['None','HPLC','GC'],
    'm-detect':['None','DAD-UV','MWD-UV','Quad-MS','TOF-MS','Q-TOF-MS'],
}
