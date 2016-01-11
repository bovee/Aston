from matplotlib.figure import Figure
from matplotlib.pyplot import get_cmap
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from aston.qtgui.PlotNavbar import AstonNavBar


class Plotter(object):
    def __init__(self, masterWindow, style=None, scheme=None):
        self.masterWindow = masterWindow
        self.legend = False

        plotArea = masterWindow.ui.plotArea

        # create the plotting canvas and its toolbar and add them
        tfig = Figure()
        tfig.set_facecolor('white')
        self.canvas = FigureCanvasQTAgg(tfig)
        self.canvas.setMinimumSize(50, 100)
        self.canvas.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                  QtWidgets.QSizePolicy.Expanding)
        self.navbar = AstonNavBar(self.canvas, masterWindow)
        plotArea.addWidget(self.navbar)
        plotArea.addWidget(self.canvas)

        self.plt = tfig.add_axes((0.05, 0.1, 0.9, 0.85), frame_on=False)
        self.plt.axes.hold(False)
        self.plt.xaxis.set_ticks_position('none')
        self.plt.yaxis.set_ticks_position('none')
        self.patches = []
        self.cb = None

        # TODO: find a way to make the axes fill the figure properly
        # tfig.subplots_adjust(left=0.05, right=0.95, bottom=0.05, top=0.95)
        # tfig.tight_layout(pad=2)

        self.canvas.setFocusPolicy(Qt.ClickFocus)
        self.canvas.mpl_connect('button_press_event', self.mousedown)
        self.canvas.mpl_connect('button_release_event', self.mouseup)
        self.canvas.mpl_connect('scroll_event', self.mousescroll)

        self.highlight = None

    def plot_data(self, plots, update_bounds=True):
        if not update_bounds:
            bnds = self.plt.get_xlim(), self.plt.get_ylim()

        # clean up anything on the graph already
        self.plt.cla()
        if self.cb is not None:
            #TODO: this should work? need way to update size of mappable axes
            #self.plt.figure.delaxes(self.cb.ax)
            #self.cb.mappable.axes.autoscale()
            #self.cb = None
            #the next two lines used to work?
            self.plt.figure.delaxes(self.cb.ax)
            self.cb = None
            tfig = self.plt.figure
            tfig.clf()
            self.plt = tfig.add_subplot(111, frameon=False)
            self.plt.xaxis.set_ticks_position('none')
            self.plt.yaxis.set_ticks_position('none')
            self.cb = None
        self.plt.figure.subplots_adjust(left=0.05, right=0.95)
        self.patches = []

        #plot all of the datafiles
        if len(plots) == 0:
            self.canvas.draw()
            return

        ## make up a factor to separate plots by
        #if 'stacked' in self._style:
        #    fts = datafils[0].trace(datafiles[0].info['traces'].split(',')[0])
        #    sc_factor = (max(fts.data[:, 0]) - min(fts.data[:, 0])) / 5.

        ## count the number of traces that will be displayed
        nplots = len(plots)
        if nplots < 6:
            alpha = 0.75 - nplots * 0.1
        else:
            alpha = 0.15
        #FIXME: read this from the menu
        colors = get_cmap('Spectral')

        #TODO: do scaling/scaling with offset/etc?
        #TODO: determine the number of axes to use
        #TODO: should be filtering out invalid plots before here
        for pnum, plot in enumerate(plots):
            style = plot.style
            if plot.color == 'auto':
                if style in {'heatmap', 'colors'}:
                    c = colors
                elif nplots > 7:
                    c = colors(int(pnum % 7) / 6.0, 1)
                elif nplots == 1:
                    c = colors(0, 1)
                else:
                    c = colors(int(pnum % nplots) / float(nplots - 1), 1)
            else:
                c = plot.color

            if style == 'heatmap':
                plot.plot(style=style, color=c, ax=self.plt)
                if self.legend:
                    self.cb = self.plt.figure.colorbar(self.plt.images[0])
            elif style == 'colors':
                plot.plot(style=style, color=c, ax=self.plt)
            else:
                plot.plot(style=style, color=c, ax=self.plt)

                # plot the peaks
                for pk in plot.peaks:
                    if pk.color == 'auto':
                        pc = c
                    else:
                        pc = pk.color

                    if pk.vis:
                        pk_pa = pk.plot(ax=self.plt, color=pc, alpha=alpha)
                        self.patches.append(pk_pa)

                #add a legend and make it pretty
                if self.legend:
                    leg = self.plt.legend(frameon=False)
                    clrs = [i.get_color() for i in leg.get_lines()]
                    for i, j in enumerate(clrs):
                        leg.get_texts()[i].set_color(j)
                    for i in leg.get_lines():
                        i.set_linestyle('')

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

            ## for heatmap plots
            #if self.legend:
            #    self.cb = self.plt.figure.colorbar(img)

        #update the view bounds in the navbar's history
        if update_bounds:
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
        #    tss = dt.active_plots(n=0)
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
