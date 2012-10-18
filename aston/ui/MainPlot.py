import numpy as np
import scipy.interpolate
import scipy.sparse
from aston.ui.Navbar import AstonNavBar
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
from matplotlib.path import Path
import matplotlib.patches as patches
import matplotlib.pyplot as plt


class Plotter(object):
    def __init__(self, masterWindow, style='default', scheme='Spectral'):
        self.masterWindow = masterWindow
        self.style = style

        plotArea = masterWindow.ui.plotArea

        #create the plotting canvas and its toolbar and add them
        tfig = Figure()
        tfig.set_facecolor('white')
        self.canvas = FigureCanvasQTAgg(tfig)
        self.navbar = AstonNavBar(self.canvas, masterWindow)
        plotArea.addWidget(self.navbar)
        plotArea.addWidget(self.canvas)

        self.plt = tfig.add_subplot(111, frameon=False)
        self.plt.xaxis.set_ticks_position('none')
        self.plt.yaxis.set_ticks_position('none')
        self.cb = None

        #TODO: find a way to make the axes fill the figure properly
        #tfig.subplots_adjust(left=0.05, right=0.95, bottom=0.05, top=0.95)
        tfig.tight_layout(pad=2)

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
            'Paired': 'Paired'
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
            self.plt.figure.delaxes(self.cb.ax)
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
        Plots 2D times series on the graph.
        """

        # make up a factor to separate traces by
        if 'stacked' in self.style:
            ftrace = datafiles[0].trace(datafiles[0].getInfo('traces').split(',')[0])
            sc_factor = (max(ftrace) - min(ftrace)) / 5.

        # count the number of traces that will be displayed
        ts = sum(1 for x in datafiles for _ in x.getInfo('traces').split(','))
        if ts < 6:
            alpha = 0.75 - ts * 0.1
        else:
            alpha = 0.15

        tnum = 0
        for dt in datafiles:
            for y in dt.getInfo('traces').split(','):
                trace = dt.trace(y.strip())
                if 'scaled' in self.style:
                    trace -= min(trace)
                    trace /= max(trace)
                    trace *= 100
                if 'stacked' in self.style:
                    trace += tnum * sc_factor
                # stretch out the color spectrum if there are under 7
                if ts > 7:
                    c = self._color(int(tnum % 7) / 6.0, 1)
                elif ts == 1:
                    c = self._color(0, 1)
                else:
                    c = self._color(int(tnum % ts) / float(ts - 1), 1)
                ls = self._linestyle[int(np.floor((tnum % 28) / 7))]
                nm = dt.getInfo('name') + ' ' + y
                self.plt.plot(dt.time(), trace, color=c, ls=ls, lw=1.2, label=nm)
                tnum += 1
            self.pk_clr_idx[dt.db_id] = (c, alpha)

        #add a legend and make it pretty
        if 'legend' in self.style:
            leg = self.plt.legend(frameon=False)
            #leg.get_frame().edgecolor = None
            clrs = [i.get_color() for i in leg.get_lines()]
            for i, j in enumerate(clrs):
                leg.get_texts()[i].set_color(j)
            for i in leg.get_lines():
                i.set_linestyle('')

    def _plot2D(self, dt):
        if dt.data is None:
            dt._cacheData()

        ext = (dt.data[0, 0], dt.data[-1, 0], min(dt.ions), max(dt.ions))
        if type(dt.data) is np.ndarray:
            grid = dt.data[:, [0] + list(np.argsort(dt.ions) + 1)].transpose()
        else:
            data = dt.data[:, 1:].tocoo()
            data_ions = np.array([dt.ions[i] for i in data.col])
            grid = scipy.sparse.coo_matrix((data.data, (data_ions, data.row))).toarray()

        img = self.plt.imshow(grid, origin='lower', aspect='auto', \
          extent=ext, cmap=self._color)
        if 'legend' in self.style:
            self.cb = self.plt.figure.colorbar(img)

    def redraw(self):
        self.canvas.draw()

    def drawSpecLine(self, x, color='black', linestyle='-'):
        """
        Draw the line that indicates where the spectrum came from.
        """
        #try to remove the line from the previous spectrum (if it exists)
        if self.spec_line is not None:
            try:
                self.plt.lines.remove(self.spec_line)
            except ValueError:
                pass  # not sure why this happens?
        #draw a new line
        if x is not None:
            self.spec_line = self.plt.axvline(x, color=color, ls=linestyle)
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

                self.patches[pk.db_id] = patches.PathPatch(Path(pk.data), \
                  facecolor=desaturate(c, 0.2), alpha=a, lw=0)
                self.plt.add_patch(self.patches[pk.db_id])
        self.redraw()
