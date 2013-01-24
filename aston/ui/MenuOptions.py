# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from collections import OrderedDict
from PyQt4.QtCore import QObject
import aston.Math.Integrators as ami
import aston.Math.PeakFinding as ampf


tr = lambda s: QObject().trUtf8(s)

peak_finders = OrderedDict()
peak_finders[tr('Simple')] = ampf.simple_peak_find
peak_finders[tr('StatSlope')] = ampf.stat_slope_peak_find
peak_finders[tr('Wavelet')] = ampf.wavelet_peak_find
peak_finders[tr('Event')] = ampf.event_peak_find

integrators = OrderedDict()
integrators[tr('Overlap')] = ami.simple_integrate
integrators[tr('Drop')] = ami.drop_integrate
integrators[tr('LeastSq')] = ami.leastsq_integrate

peak_models = {tr('None'): None,
               tr('Bigaussian'): 'bigaussian',
               tr('Box'): 'box',
               tr('ExpModGaussian'): 'exp_mod_gaussian',
               tr('ExtremeValue'): 'extreme_value',
               tr('Gamma'): 'gamma_dist',
               tr('Gaussian'): 'gaussian',
               tr('Giddings'): 'giddings',
               tr('HVL'): 'haarhoffvanderlinde',
               tr('LogNormal'): 'lognormal',
               tr('Lorentzian'): 'lorentzian',
               tr('PapaiPap'): 'papai_pap',
               tr('Parabola'): 'parabola',
               tr('PearsonVII'): 'pearsonVII',
               tr('Poisson'): 'poisson',
               tr('StudentsT'): 'studentt',
               tr('Triangle'): 'triangle',
               tr('Weibull3'): 'weibull3'}
