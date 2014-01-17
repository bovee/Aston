import numpy as np
from pandas import Series


def _apply_f(f, s, s2):
    """
    Convenience function for all of the math stuff.
    """
    if type(s2) == int or type(s2) == float:
        # s2 is a number, so make an array of the same size
        # with just that number in it
        d = s2 * np.ones(s.index.shape)
    elif s2 is None:
        d = None
    elif all(s2.index == s.index):
        # same times, so can do math directly
        d = s2.data
    else:
        # retime s2 so it matches up with s
        d = _retime(s2, s.index)
        # TODO: needs to be smarter with retiming, so
        #nonoverlapping times don't break this

    new_data = np.apply_along_axis(f, 0, s.values, d)
    return Series(new_data, s.index, s.columns)


def add(s1, s2):
    return _apply_f(lambda x, y: x + y, s1, s2)


def sub(s1, s2):
    return _apply_f(lambda x, y: x - y, s1, s2)


def mul(s1, s2):
    return _apply_f(lambda x, y: x * y, s1, s2)


def div(s1, s2):
    return _apply_f(lambda x, y: x / y, s1, s2)


#def and(s1, s2):
#    pass


def _retime(s, new_times, fill=0.0):
    from scipy.interpolate import interp1d
    if new_times.shape == s.index.shape:
        if np.all(np.equal(new_times, s.index)):
            return s
    f = lambda d: interp1d(s.index, d, \
        bounds_error=False, fill_value=fill)(new_times)
    return np.apply_along_axis(f, 0, s.values)


def retime(s, new_times):
    return Series(_retime(s), new_times, name=s.name)


def adjust_time(s, offset=0.0, scale=1.0):
    adj_s = s.copy()
    adj_s.index = adj_s.index * scale + offset
    return adj_s


def as_text(s, width=80, height=20):
    raise NotImplementedError
    #break s.index into width chunks
    #find max and min of each chunk along with start and stop?


def dump(df):
    pass


def load(df_str):
    pass
