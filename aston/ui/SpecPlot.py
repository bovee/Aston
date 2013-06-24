import time
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt4 import NavigationToolbar2QT
#from matplotlib.ticker import AutoMinorLocator
from aston.spectra import Spectrum


class SpecPlotter(object):
    def __init__(self, masterWindow, style='default'):
        self.masterWindow = masterWindow
        self.style = style

        specArea = masterWindow.ui.specArea

        #create the canvas for spectral plotting
        bfig = Figure()
        bfig.set_facecolor('white')
        self.canvas = FigureCanvasQTAgg(bfig)
        specArea.addWidget(self.canvas)

        #TODO: next line is slowest in module
        self.plt = bfig.add_subplot(111, frameon=False)
        self.plt.xaxis.set_ticks_position('bottom')
        self.plt.yaxis.set_ticks_position('none')
        self.plt.xaxis.set_tick_params(which='both', direction='out')

        # create a hidden NavigationBar to handle panning/zooming
        self.navbar = NavigationToolbar2QT(self.canvas, None)
        self.ev_time = 0, None, None

        self.canvas.mpl_connect('button_press_event', self.mousedown)
        self.canvas.mpl_connect('button_release_event', self.mouseup)
        self.canvas.mpl_connect('scroll_event', self.mousescroll)

        self.mainscan = None
        self.prevscan = None
        self.libscans = []
        self.spec_time, self.pspec_time = '', ''

    def set_main_spec(self, scan, time):
        self.mainscan, self.prevscan = scan, self.mainscan
        self.spec_time, self.pspec_time = time, self.spec_time

    def plot(self):
        mwui = self.masterWindow.ui
        self.plt.cla()

        xmin, xmax = np.inf, -np.inf
        ymin, ymax = 0, -np.inf

        if mwui.actionSpecLibDisp.isChecked() and len(self.libscans) > 0:
            lbl = mwui.actionSpecLibLabel.isChecked()
            for scn in self.libscans:
                xmin, xmax = min(min(scn[0]), xmin), max(max(scn[0]), xmax)
                ymin, ymax = min(min(scn[1]), ymin), max(max(scn[1]), ymax)
                self.plot_spec(scn, 'blue', label=lbl)

        if mwui.actionSpecPrevDisp.isChecked() and self.prevscan is not None:
            scn = self.prevscan
            xmin, xmax = min(min(scn[0]), xmin), max(max(scn[0]), xmax)
            ymin, ymax = min(min(scn[1]), ymin), max(max(scn[1]), ymax)
            lbl = mwui.actionSpecPrevLabel.isChecked()
            self.plot_spec(scn, '0.7', label=lbl)

        if mwui.actionSpecMainDisp.isChecked() and self.mainscan is not None:
            scn = self.mainscan
            xmin, xmax = min(min(scn[0]), xmin), max(max(scn[0]), xmax)
            ymin, ymax = min(min(scn[1]), ymin), max(max(scn[1]), ymax)
            lbl = mwui.actionSpecMainLabel.isChecked()
            self.plot_spec(scn, 'black', label=lbl)

        # update the view bounds and save them for the navbar
        self.plt.set_xlim(xmin - 1, xmax + 1)
        self.plt.set_ylim(ymin, ymax)
        self.navbar._views.clear()
        self.navbar._positions.clear()
        self.navbar.push_current()

        # plot everything!
        self.canvas.draw()

    def plot_spec(self, scn, clr, label=False):
        if scn.shape[1] > 10 and np.all(np.abs(np.diff(scn[0]) - \
          (scn[0, 1] - scn[0, 0])) < 1e-9):
            #if the spacing between all the points is equal, plot as a line
            scn = scn[:, np.argsort(scn)[0]]
            self.plt.plot(scn[0], scn[1], '-', color=clr)
        else:
            try:
                #FIXME: this crashes on Windows unless the user has clicked on
                #the spectrum graph previously. Matplotlib bug needs workaround
                self.plt.vlines(scn[0], 0, scn[1], color=clr, alpha=0.5)
            except:
                pass
            self.plt.plot(scn[0], scn[1], ',', color=clr)

        if label:
            #go through the top 10% highest ions from highest to lowest
            #always have at least 10 labels, but no more than 50 (arbitrary)
            #if an ion is close to one seen previously, don't display it
            v2lbl = {}  # values to label
            plbl = []  # all values so far
            max_val = max(np.array(scn[1]))  # only label peaks X % of this
            for i in np.array(scn[1]).argsort()[::-1]:
                mz = scn[0][i]
                #don't allow a new label within 1.5 units of another
                if not np.any(np.abs(np.array(plbl) - mz) < 1.5) and \
                  scn[1][i] > 0.01 * max_val:
                    v2lbl[mz] = scn[1][i]
                plbl.append(mz)

            #add peak labels
            for v in v2lbl:
                self.plt.text(v, v2lbl[v], str(v), ha='center', \
                    va='bottom', rotation=90, size=10, color=clr)
                #self.plt.text(v, v2lbl[v], str(v), ha='center', \
                #    va='bottom', rotation=90, size=10, color=clr, \
                #    bbox={'boxstyle': 'larrow,pad=0.3', 'fc': clr, \
                #        'ec': clr, 'lw': 1, 'alpha': '0.25'})

    def mousedown(self, event):
        if event.button == 1:
            if self.ev_time[1] is not None and self.ev_time[2] is not None:
                if time.time() - self.ev_time[0] < 1 and \
                  np.abs(event.xdata - self.ev_time[1]) < 1 and \
                  np.abs(event.ydata - self.ev_time[2]) < 1:
                    self.navbar.home()
            self.navbar.press_zoom(event)
        elif event.button == 3:
            event.button = 1
            self.navbar.press_pan(event)

    def mouseup(self, event):
        if event.button == 1:
            self.navbar.release_zoom(event)
            self.ev_time = time.time(), event.xdata, event.ydata
        elif event.button == 3:
            event.button = 1
            self.navbar.release_pan(event)

    def mousescroll(self, event):
        xmin, xmax = self.plt.get_xlim()
        ymin, ymax = self.plt.get_ylim()
        if event.button == 'up':  # zoom in
            self.plt.set_xlim(event.xdata - (event.xdata - xmin) / 2., \
              event.xdata + (xmax - event.xdata) / 2.)
            self.plt.set_ylim(event.ydata - (event.ydata - ymin) / 2., \
              event.ydata + (ymax - event.ydata) / 2.)
        elif event.button == 'down':  # zoom out
            dlim = self.plt.dataLim.get_points()
            xmin = max(event.xdata - 2 * (event.xdata - xmin), dlim[0][0])
            xmax = min(event.xdata + 2 * (xmax - event.xdata), dlim[1][0])
            ymin = max(event.ydata - 2 * (event.ydata - ymin), dlim[0][1])
            ymax = min(event.ydata + 2 * (ymax - event.ydata), dlim[1][1])
            self.plt.axis([xmin, xmax, ymin, ymax])
        self.canvas.draw()

    def save_main_spec(self):
        dt = self.masterWindow.obj_tab.active_file()
        spc = Spectrum({'name': self.spec_time}, self.mainscan)
        dt.children += [spc]

    def save_prev_spec(self):
        dt = self.masterWindow.obj_tab.active_file()
        spc = Spectrum({'name': self.pspec_time}, self.prevscan)
        self.masterWindow.obj_tab.addObjects(dt, [spc])
