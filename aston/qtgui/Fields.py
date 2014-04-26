# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from collections import OrderedDict
from aston.resources import tr
from aston.qtgui.MenuOptions import peak_models


aston_groups = OrderedDict()
aston_groups['m'] = tr('Method')
aston_groups['d'] = tr('Detector')
aston_groups['r'] = tr('Run')
aston_groups['s'] = tr('Stats')
aston_groups['p'] = tr('Peaks')

aston_fields = OrderedDict()

# aston specific information
aston_fields['name'] = tr('Name')
aston_fields['sel'] = tr('Sel?')
aston_fields['vis'] = tr('Vis?')
aston_fields['color'] = tr('Color')
aston_fields['style'] = tr('Style')

# method information
aston_fields['m-name'] = tr('Method Name')  # e.g. BPROT. strip out *.M suffix
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
aston_fields['m-slv-b'] = tr('Solvent B')
aston_fields['m-slv-b-per'] = tr('% Solvent B')  # type = time-dict
aston_fields['m-slv-c'] = tr('Solvent C')
aston_fields['m-slv-c-per'] = tr('% Solvent C')  # type = time-dict
aston_fields['m-slv-d'] = tr('Solvent D')
aston_fields['m-slv-d-per'] = tr('% Solvent D')  # type = time-dict

# detector information
aston_fields['d-name'] = tr('Detector Type')
aston_fields['d-ms-int-mode'] = tr('MS Interface Mode')
aston_fields['d-y-units'] = tr('Units')
#TODO: y units should be read in TraceFile and returned with DataFrame?

# run information
aston_fields['r-filenames'] = tr('File Name')
aston_fields['r-analyses'] = tr('Analyses')
aston_fields['r-smp'] = tr('Sample')  # e.g. BSA
aston_fields['r-smp-conc'] = tr('Sample Concentration')  # e.g. 5 mg/ml
aston_fields['r-date'] = tr('Date')
aston_fields['r-opr'] = tr('Operator')
aston_fields['r-type'] = tr('Type')  # sample, standard, etc.
aston_fields['r-vial-pos'] = tr('Vial Position')
aston_fields['r-seq-num'] = tr('Sequence Number')
aston_fields['r-inst'] = tr('Instrument')
aston_fields['r-d18o-std'] = tr('Reference δ¹⁸O Value (‰)')
aston_fields['r-d13c-std'] = tr('Reference δ¹³C Value (‰)')
aston_fields['r-file-type'] = tr('File Type')
aston_fields['r-st-time'] = tr('Start Time (min)')
aston_fields['r-en-time'] = tr('End Time (min)')

# information generated in the program ("statistics")
aston_fields['s-scans'] = tr('# of Scans')
aston_fields['s-mzs'] = tr("# of MZ's/Wavelengths")
aston_fields['s-mz-names'] = tr("MZ/Wavelength Names")
aston_fields['s-peaks'] = tr('# of Peaks')
aston_fields['s-spectra'] = tr('# of Spectra')
aston_fields['s-peaks-st'] = tr('First Peak RT (min)')
aston_fields['s-peaks-en'] = tr('Last Peak RT (min)')
aston_fields['s-pkcap'] = tr('Peak Capacity (# Peaks)')
aston_fields['s-scale'] = tr('Scale')
aston_fields['s-offset'] = tr('Offset')
aston_fields['s-smooth'] = tr('Smoothing Method')
aston_fields['s-smooth-order'] = tr('Smoothing Order')
aston_fields['s-smooth-window'] = tr('Smoothing Window')
aston_fields['s-remove-noise'] = tr('Noise Removal Method')

# peak info
aston_fields['p-type'] = tr('Peak Type')
aston_fields['p-model'] = tr('Peak Model')
aston_fields['p-model-fit'] = tr('Peak Model Fit (r²)')
aston_fields['p-area'] = tr('Peak Area')
aston_fields['p-length'] = tr('Peak Width (min)')
aston_fields['p-height'] = tr('Peak Height')
aston_fields['p-time'] = tr('Peak Retention Time (min)')
aston_fields['p-pwhm'] = tr('Peak Width Half-Max (min)')
aston_fields['p-d13c'] = tr('δ¹³C Value (‰)')

#for time-dicts:
#blank = not regulated otherwise, it's a dict with at least one entry: S
#e.g. {'S':5,0:30,9:80,9.01:100,11:100}

#TODO: add other options back in
aston_field_opts = {}
aston_field_opts['style'] = OrderedDict()
aston_field_opts['style']['solid'] = tr('Solid')
aston_field_opts['style']['dash'] = tr('Dash')
aston_field_opts['style']['dot'] = tr('Dot')
aston_field_opts['style']['dash-dot'] = tr('Dash-Dot')
aston_field_opts['style']['heatmap'] = tr('Heatmap')
aston_field_opts['style']['colors'] = tr('Colors')

