# -*- coding: utf-8 -*-
import numpy as np
import re
from aston.trace import Trace
from aston.trace.math_chromatograms import molmz, mzminus, basemz
from aston.trace.math_traces import (ts_func, fft, noisefilter,
                                     movingaverage, savitzkygolay)

functions = {}  # TODO
istr_type_2d = ['ms', 'uv', 'irms']
istr_type_evts = ['refgas', 'fia', 'fxn', 'deadvol']

SHORTCUTS = {
    'alkanes': '57#ms+71#ms+85#ms',
    'alkenes': '55#ms+69#ms+83#ms',
    'alkadienes': '67#ms+81#ms',
    'hopanes': '191#ms',
    'hopenes': '189#ms',
    'steranes': '217#ms',
    'ketones': '59#ms',
    'amides': '59#ms',
    'tms': '73#ms',
    'methylesters': '74#ms',
    'alcohols': '75#ms',
    'pthalates': '149#ms'
}


def tokens(istr):
    """
    Same as tokenize, but returns only tokens
    (and at all parantheses levels).
    """

    # make a list of all alphanumeric tokens
    toks = re.findall(r'[^\*\\\+\-\^\(\)]+\(?', istr)

    # remove the functions
    return [t for t in toks if not t.endswith('(')]


def istr_type(istr):
    """
    Given an "ion" specification, determine its "type", e.g. 1D, Events, etc.
    """
    data = set(i.rstrip('0123456789') for i in tokens(istr))
    has_events = not data.isdisjoint(istr_type_evts)
    has_2d = not data.isdisjoint(istr_type_2d)
    has_1d = data.difference(istr_type_evts).difference(istr_type_2d) != set()

    if has_events and not (has_1d or has_2d):
        return 'events'
    elif has_1d and not has_events:
        return '1d'
    elif has_2d and not (has_events or has_1d):
        return '2d'
    else:
        return None


def istr_best_2d_source(istr, avail_sources=None):
    if avail_sources is None:
        avail_sources = []
    for token in tokens(istr):
        s = token.split('#')[-1]
        if s.rstrip('0123456789') in istr_type_2d and s in avail_sources:
            return s
    for s in istr_type_2d:
        if s in avail_sources:
            return s
    return None


def token_source(token, avail_sources=None):
    prim_2d = None
    if avail_sources is None:
        avail_sources = []
    else:
        # find the "best" 2d trace available
        for s in istr_type_2d:
            if s in avail_sources:
                prim_2d = s
                break

    if token in avail_sources:
        if token.rstrip('0123456789') in istr_type_2d:
            return 'tic', token
        else:
            return token, token
    elif '#' in token:
        return token.rsplit('#', 1)
    elif token in {'tic', 'x', ''} and 'fid' in avail_sources:
        return token, 'fid'
    else:
        return token, prim_2d


def tokenize(istr, token):
    plevel, words, sacc = 0, [], ''
    for s in istr.split(token):
        plevel += sum(1 for i in s if i == '(')
        plevel -= sum(1 for i in s if i == ')')
        if sacc == '':
            sacc += s
        else:
            sacc += token + s
        if plevel == 0:
            words.append(sacc.strip())
            sacc = ''
    if sacc != '':
        words.append(sacc.strip())
    return words


def is_parans_exp(istr):
    """
    Determines if an expression is a valid function "call"
    """
    fxn = istr.split('(')[0]
    if (not fxn.isalnum() and fxn != '(') or istr[-1] != ')':
        return False
    plevel = 1
    for c in '('.join(istr[:-1].split('(')[1:]):
        if c == '(':
            plevel += 1
        elif c == ')':
            plevel -= 1
        if plevel == 0:
            return False
    return True


