import numpy as np
from PyQt4 import QtCore, QtGui
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
from matplotlib.ticker import AutoMinorLocator
from aston.Features import Spectrum


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

        self.plt = bfig.add_subplot(111, frameon=False)
        self.plt.xaxis.set_ticks_position('bottom')
        self.plt.yaxis.set_ticks_position('none')
        self.plt.xaxis.set_tick_params(which='both', direction='out')

        self.canvas.mpl_connect('button_press_event', self.specmousedown)
        self.canvas.mpl_connect('scroll_event', self.specmousescroll)

        self.scans = {}
        self.scansToDisp = []
        self.scansToLbl = ['']
        self.specTime = None

    def addSpec(self, scan, label=''):
        #save into scans dictionary
        if label is '' and '' in self.scans:
            self.scans['prev'] = self.scans['']
        self.scans[label] = scan
        if label not in self.scansToDisp:
            self.scansToDisp.append(label)

    def plotSpec(self):
        #plot it in the area below
        self.plt.cla()

        #colors
        clrs = {'': 'black', 'prev': '0.7', 'lib': 'blue'}
        xmin, xmax = np.inf, -np.inf
        ymin, ymax = 0, -np.inf

        #loop through all of the scans to be displayed
        for scn_nm in self.scansToDisp:
            scn = self.scans[scn_nm]

            xmin = min(min(scn[0]), xmin)
            xmax = max(max(scn[0]), xmax)
            ymin = min(min(scn[1]), ymin)
            ymax = max(max(scn[1]), ymax)

            try:
                clr = clrs[scn_nm]
            except:
                clr = 'black'

            #add the spectral lines (and little points!)
            if scn.shape[1] > 10 and np.all(np.diff(scn[0]) - \
              (scn[0, 1] - scn[0, 0]) < 1e-9):
                #if the spacing between all the points is equal, plot as a line
                self.plt.plot(scn[0], scn[1], '-', color=clr)
            else:
                try:
                    #FIXME: this crashes on Windows unless the user has clicked on
                    #the spectrum graph previously. Matplotlib bug, needs workaround
                    self.plt.vlines(scn[0], 0, scn[1], color=clr, alpha=0.5)
                except:
                    pass
                self.plt.plot(scn[0], scn[1], ',', color=clr)
#            self.plt.set_ylim(bottom=0)

            if scn_nm in self.scansToLbl:
                #go through the top 10% highest ions from highest to lowest
                #always have at least 10 labels, but no more than 50 (arbitrary)
                #if an ion is close to one seen previously, don't display it
                v2lbl = {}  # values to label
                plbl = []  # skip labeling these values
                #number of labels
                nls = -1 * min(max(int(len(scn) / 10.0), 10), 50)
                for i in np.array(scn[1]).argsort()[:nls:-1]:
                    mz = scn[0][i]
                    #don't allow a new label within 1.5 units of another
                    if not np.any(np.abs(np.array(plbl) - mz) < 1.5):
                        v2lbl[mz] = scn[1][i]
                    plbl.append(mz)

                #add peak labels
                for v in v2lbl:
                    self.plt.text(v, v2lbl[v], str(v), ha='center', \
                      va='bottom', rotation=90, size=10, color=clr, \
                      bbox={'boxstyle': 'larrow,pad=0.3', 'fc': clr, \
                            'ec': clr, 'lw': 1, 'alpha': '0.25'})

        #redraw the canvas
        self.plt.set_xlim(xmin - 1, xmax + 1)
        self.plt.set_ylim(ymin, ymax)
        self.canvas.draw()

    def specmousedown(self, event):
        if event.button == 1:
            dlim = self.plt.dataLim.get_points()
            self.plt.axis([dlim[0][0], dlim[1][0], dlim[0][1], dlim[1][1]])
            self.canvas.draw()
        elif event.button == 3:
            #TODO: make the spec window work better
            menu = QtGui.QMenu(self.canvas)
            for i in self.scans:
                if i == '':
                    ac = menu.addAction('current')
                else:
                    ac = menu.addAction(i)
                submenu = QtGui.QMenu(menu)
                sac = submenu.addAction('Display', self.togSpc)
                sac.setCheckable(True)
                sac.setChecked(i in self.scansToDisp)
                sac.setData(i)
                sac = submenu.addAction('Label', self.spcLbl)
                sac.setCheckable(True)
                sac.setChecked(i in self.scansToLbl)
                sac.setData(i)
                sac = submenu.addAction('Save', self.saveSpc)
                sac.setData(i)
                ac.setMenu(submenu)

            if not menu.isEmpty():
                menu.exec_(self.canvas.mapToGlobal(
                  QtCore.QPoint(event.x, self.canvas.height() - event.y)))

    def togSpc(self):
        scn_nm = str(self.masterWindow.sender().data())
        if scn_nm in self.scansToDisp:
            self.scansToDisp.remove(scn_nm)
        else:
            self.scansToDisp.append(scn_nm)
        self.plotSpec()

    def spcLbl(self):
        scn_nm = str(self.masterWindow.sender().data())
        if scn_nm in self.scansToLbl:
            self.scansToLbl.remove(scn_nm)
        else:
            self.scansToLbl.append(scn_nm)
        self.plotSpec()

    def saveSpc(self):
        #TODO: better metadata on spectra
        scn_nm = str(self.masterWindow.sender().data())
        scn = self.scans[scn_nm]
        dt = self.masterWindow.obj_tab.returnSelFile()
        info = {'name': scn_nm}
        if dt is None:
            spc = Spectrum(self.masterWindow.obj_tab.db, \
                           None, None, info, scn)
        else:
            spc = Spectrum(dt.db, None, dt.db_id, info, scn)
        self.masterWindow.obj_tab.addObjects(dt, [spc])

    def specmousescroll(self, event):
        xmin, xmax = self.plt.get_xlim()
        ymin, ymax = self.plt.get_ylim()
        if event.button == 'up':  # zoom in
            self.plt.set_xlim(event.xdata - (event.xdata - xmin) / 2., \
              event.xdata + (xmax - event.xdata) / 2.)
            self.plt.set_ylim(event.ydata - (event.ydata - ymin) / 2., \
              event.ydata + (ymax - event.ydata) / 2.)
        elif event.button == 'down': #zoom out
            dlim = self.plt.dataLim.get_points()
            xmin = max(event.xdata - 2 * (event.xdata - xmin), dlim[0][0])
            xmax = min(event.xdata + 2 * (xmax - event.xdata), dlim[1][0])
            ymin = max(event.ydata - 2 * (event.ydata - ymin), dlim[0][1])
            ymax = min(event.ydata + 2 * (ymax - event.ydata), dlim[1][1])
            self.plt.axis([xmin, xmax, ymin, ymax])
        self.canvas.draw()
