import math
import re
from aston.trace.Trace import AstonSeries

functions = {}  # TODO
istr_type_2d = ['ms', 'uv', 'irms']
istr_type_evts = ['refgas', 'fia', 'fxn', 'deadvol']

SHORTCUTS = {'alkanes': '57#ms+71#ms+85#ms',
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
             'pthalates': '149#ms'}


def tokens(istr):
    """
    Same as tokenize, but returns only tokens
    (and at all parantheses levels).
    """

    # make a list of all alphanumeric tokens
    toks = re.findall(r'[^\*\\\+\-\^\(\)]+\(?', istr)

    #remove the functions
    return [t for t in toks if not t.endswith('(')]


def istr_type(istr):
    """
    Given an "ion" specification, determine its "type", e.g. 1D, Events, etc.
    """
    data = set(tokens(istr))
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
        if s in istr_type_2d and s in avail_sources:
            return s
    else:
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
        return '', token
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


def parse_ion_string(istr, tr_resolver, twin=None):
    """
    Recursive string parser that handles "ion" strings.
    """

    if istr.strip() == '':
        return AstonSeries()

    #remove (unnessary?) pluses from the front
    #TODO: plus should be abs?
    istr = istr.lstrip('+')

    #invert it if preceded by a minus sign
    if istr[0] == '-':
        return -parse_ion_string(istr[1:], tr_resolver, twin)

    #this is a function or paranthesized expression
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
            ts = parse_ion_string(args[0], tr_resolver, twin)
            #FIXME
            return ts
            #return _apply_fxn(ts, fxn, *args[1:])

    # all the complicated math is gone, so simple lookup
    if set(istr).intersection(set('+-/*()')) == set():
        if istr in SHORTCUTS:
            # allow some shortcuts to pull out common ions
            return parse_ion_string(SHORTCUTS[istr], tr_resolver, twin)
        elif istr[0] == '!' and all(i in '0123456789.' for i in istr[1:]):
            #TODO: should this handle negative numbers?
            return float(istr[1:])
        elif istr == '!pi':
            return math.pi
        elif istr == '!e':
            return math.e
        else:
            return tr_resolver(istr, twin)

    # go through and handle operators
    for token in '/*+-^':
        if len(tokenize(istr, token)) != 1:
            ts = tokenize(istr, token)
            s = parse_ion_string(ts[0], tr_resolver, twin)
            for t in ts[1:]:
                if token == '/':
                    s /= parse_ion_string(t, tr_resolver, twin)
                elif token == '*':
                    s *= parse_ion_string(t, tr_resolver, twin)
                elif token == '+':
                    s += parse_ion_string(t, tr_resolver, twin)
                elif token == '-':
                    s -= parse_ion_string(t, tr_resolver, twin)
                elif token == '^':
                    s **= parse_ion_string(t, tr_resolver, twin)
            return s
    #TODO: shouldn't hit this point?
    pass