aston_field_opts['r-type'] = OrderedDict()
aston_field_opts['r-type'][''] = tr('None')
aston_field_opts['r-type']['sample'] = tr('Sample')
aston_field_opts['r-type']['std'] = tr('Standard')
aston_field_opts['r-type']['calib'] = tr('Calibration Curve')
aston_field_opts['r-type']['negctrl'] = tr('Negative Control')
aston_field_opts['r-type']['posctrl'] = tr('Positive Control')

aston_field_opts['s-smooth'] = OrderedDict()
aston_field_opts['s-smooth'][''] = tr('None')
aston_field_opts['s-smooth']['moving'] = tr('Moving Average')
aston_field_opts['s-smooth']['savitzky'] = tr('Savitzky-Golay')

aston_field_opts['m-type'] = OrderedDict()
aston_field_opts['m-type'][''] = tr('None')
aston_field_opts['m-type']['hplc'] = tr('HPLC')
aston_field_opts['m-type']['gc'] = tr('GC')

aston_field_opts['d-name'] = OrderedDict()
aston_field_opts['d-name'][''] = tr('None')
aston_field_opts['d-name']['uv-dad'] = tr('DAD')
aston_field_opts['d-name']['uv-mwd'] = tr('MWD')
aston_field_opts['d-name']['ms-quad'] = tr('Quadrupole')
aston_field_opts['d-name']['ms-tof'] = tr('Time of Flight')
aston_field_opts['d-name']['ms-qtof'] = tr('Quad Time of Flight')
aston_field_opts['d-name']['ms-qqq'] = tr('QQQ')

aston_field_opts['p-model'] = OrderedDict()
for k in peak_models:
    aston_field_opts['p-model'][peak_models[k]] = k

aston_field_opts['p-type'] = OrderedDict()
aston_field_opts['p-type'][''] = tr('None')
aston_field_opts['p-type']['sample'] = tr('Sample')
aston_field_opts['p-type']['std'] = tr('Standard')
aston_field_opts['p-type']['isostd'] = tr('Isotope Standard')

aston_field_opts['color-1d'] = OrderedDict()
aston_field_opts['color-1d']['auto'] = tr('Auto')
aston_field_opts['color-1d']['black'] = tr('Black')
aston_field_opts['color-1d']['gray'] = tr('Gray')
aston_field_opts['color-1d']['silver'] = tr('Silver')
aston_field_opts['color-1d']['red'] = tr('Red')
aston_field_opts['color-1d']['maroon'] = tr('Maroon')
aston_field_opts['color-1d']['orange'] = tr('Orange')
aston_field_opts['color-1d']['yellow'] = tr('Yellow')
aston_field_opts['color-1d']['olive'] = tr('Olive')
aston_field_opts['color-1d']['lime'] = tr('Lime')
aston_field_opts['color-1d']['aqua'] = tr('Aqua')
aston_field_opts['color-1d']['teal'] = tr('Teal')
aston_field_opts['color-1d']['green'] = tr('Green')
aston_field_opts['color-1d']['blue'] = tr('Blue')
aston_field_opts['color-1d']['navy'] = tr('Navy')
aston_field_opts['color-1d']['fuchsia'] = tr('Fuchsia')
aston_field_opts['color-1d']['purple'] = tr('Purple')

aston_field_opts['color-2d'] = OrderedDict()
aston_field_opts['color-2d']['auto'] = tr('Auto')
aston_field_opts['color-2d']['hsv'] = tr('Rainbow')
aston_field_opts['color-2d']['Accent'] = tr('Pastels')
aston_field_opts['color-2d']['BrBG'] = tr('Brown-Blue-Green')
aston_field_opts['color-2d']['RdBu'] = tr('Red-Blue')
aston_field_opts['color-2d']['RdYlBu'] = tr('Red-Yellow-Blue')
aston_field_opts['color-2d']['RdYlGn'] = tr('Red-Yellow-Green')
aston_field_opts['color-2d']['RdBu'] = tr('Red-Blue')
aston_field_opts['color-2d']['PiYG'] = tr('Pink-Yellow-Green')
aston_field_opts['color-2d']['Spectral'] = tr('Spectral')
aston_field_opts['color-2d']['spring'] = tr('Spring')
aston_field_opts['color-2d']['summer'] = tr('Summer')
aston_field_opts['color-2d']['autumn'] = tr('Autumn')
aston_field_opts['color-2d']['winter'] = tr('Winter')
aston_field_opts['color-2d']['cool'] = tr('Cool')
aston_field_opts['color-2d']['copper'] = tr('Copper')
aston_field_opts['color-2d']['jet'] = tr('Jet')
aston_field_opts['color-2d']['Paired'] = tr('Paired')
aston_field_opts['color-2d']['binary'] = tr('White-Black')
aston_field_opts['color-2d']['gray'] = tr('Black-White')
