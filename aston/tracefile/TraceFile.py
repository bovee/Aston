import numpy as np
from aston.trace.Trace import AstonSeries, AstonFrame
from aston.tracefile.Common import tfclasses, file_type


class TraceFile(object):
    fnm = None  # file name, if constant
    ext = None  # file extension, if constant
    mgc = None  # first two bytes of the file, if constant

    # traces is a list of possible traces:
    # each item may start with a * indicating a events
    # a # indicating a 2d trace or nothing indicating a single trace name
    traces = []

    def __init__(self, filename=None, ftype=None, data=None):
        self.filename = filename
        self.ftype = ''
        self._data = None

        # try to automatically change my class to reflect
        # whatever type of file I'm pointing at if not provided
        if type(self) is TraceFile:
            if data is not None:
                self._data = data

            if filename is None:
                return

            ftype = file_type(filename)

            if ftype is not None:
                # try to automatically subclass myself to provided type
                for cls in tfclasses():
                    if cls.__name__ == ftype:
                        self.__class__ = cls
                        self.ftype = ftype
        else:
            self.ftype = self.__class__.__name__

    @property
    def data(self):
        if self._data is not None:
            return self._data
        else:
            return AstonFrame()

    def total_trace(self, twin=None):
        return self.data.trace(twin=twin)

    #TODO: should this code be kept? (needs to be improved, if so)
    #def plot(self, name='', ax=None):
    #    if ax is None:
    #        import matplotlib.pyplot as plt
    #        ax = plt.gca()

    #    for t in self.traces:
    #        if t.startswith('#'):
    #            #self.trace(t[1:]).plot(ax=ax)
    #            self.trace('').plot(ax=ax)
    #        elif t.startswith('*'):
    #            #TODO: plot events
    #            pass
    #        else:
    #            self.trace(t).plot(ax=ax)

    #    #TODO: colors?
    #    #TODO: plot 2d/colors

    def trace(self, name='', tol=0.5, twin=None):
        if isinstance(name, (int, float, np.float32, np.float64)):
            name = str(name)
        else:
            name = name.lower()

        # name of the 2d trace, if it exists
        if any(t.startswith('#') for t in self.traces):
            t2d = [t[1:] for t in self.traces if t.startswith('#')][0]

            # clip out the starting 'MS' if present
            if name.startswith(t2d):
                name = name[len(t2d):]
        else:
            t2d = ''

        # this is the only string we handle; all others handled in subclasses
        if name in ['tic', 'x', '']:
            return self.total_trace(twin)
        elif name in self.traces:
            return self._trace(name, twin)
        elif t2d != '':
            # this file contains 2d data; find the trace in that
            return self.data.trace(name, tol, twin)
        else:
            return AstonSeries()

    def scan(self, t, dt=None, aggfunc=None):
        """
        Returns the spectrum from a specific time or range of times.
        """
        return self.data.scan(t, dt, aggfunc)

    @property
    def info(self):
        #TODO: add creation date and short name
        return {'filename': self.filename,
                'filetype': self.ftype}

    def events(self, name, twin=None):
        #TODO: check for '*' trace in self.traces
        return []

    def md5hash(self):
        #TODO: calculate md5hash of this file
        # to be used for determining if files in db are unique
        raise NotImplementedError
