import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
from matplotlib.path import Path
from matplotlib.transforms import offset_copy
from matplotlib.patches import PathPatch, Polygon
from PyQt4.QtCore import Qt, QCoreApplication
from aston.qtgui.PlotNavbar import AstonNavBar


class Plotter(object):
    def __init__(self, masterWindow, style=None, scheme=None):
        self.masterWindow = masterWindow
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
        #self.plt = tfig.add_subplot(111, frameon=False)
        self.plt = tfig.add_axes((0.05, 0.1, 0.9, 0.85), frame_on=False)
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

        self.highlight = None

        tr = lambda s: QCoreApplication.translate('', s)
        self._colors = {
            'hsv': tr('Rainbow'),
            'Accent': tr('Pastels'),
            'BrBG': tr('Brown-Bluegreen'),
            'RdBu': tr('Red-Blue'),
            'RdYlBu': tr('Red-Yellow-Blue'),
            'RdYlGn': tr('Red-Yellow-Green'),
            'RdBu': tr('Red-Blue'),
            'PiYG': tr('Pink-Yellow-Green'),
            'Spectral': tr('Spectral'),
            'spring': tr('Spring'),
            'summer': tr('Summer'),
            'autumn': tr('Autumn'),
            'winter': tr('Winter'),
            'cool': tr('Cool'),
            'copper': tr('Copper'),
            'jet': tr('Jet'),
            'Paired': tr('Paired'),
            'binary': tr('White-Black'),
            'gray': tr('Black-White')}
        self._styles = {
            'default': tr('Default'),
            'scaled': tr('Scaled'),
            'stacked': tr('Stacked'),
            'scaled stacked': tr('Scaled Stacked'),
            '2d': tr('2D')}
        self._linestyle = ['-', '--', ':', '-.']
        self.setColorScheme(scheme)
        self.setStyle(style)

    def setColorScheme(self, scheme=None):
        colors = dict((str(self._colors[k]), k) for k in self._colors)
        if scheme is None:
            scheme = self._colors['Spectral']
        self._color = plt.get_cmap(colors[str(scheme)])
        self._peakcolor = self._color(0, 1)
        return colors[str(scheme)]

    def availColors(self):
        l = [self._colors['Spectral']]
        l += [self._colors[c] for c in self._colors if c != 'Spectral']
        return l

    def setStyle(self, style=None):
        styles = dict((str(self._styles[k]), k) for k in self._styles)
        if style is None:
            self._style = 'default'
        else:
            self._style = styles[str(style)]
        return self._style

    def availStyles(self):
        l_ord = ['default', 'scaled', 'stacked', 'scaled stacked', '2d']
        return [self._styles[s] for s in l_ord]

    def plotData(self, traces, updateBounds=True):
        if not updateBounds:
            bnds = self.plt.get_xlim(), self.plt.get_ylim()

        # clean up anything on the graph already
        self.plt.cla()
        #if self.cb is not None:
        #    #TODO: make this not horrific!
        #    #the next two lines used to work?
        #    #self.plt.figure.delaxes(self.cb.ax)
        #    #self.cb = None
        #    tfig = self.plt.figure
        #    tfig.clf()
        #    self.plt = tfig.add_subplot(111, frameon=False)
        #    self.plt.xaxis.set_ticks_position('none')
        #    self.plt.yaxis.set_ticks_position('none')
        #    self.cb = None
        #self.plt.figure.subplots_adjust(left=0.05, right=0.95)
        #self.patches = {}

        #plot all of the datafiles
        if len(traces) == 0:
            self.canvas.draw()
            return
        #if '2d' in self._style:
        #    self._plot2D(datafiles[0])
        else:
            self._plot(traces)

        #update the view bounds in the navbar's history
        if updateBounds:
            self.navbar._views.clear()
            self.navbar._positions.clear()
            self.navbar.push_current()
        else:
            self.plt.set_xlim(bnds[0])
            self.plt.set_ylim(bnds[1])
            #if type(self.highlight) == Polygon:
            #    self.plt.add_patch(self.highlight)
            #elif self.highlight is not None:
            #    self.plt.add_line(self.highlight)

        # plot events on the bottom of the graph
        #evts = []
        #if self.masterWindow.ui.actionGraphFxnCollection.isChecked():
        #    evts += datafiles[0].events('fxn')
        #if self.masterWindow.ui.actionGraphFIA.isChecked():
        #    evts += datafiles[0].events('fia')
        #if self.masterWindow.ui.actionGraphIRMS.isChecked():
        #    evts += datafiles[0].events('refgas')
        #if self.masterWindow.ui.actionGraph_Peaks_Found.isChecked():
        #    dt = self.masterWindow.obj_tab.active_file()
        #    tss = dt.active_traces(n=0)
        #    pevts = self.masterWindow.find_peaks(tss, dt)
        #    for i, p in enumerate(pevts[0]):
        #        p[2]['name'] = 'P' + str(i + 1)
        #    evts += pevts[0]

        #if evts != []:
        #    # TODO: save the text and lines to delete later?
        #    # TODO: make this prettier

        #    trans = self.plt.get_xaxis_transform()
        #    transText = offset_copy(trans, fig=self.plt.figure, \
        #                            x=3, units='points')
        #    for ev in evts:
        #        t0, t1, ta = ev[0], ev[1], (ev[1] + ev[0]) / 2.
        #        self.plt.vlines(t1, 0, 0.1, color='0.75', transform=trans)
        #        self.plt.vlines(t0, 0, 0.1, transform=trans)
        #        self.plt.text(ta, 0, ev[2]['name'], \
        #                      ha='center', transform=transText)

        # draw the y axis as log
        if self.masterWindow.ui.actionGraphLogYAxis.isChecked():
            self.plt.set_yscale('log')

        #draw grid lines
        if self.masterWindow.ui.actionGraphGrid.isChecked():
            self.plt.grid(c='black', ls='-', alpha=0.05)

        #update the canvas
        self.canvas.draw()

    def _plot(self, traces):
        """
        Plots times series on the graph.
        """
        def desaturate(c, k=0):
            """
            Utility function to desaturate a color c by an amount k.
            """
            intensity = 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]
            return [intensity * k + i * (1 - k) for i in c]

        ## make up a factor to separate traces by
        #if 'stacked' in self._style:
        #    fts = datafiles[0].trace(datafiles[0].info['traces'].split(',')[0])
        #    sc_factor = (max(fts.data[:, 0]) - min(fts.data[:, 0])) / 5.

        ## count the number of traces that will be displayed
        #trs = sum(1 for x in datafiles for _ in x.info['traces'].split(','))
        #if trs < 6:
        #    alpha = 0.75 - trs * 0.1
        #else:
        #    alpha = 0.15

        for tnum, ts in enumerate(traces):
            ts.plot(self.plt)
        #        if 'scaled' in self._style:
        #            #TODO: fails at negative chromatograms
        #            trace -= min(trace)
        #            trace /= max(trace)
        #            trace *= 100
        #        if 'stacked' in self._style:
        #            trace += tnum * sc_factor
        #        # stretch out the color spectrum if there are under 7
        #        if trs > 7:
        #            c = self._color(int(tnum % 7) / 6.0, 1)
        #        elif trs == 1:
        #            c = self._color(0, 1)
        #        else:
        #            c = self._color(int(tnum % trs) / float(trs - 1), 1)
        #        ls = self._linestyle[int(np.floor((tnum % 28) / 7))]
        #        nm = dt.info['name'].strip('_') + ' ' + ts.ions[0]
        #        self.plt.plot(ts.times, trace, color=c, \
        #          ls=ls, lw=1.2, label=nm)
        #        tnum += 1

        #        # plot peaks
        #        for pk in dt.children_of_type('peak'):
        #            #TODO: there has to be a better way to handle if
        #            # the ion is a string or a float
        #            #TODO: allow user to auto subtract out baseline
        #            #if enabled, need to change Peak.contains too.
        #            if ts.ions[0] in pk.data.ions or \
        #              ts.ions[0] in [str(i) for i in pk.data.ions]:
        #                try:
        #                    ply = Path(pk.as_poly(float(ts.ions[0])))
        #                except:
        #                    ply = Path(pk.as_poly(ts.ions[0]))
        #                self.patches[pk.db_id] = PathPatch(ply, \
        #                  facecolor=desaturate(c, 0.2), alpha=alpha, lw=0)
        #                self.plt.add_patch(self.patches[pk.db_id])

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

        print(type(ext), type(grid), ext)
        img = self.plt.imshow(grid, origin='lower', aspect='auto', \
          extent=ext, cmap=self._color)
        if self.legend:
            self.cb = self.plt.figure.colorbar(img)

    def redraw(self):
        self.canvas.draw()

    def clear_highlight(self):
        #try to remove the line from the previous spectrum (if it exists)
        if self.highlight is not None:
            if self.highlight in self.plt.lines:
                self.plt.lines.remove(self.highlight)
            if self.highlight in self.plt.patches:
                self.plt.patches.remove(self.highlight)
            self.redraw()
        self.highlight = None

    def draw_highlight(self, x1, x2, color='black', linestyle='-'):
        """
        Draw the line that indicates where the spectrum came from.
        """
        self.clear_highlight()
        #draw a new line
        if x1 is None:
            self.highlight = None
        elif x1 == x2:
            self.highlight = self.plt.axvline(x1, color=color, ls=linestyle)
        else:
            self.highlight = self.plt.axvspan(x1, x2, alpha=0.25, color=color)
        #redraw the canvas
        self.canvas.draw()

    def draw_highlight_peak(self, pk, color='white'):
        coords = pk.as_poly().T
        self.highlight = self.plt.fill(coords[0], coords[1], \
                                       fc=color, alpha=0.5)[0]
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
