# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from PyQt4.QtCore import QObject

tr = lambda s: QObject().trUtf8(s)

aston_groups = {'m': tr('Method'),
          'r': tr('Run'),
          's': tr('Stats'),
          't': tr('Transforms'),
          'p': tr('Peaks'),
          'sp': tr('Spectra')}

aston_fields = {
    # aston specific information
        'name': tr('Name'),
        'vis': tr('Vis?'),
        'traces': tr('Traces'),
    # method information
        'm': tr('Method Name'),  # e.g. RJBPROT. strip out *.M suffix
        'm-type': tr('Chromatography Type'),
        'm-col': tr('Column Name'),
        'm-col-type': tr('Column Phase'),
        'm-col-dim': tr('Column Dimensions (mm x mm)'),
        'm-col-part-size': tr('Column Particle Size (µ)'),
        'm-len': tr('Run Length (min)'),
        'm-inj-size': tr('Injection Size (µl)'),
        'm-tmp': tr('Temperature (°C)'),  # type = time-dict
        'm-prs': tr('Pressure (kbar)'),  # type = time-dict
        'm-flw': tr('Flow (µl/min)'),  # type = time-dict
        'm-slv': tr('Solvent/Carrier'),  # Solvent A
        'm-slv-B': tr('Solvent B'),
        'm-slv-B-per': tr('% Solvent B'),  # type = time-dict
        'm-slv-C': tr('Solvent C'),
        'm-slv-C-per': tr('% Solvent C'),  # type = time-dict
        'm-slv-D': tr('Solvent D'),
        'm-slv-D-per': tr('% Solvent D'),  # type = time-dict
        'm-detect': tr('Detector Type'),
        'm-uv': tr('UV Wavelengths'),
        'm-ms-int-mode': tr('MS Interface Mode'),
        'm-y-units': tr('Units'),
    # run information
        'r-filename': tr('File Name'),
        'r-smp': tr('Sample'),  # e.g. BSA
        'r-smp-conc': tr('Sample Concentration'),  # e.g. 5 mg/ml
        'r-date': tr('Date'),
        'r-opr': tr('Operator'),
        'r-type': tr('Type'),  # sample, standard, etc.
        'r-vial-pos': tr('Vial Position'),
        'r-seq-num': tr('Sequence Number'),
        'r-inst': tr('Instrument'),
        'r-d13c-std': tr('Reference δ13C Value (‰)'),
    # information generated in the program ("statistics")
        's-file-type': tr('File Type'),
        's-scans': tr('Scans'),
        's-mzs': tr('Ions'),
        's-st-time': tr('Start Time (min)'),
        's-en-time': tr('End Time (min)'),
        's-peaks': tr('# of Peaks'),
        's-spectra': tr('# of Spectra'),
        's-peaks-st': tr('First Peak RT (min)'),
        's-peaks-en': tr('Last Peak RT (min)'),
    # data transformations
        't-scale': tr('Scale'),
        't-offset': tr('Offset'),
        't-smooth': tr('Smoothing Method'),
        't-smooth-order': tr('Smoothing Order'),
        't-smooth-window': tr('Smoothing Window'),
        't-remove-noise': tr('Noise Removal Method'),
    # peak info
        'p-type': tr('Peak Type'),
        'p-model': tr('Peak Model'),
        'p-s-area': tr('Peak Area'),
        'p-s-length': tr('Peak Width (min)'),
        'p-s-height': tr('Peak Height'),
        'p-s-time': tr('Peak Retention Time (min)'),
        'p-s-pwhm': tr('Peak Width Half-Max (min)'),
        'p-s-pkcap': tr('Peak Capacity (# Peaks)'),
    #spectrum info
        'sp-type': tr('Spectrum Type'),
        'sp-time': tr('Spectrum Time (min)'),
        'sp-d13c': tr('δ13C Value (‰)'),
       }

#for time-dicts:
#blank = not regulated otherwise, it's a dict with at least one entry: S
#e.g. {'S':5,0:30,9:80,9.01:100,11:100}

aston_field_opts = {
    'r-type': ['None', 'Sample', 'Standard'],
    'p-type': ['None', 'Sample', 'Standard'],
    'p-model': ['None', 'Normal', 'Lognormal', 'Exp Mod Normal', 'Lorentzian'],
    'sp-type': ['None', 'Sample', 'Standard', 'Isotope Standard'],
    't-smooth': ['None', 'Moving Average', 'Savitsky-Golay'],
    't-remove-noise': ['None'],
    'm-type': ['None', 'HPLC', 'GC'],
    'm-detect': ['None', 'DAD-UV', 'MWD-UV', 'Quad-MS', 'TOF-MS', 'Q-TOF-MS'],
}
