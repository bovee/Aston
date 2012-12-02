import numpy as np
from aston.ui.Navbar import AstonNavBar
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
from matplotlib.path import Path
import matplotlib.patches as patches
import matplotlib.pyplot as plt
from PyQt4.QtCore import Qt


class Plotter(object):
    def __init__(self, masterWindow, style='default', scheme='Spectral'):
        self.masterWindow = masterWindow
        self.style = style
        self.legend = False

        plotArea = masterWindow.ui.plotArea

        #create the plotting canvas and its toolbar and add them
        tfig = Figure()
        tfig.set_facecolor('white')
        self.canvas = FigureCanvasQTAgg(tfig)
        self.navbar = AstonNavBar(self.canvas, masterWindow)
        plotArea.addWidget(self.navbar)
        plotArea.addWidget(self.canvas)

        #TODO this next line is the slowest in this module
        self.plt = tfig.add_subplot(111, frameon=False)
        self.plt.xaxis.set_ticks_position('none')
        self.plt.yaxis.set_ticks_position('none')
        self.cb = None

        #TODO: find a way to make the axes fill the figure properly
        #tfig.subplots_adjust(left=0.05, right=0.95, bottom=0.05, top=0.95)
        #tfig.tight_layout(pad=2)

        self.canvas.setFocusPolicy(Qt.ClickFocus)
        self.canvas.mpl_connect('button_press_event', self.mousedown)
        self.canvas.mpl_connect('button_release_event', self.mouseup)
        self.canvas.mpl_connect('scroll_event', self.mousescroll)

        self.spec_line = None
        self.patches = {}

        self._colors = {
            'Rainbow': 'hsv',
            'Pastels': 'Accent',
            'Brown-Bluegreen': 'BrBG',
            'Red-Blue': 'RdBu',
            'Red-Yellow-Blue': 'RdYlBu',
            'Red-Yellow-Green': 'RdYlGn',
            'Red-Blue': 'RdBu',
            'Pink-Yellow-Green': 'PiYG',
            'Spectral': 'Spectral',
            'Spring': 'spring',
            'Summer': 'summer',
            'Autumn': 'autumn',
            'Winter': 'winter',
            'Cool': 'cool',
            'Copper': 'copper',
            'Jet': 'jet',
            'Paired': 'Paired',
            'White-Black': 'binary',
            'Black-White': 'gray'
            }
        self._linestyle = ['-', '--', ':', '-.']
        self.setColorScheme(scheme)

    def setColorScheme(self, scheme='Spectral'):
        self._color = plt.get_cmap(self._colors[str(scheme)])
        self._peakcolor = self._color(0, 1)

    def availColors(self):
        return list(self._colors.keys())

    def availStyles(self):
        return ['Default', 'Scaled', 'Stacked', 'Scaled Stacked', '2D']

    def plotData(self, datafiles, updateBounds=True):
        if not updateBounds:
            bnds = self.plt.get_xlim(), self.plt.get_ylim()

        # clean up anything on the graph already
        self.plt.cla()
        if self.cb is not None:
            #TODO: make this not horrific!
            #the next two lines used to work?
            #self.plt.figure.delaxes(self.cb.ax)
            #self.cb = None
            tfig = self.plt.figure
            tfig.clf()
            self.plt = tfig.add_subplot(111, frameon=False)
            self.plt.xaxis.set_ticks_position('none')
            self.plt.yaxis.set_ticks_position('none')
            self.cb = None
        self.plt.figure.subplots_adjust(left=0.05, right=0.95)
        self.pk_clr_idx = {}

        #plot all of the datafiles
        if len(datafiles) == 0:
            return
        if '2d' in self.style:
            self._plot2D(datafiles[0])
        else:
            self._plot(datafiles)

        #update the view bounds in the navbar's history
        if updateBounds:
            self.navbar._views.clear()
            self.navbar._positions.clear()
            self.navbar.push_current()
        else:
            self.plt.set_xlim(bnds[0])
            self.plt.set_ylim(bnds[1])

        #draw grid lines
        self.plt.grid(c='black', ls='-', alpha='0.05')

        #update the canvas
        self.canvas.draw()

    def _plot(self, datafiles):
        """
        Plots times series on the graph.
        """

        # make up a factor to separate traces by
        if 'stacked' in self.style:
            fts = datafiles[0].trace(datafiles[0].info['traces'].split(',')[0])
            sc_factor = (max(fts.data[:, 0]) - min(fts.data[:, 0])) / 5.

        # count the number of traces that will be displayed
        trs = sum(1 for x in datafiles for _ in x.info['traces'].split(','))
        if trs < 6:
            alpha = 0.75 - trs * 0.1
        else:
            alpha = 0.15

        tnum = 0
        for dt in datafiles:
            for y in dt.info['traces'].split(','):
                ts = dt.trace(y.strip())
                trace = ts.data
                if 'scaled' in self.style:
                    trace -= min(trace)
                    trace /= max(trace)
                    trace *= 100
                if 'stacked' in self.style:
                    trace += tnum * sc_factor
                # stretch out the color spectrum if there are under 7
                if trs > 7:
                    c = self._color(int(tnum % 7) / 6.0, 1)
                elif trs == 1:
                    c = self._color(0, 1)
                else:
                    c = self._color(int(tnum % trs) / float(trs - 1), 1)
                ls = self._linestyle[int(np.floor((tnum % 28) / 7))]
                nm = dt.info['name'].strip('_') + ' ' + y
                self.plt.plot(ts.times, trace, color=c, \
                  ls=ls, lw=1.2, label=nm)
                tnum += 1
            self.pk_clr_idx[dt.db_id] = (c, alpha)

        #add a legend and make it pretty
        if self.legend:
            leg = self.plt.legend(frameon=False)
            clrs = [i.get_color() for i in leg.get_lines()]
            for i, j in enumerate(clrs):
                leg.get_texts()[i].set_color(j)
            for i in leg.get_lines():
                i.set_linestyle('')

    def _plot2D(self, dt):
        if dt.data is None:
            dt._cache_data()

        ext, grid = dt.as_2D()

        img = self.plt.imshow(grid, origin='lower', aspect='auto', \
          extent=ext, cmap=self._color)
        if self.legend:
            self.cb = self.plt.figure.colorbar(img)

    def redraw(self):
        self.canvas.draw()

    def draw_spec_line(self, x1, x2, color='black', linestyle='-'):
        """
        Draw the line that indicates where the spectrum came from.
        """
        #try to remove the line from the previous spectrum (if it exists)
        if self.spec_line is not None:
            if self.spec_line in self.plt.lines:
                self.plt.lines.remove(self.spec_line)
            if self.spec_line in self.plt.patches:
                self.plt.patches.remove(self.spec_line)
        #draw a new line
        if x1 is None:
            self.spec_line = None
        elif x1 == x2:
            self.spec_line = self.plt.axvline(x1, color=color, ls=linestyle)
        else:
            self.spec_line = self.plt.axvspan(x1, x2, alpha=0.25, color=color)
        #redraw the canvas
        self.canvas.draw()

    def mousedown(self, event):
        if event.button == 3 and self.navbar.mode in ['peak', 'spectrum']:
            event.button = 1
            self.navbar.mode += '_pan'
            self.navbar.press_pan(event)

    def mouseup(self, event):
        if event.button == 3 and self.navbar.mode[-4:] == '_pan':
            event.button = 1
            self.navbar.release_pan(event)
            self.navbar.mode = self.navbar.mode[:-4]

    def mousescroll(self, event):
        if event.xdata is None or event.ydata is None:
            return
        xmin, xmax = self.plt.get_xlim()
        ymin, ymax = self.plt.get_ylim()
        if event.button == 'up':  # zoom in
            self.plt.set_xlim(event.xdata - (event.xdata - xmin) / 2.,
              event.xdata + (xmax - event.xdata) / 2.)
            self.plt.set_ylim(event.ydata - (event.ydata - ymin) / 2.,
              event.ydata + (ymax - event.ydata) / 2.)
        elif event.button == 'down':  # zoom out
            xmin = event.xdata - 2 * (event.xdata - xmin)
            xmax = event.xdata + 2 * (xmax - event.xdata)
            xmin = max(xmin, self.navbar._views.home()[0][0])
            xmax = min(xmax, self.navbar._views.home()[0][1])
            ymin = event.ydata - 2 * (event.ydata - ymin)
            ymax = event.ydata + 2 * (ymax - event.ydata)
            ymin = max(ymin, self.navbar._views.home()[0][2])
            ymax = min(ymax, self.navbar._views.home()[0][3])
            self.plt.axis([xmin, xmax, ymin, ymax])
        self.redraw()

    def clear_peaks(self):
        self.plt.patches = []
        self.patches = {}
        self.redraw()

    def remove_peaks(self, pks):
        for pk in pks:
            if pk.db_type == 'peak':
                if pk.db_id in self.patches:
                    patch = self.patches[pk.db_id]
                    self.plt.patches.remove(patch)
        self.redraw()

    def add_peaks(self, pks):
        def desaturate(c, k=0):
            """
            Utility function to desaturate a color c by an amount k.
            """
            intensity = 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]
            return [intensity * k + i * (1 - k) for i in c]

        for pk in pks:
            if pk.db_type == 'peak':
                fid = pk.getParentOfType('file').db_id
                c, a = self.pk_clr_idx[fid]

                self.patches[pk.db_id] = patches.PathPatch(Path(pk.as_poly()), \
                  facecolor=desaturate(c, 0.2), alpha=a, lw=0)
                self.plt.add_patch(self.patches[pk.db_id])
        self.redraw()
