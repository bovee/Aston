# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from collections import OrderedDict
from aston.resources import tr
from aston.qtgui.MenuOptions import peak_models


aston_groups = OrderedDict()
aston_groups['m'] = tr('Method')
aston_groups['r'] = tr('Run')
aston_groups['s'] = tr('Stats')
aston_groups['t'] = tr('Transforms')
aston_groups['p'] = tr('Peaks')

aston_fields = OrderedDict()
# aston specific information
aston_fields['name'] = tr('Name')
aston_fields['sel'] = tr('Sel?')
aston_fields['vis'] = tr('Vis?')
aston_fields['traces'] = tr('Traces')
# method information
aston_fields['m'] = tr('Method Name')  # e.g. RJBPROT. strip out *.M suffix
aston_fields['m-type'] = tr('Chromatography Type')
aston_fields['m-col'] = tr('Column Name')
aston_fields['m-col-type'] = tr('Column Phase')
aston_fields['m-col-dim'] = tr('Column Dimensions (mm x mm)')
aston_fields['m-col-part-size'] = tr('Column Particle Size (µ)')
aston_fields['m-len'] = tr('Run Length (min)')
aston_fields['m-inj-size'] = tr('Injection Size (µl)')
aston_fields['m-tmp'] = tr('Temperature (°C)')  # type = time-dict
aston_fields['m-prs'] = tr('Pressure (kbar)')  # type = time-dict
aston_fields['m-flw'] = tr('Flow (µl/min)')  # type = time-dict
aston_fields['m-slv'] = tr('Solvent/Carrier')  # Solvent A
aston_fields['m-slv-B'] = tr('Solvent B')
aston_fields['m-slv-B-per'] = tr('% Solvent B')  # type = time-dict
aston_fields['m-slv-C'] = tr('Solvent C')
aston_fields['m-slv-C-per'] = tr('% Solvent C')  # type = time-dict
aston_fields['m-slv-D'] = tr('Solvent D')
aston_fields['m-slv-D-per'] = tr('% Solvent D')  # type = time-dict
aston_fields['m-detect'] = tr('Detector Type')
aston_fields['m-uv'] = tr('UV Wavelengths')
aston_fields['m-ms-int-mode'] = tr('MS Interface Mode')
aston_fields['m-y-units'] = tr('Units')
# run information
aston_fields['r-filename'] = tr('File Name')
aston_fields['r-smp'] = tr('Sample')  # e.g. BSA
aston_fields['r-smp-conc'] = tr('Sample Concentration')  # e.g. 5 mg/ml
aston_fields['r-date'] = tr('Date')
aston_fields['r-opr'] = tr('Operator')
aston_fields['r-type'] = tr('Type')  # sample, standard, etc.
aston_fields['r-vial-pos'] = tr('Vial Position')
aston_fields['r-seq-num'] = tr('Sequence Number')
aston_fields['r-inst'] = tr('Instrument')
aston_fields['r-d18o-std'] = tr('Reference δ18O Value (‰)')
aston_fields['r-d13c-std'] = tr('Reference δ13C Value (‰)')
# information generated in the program ("statistics")
aston_fields['s-file-type'] = tr('File Type')
aston_fields['s-scans'] = tr('Scans')
aston_fields['s-mzs'] = tr('Ions')
aston_fields['s-st-time'] = tr('Start Time (min)')
aston_fields['s-en-time'] = tr('End Time (min)')
aston_fields['s-peaks'] = tr('# of Peaks')
aston_fields['s-spectra'] = tr('# of Spectra')
aston_fields['s-peaks-st'] = tr('First Peak RT (min)')
aston_fields['s-peaks-en'] = tr('Last Peak RT (min)')
# data transformations
aston_fields['t-scale'] = tr('Scale')
aston_fields['t-offset'] = tr('Offset')
aston_fields['t-smooth'] = tr('Smoothing Method')
aston_fields['t-smooth-order'] = tr('Smoothing Order')
aston_fields['t-smooth-window'] = tr('Smoothing Window')
aston_fields['t-remove-noise'] = tr('Noise Removal Method')
# peak info
aston_fields['p-type'] = tr('Peak Type')
aston_fields['p-model'] = tr('Peak Model')
aston_fields['p-s-model-fit'] = tr('Peak Model Fit (r²)')
aston_fields['p-s-area'] = tr('Peak Area')
aston_fields['p-s-length'] = tr('Peak Width (min)')
aston_fields['p-s-height'] = tr('Peak Height')
aston_fields['p-s-time'] = tr('Peak Retention Time (min)')
aston_fields['p-s-pwhm'] = tr('Peak Width Half-Max (min)')
aston_fields['p-s-pkcap'] = tr('Peak Capacity (# Peaks)')
aston_fields['p-s-d13c'] = tr('δ13C Value (‰)')

#for time-dicts:
#blank = not regulated otherwise, it's a dict with at least one entry: S
#e.g. {'S':5,0:30,9:80,9.01:100,11:100}

aston_field_opts = {
    'r-type': ['None', 'Sample', 'Standard'],
    'p-type': ['None', 'Sample', 'Standard', 'Isotope Standard'],
    'p-model': [k for k in peak_models],
    'sp-type': ['None', 'Sample', 'Standard', 'Isotope Standard'],
    't-smooth': ['None', 'Moving Average', 'Savitsky-Golay'],
    't-remove-noise': ['None'],
    'm-type': ['None', 'HPLC', 'GC'],
    'm-detect': ['None', 'DAD-UV', 'MWD-UV', 'Quad-MS', 'TOF-MS', 'Q-TOF-MS'],
}
