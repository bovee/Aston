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
integrators[tr('Constant Background')] = ami.constant_bl_integrate
integrators[tr('Periodic')] = ami.periodic_integrate
integrators[tr('Drop')] = ami.drop_integrate
integrators[tr('LeastSq')] = ami.leastsq_integrate

peak_models = OrderedDict()
peak_models[tr('None')] = None
peak_models[tr('Bigaussian')] = 'bigaussian'
peak_models[tr('Box')] = 'box'
peak_models[tr('ExpModGaussian')] = 'exp_mod_gaussian'
peak_models[tr('ExtremeValue')] = 'extreme_value'
peak_models[tr('Gamma')] = 'gamma_dist'
peak_models[tr('Gaussian')] = 'gaussian'
peak_models[tr('Giddings')] = 'giddings'
peak_models[tr('HVL')] = 'haarhoffvanderlinde'
peak_models[tr('LogNormal')] = 'lognormal'
peak_models[tr('Lorentzian')] = 'lorentzian'
peak_models[tr('PapaiPap')] = 'papai_pap'
peak_models[tr('Parabola')] = 'parabola'
peak_models[tr('PearsonVII')] = 'pearsonVII'
peak_models[tr('Poisson')] = 'poisson'
peak_models[tr('StudentsT')] = 'studentt'
peak_models[tr('Triangle')] = 'triangle'
peak_models[tr('Weibull3')] = 'weibull3'
