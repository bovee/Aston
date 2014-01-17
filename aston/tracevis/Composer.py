import matplotlib.pyplot as plt
"""
Example:

"""


def plot(plotitems):
    for pi in plotitems:
        pass

    xaxis_name = 'Retention Time'
    xaxis_units = 'min'

    #options:

    # time-axis: x or y
    # color scheme
    # grid?
    # axis labelling?
    # log-scale
    # draw peak polygons
    # label peaks? with name, structure, etc

    # combine all series into "panels"?
    # how to combine series: by y-unit? series name?
    # turn dataframes into colors, 2d plots, or TICs?
    # allow different x-axis units
    # allow all series to be normalized to 100%
    # draw time events over all panels?
    pass


class PlotItem(object):
    def __init__(self, x=None, y=None):
        self.x = x
        self.y = y

        self.y_units = ''

    def plot_xy(self):
        #TODO: how to pass colors in here?
        # or just output x/y?
        pass

    def plot_peaks(self):
        pass

    def plot_strip(self):
        # plot colors strips
        # or plot lines representing events
        pass

    def plot_2d(self):
        #TODO: colorscheme?
        #TODO: allow single shade with transparency (to allow RGB stacking)
        pass