def trace_resolver(istr, analyses, twin=None):
    avail_sources = [i.lstrip('#*') for a in analyses
                     for i in a.trace.split(',')]
    istr, source = token_source(istr, avail_sources)
    if source is None:
        return Trace()

    for a in analyses:
        if source in [i.lstrip('#*') for i in a.trace.split(',')]:
            df = a.datafile
            break
    else:
        df = None

    if istr in {'coda', 'rnie', 'wmsm'}:
        # TODO: allow more complicated options to turn
        # Chromatograms into plotable Traces

        # coda
        #  Windig W: The use of the Durbin-Watson criterion for
        #  noise and background reduction of complex liquid
        #  chromatography/mass spectrometry data and a new algorithm
        #  to determine sample differences. Chemometrics and
        #  Intelligent Laboratory Systems. 2005, 77:206-214.

        # rnie
        #  Yunfei L, Qu H, and Cheng Y: A entropy-based method
        #  for noise reduction of LC-MS data. Analytica Chimica
        #  Acta 612.1 (2008)

        # wmsm
        #  Fleming C et al. Windowed mass selection method:
        #  a new data processing algorithm for LC-MS data.
        #  Journal of Chromatography A 849.1 (1999) 71-85.
        pass
    elif istr.startswith('m_'):
        if istr == 'm_':
            m = 0.0
        else:
            m = float(istr.split('_')[1])
        return mzminus(df.data, m)
    elif istr == 'molmz':
        return molmz(df.data)
    elif istr == 'basemz':
        return basemz(df.data)
    elif istr in {'r45std', 'r46std'}:
        # TODO: calculate isotopic data -> needs integrated peak
        # references of associated peaks in order to make these calculations
        pass
        #  calculate isotopic reference for chromatogram
        # if name == 'r45std':
        #     topion = 45
        # else:
        #     topion = 46
        # std_specs = [o for o in \
        #   self.children_of_type('peak') \
        #   if o.info['p-type'] == 'Isotope Standard']
        # x = [float(o.info['p-s-time']) for o in std_specs]
        # y = [o.area(topion) / o.area(44) for o in std_specs \
        #      if o.area(44) != 0]
        # if len(x) == 0 or len(y) == 0:
        #     return self._const(0.0, twin)

        # p0 = [y[0], 0]
        # errfunc = lambda p, x, y: p[0] + p[1] * x - y
        # try:
        #     p, succ = leastsq(errfunc, p0, args=(np.array(x), \
        #                                          np.array(y)))
        # except:
        #     p = p0
        # sim_y = np.array(errfunc(p, t, np.zeros(len(t))))
        # return TimeSeries(sim_y, t, [name])
    else:
        # interpret tolerances
        if ':' in istr:
            st = float(istr.split(':')[0])
            en = float(istr.split(':')[1])
            tol = 0.5 * (en - st)
            istr = 0.5 * (en + st)
        elif u'±' in istr:
            tol = float(istr.split(u'±')[1])
            istr = float(istr.split(u'±')[0])
        else:
            tol = 0.5

        return df.trace(istr, tol, twin=twin)


def fxn_resolver():
    # FIXME: not used properly (or at all)
    fxns = {
        'fft': fft,
        'noise': ts_func(noisefilter),
        'abs': ts_func(np.abs),
        'sin': ts_func(np.sin),
        'cos': ts_func(np.cos),
        'tan': ts_func(np.tan),
        'derivative': ts_func(np.gradient),
        'd': ts_func(np.gradient),
        'movingaverage': movingaverage,
        'savitzkygolay': savitzkygolay,
    }
    return fxns


def parse_ion_string(istr, analyses, twin=None):
    """
    Recursive string parser that handles "ion" strings.
    """

    if istr.strip() == '':
        return Trace()

    # remove (unnessary?) pluses from the front
    # TODO: plus should be abs?
    istr = istr.lstrip('+')

    # invert it if preceded by a minus sign
    if istr[0] == '-':
        return -parse_ion_string(istr[1:], analyses, twin)

    # this is a function or paranthesized expression
    if is_parans_exp(istr):
        if ')' not in istr:
            # unbalanced parantheses
            pass
        fxn = istr.split('(')[0]
        args = istr[istr.find('(') + 1:istr.find(')')].split(',')
        if fxn == '':
            # strip out the parantheses and continue
            istr = args[0]
        else:
            ts = parse_ion_string(args[0], analyses, twin)
            # FIXME
            return ts
            # return fxn_resolver(ts, fxn, *args[1:])

    # all the complicated math is gone, so simple lookup
    if set(istr).intersection(set('+-/*()')) == set():
        if istr in SHORTCUTS:
            # allow some shortcuts to pull out common ions
            return parse_ion_string(SHORTCUTS[istr], analyses, twin)
        elif istr[0] == '!' and all(i in '0123456789.' for i in istr[1:]):
            # TODO: should this handle negative numbers?
            return float(istr[1:])
        elif istr == '!pi':
            return np.pi
        elif istr == '!e':
            return np.e
        else:
            return trace_resolver(istr, analyses, twin)

    # go through and handle operators
    for token in '/*+-^':
        if len(tokenize(istr, token)) != 1:
            ts = tokenize(istr, token)
            s = parse_ion_string(ts[0], analyses, twin)
            for t in ts[1:]:
                if token == '/':
                    s /= parse_ion_string(t, analyses, twin)
                elif token == '*':
                    s *= parse_ion_string(t, analyses, twin)
                elif token == '+':
                    s += parse_ion_string(t, analyses, twin)
                elif token == '-':
                    s -= parse_ion_string(t, analyses, twin)
                elif token == '^':
                    s **= parse_ion_string(t, analyses, twin)
            return s
    raise Exception('Parser hit a point it shouldn\'t have!')
