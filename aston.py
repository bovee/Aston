#!/usr/bin/python2.7

#for compatibility with Python 2
import sip
sip.setapi('QVariant', 2)

from PyQt4 import QtCore, QtGui
from matplotlib.figure import Figure

class AstonWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        from aston.ui.aston_ui import Ui_MainWindow
        from aston.FileTable import FileTreeModel

        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        #set up the grouping for the dock widgets
        self.tabifyDockWidget(self.ui.filesDockWidget,self.ui.settingsDockWidget)
        self.tabifyDockWidget(self.ui.filesDockWidget,self.ui.peaksDockWidget)
        self.tabifyDockWidget(self.ui.filesDockWidget,self.ui.spectraDockWidget)
        self.ui.filesDockWidget.raise_()

        #connect the menu logic
        self.ui.actionOpen.triggered.connect(self.openFolder)
        self.ui.actionPeak_List_as_CSV.triggered.connect(self.peakListAsCSV)
        self.ui.actionCalculate_Info.triggered.connect(self.calculateInfo)
        self.ui.actionChromatogram_as_Picture.triggered.connect(self.chromatogramAsPic)
        self.ui.actionChromatogram_as_CSV.triggered.connect(self.chromatogramAsCSV)
        self.ui.actionSpectra_as_Picture.triggered.connect(self.spectrumAsPic)
        self.ui.actionSpectra_as_CSV.triggered.connect(self.spectrumAsCSV)
        #self.ui.actionQuit.triggered.connect(QtCore.SLOT('quit()'), QtGui.qApp)
        self.ui.actionIntegrate.triggered.connect(self.quickIntegrate)
        #self.connect(self.ui.actionIntegration_Parameters, QtCore.SIGNAL('triggered()'), self.calculateInfo)
        #self.connect(self.ui.actionIntegrate_2, QtCore.SIGNAL('triggered()'), self.calculateInfo)
        #self.connect(self.ui.actionSearch_Database, QtCore.SIGNAL('triggered()'), self.calculateInfo)
        #self.connect(self.ui.actionSave_to_Database, QtCore.SIGNAL('triggered()'), self.calculateInfo)
        #self.connect(self.ui.actionSequence, QtCore.SIGNAL('triggered()'), self.calculateInfo)
        #self.connect(self.ui.actionStructure, QtCore.SIGNAL('triggered()'), self.calculateInfo)
        #self.connect(self.ui.actionAuto_align_Chromatogram, QtCore.SIGNAL('triggered()'), self.calculateInfo)
        self.ui.actionAlign_Chromatogram.triggered.connect(self.alignChrom)
        #self.connect(self.ui.actionSubtract_Add_Chromatogram, QtCore.SIGNAL('triggered()'), self.calculateInfo)
        self.ui.actionSmoothChromatogram.triggered.connect(self.smooth)
        self.ui.actionRemove_Periodic_Noise.triggered.connect(self.removePeriodicNoise)
        self.ui.actionRevert.triggered.connect(self.revertChromChange)
        self.connect(self.ui.actionQuit, QtCore.SIGNAL('triggered()'), QtGui.qApp, QtCore.SLOT('quit()'))

        #hook up the windows to the menu
        self.ui.actionFiles.triggered.connect(self.updateWindows)
        self.ui.actionSettings.triggered.connect(self.updateWindows)
        self.ui.actionPeaks.triggered.connect(self.updateWindows)
        self.ui.actionSpectra.triggered.connect(self.updateWindows)

        self.ui.filesDockWidget.visibilityChanged.connect(self.updateWindowsMenu)
        self.ui.settingsDockWidget.visibilityChanged.connect(self.updateWindowsMenu)
        self.ui.peaksDockWidget.visibilityChanged.connect(self.updateWindowsMenu)
        self.ui.spectraDockWidget.visibilityChanged.connect(self.updateWindowsMenu)

        #hook up the search box
        self.ui.lineEdit.textChanged.connect(self.updateSearch)

        #set up plots
        self.create_plots()

        #set up the list of files in the current directory
        self.directory = '.'
        self.ptab_mod = None
        self.ftab_mod = FileTreeModel(self.directory,self.ui.fileTreeView,self)

    def create_plots(self):
        #FIXME: resizing bug obliterates controls underneath the tcanvas
        from aston.ui.navbar import AstonNavBar
        from aston.Plotting import Plotter
        from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
        
        try:
            self.ui.plotArea.removeWidget(self.tnavbar)
            self.ui.plotArea.removeWidget(self.tcanvas)
            self.ui.specArea.removeWidget(self.bcanvas)
        except: pass

        #create the plotting canvas and its toolbar and add them
        tfig = Figure()
        self.tcanvas = FigureCanvasQTAgg(tfig)
        self.tnavbar = AstonNavBar(self.tcanvas,self)
        self.ui.plotArea.addWidget(self.tnavbar)
        self.ui.plotArea.addWidget(self.tcanvas)
    
        self.tplot = tfig.add_subplot(111)
        self.tcanvas.mpl_connect('scroll_event',self.mousescroll)
        self.tcanvas.mpl_connect('button_press_event',self.mousedown)

        bfig = Figure()
        self.bcanvas = FigureCanvasQTAgg(bfig)
        self.ui.specArea.addWidget(self.bcanvas)
        self.bplot = bfig.add_subplot(111)
        
        #create the thing that keeps track of how the plot should look
        self.plotter = Plotter(self.tplot, self.tnavbar)

        #add stuff to the combo boxes
        self.ui.colorSchemeComboBox.addItems(self.plotter.availColors())
        self.ui.styleComboBox.addItems(self.plotter.availStyles())

        #make the buttons update the graph
        self.ui.legendCheckBox.clicked.connect(self.plotData)
        self.ui.colorSchemeComboBox.currentIndexChanged.connect(self.plotData)
        self.ui.styleComboBox.currentIndexChanged.connect(self.plotData)

    def updateWindows(self):
        self.ui.filesDockWidget.setVisible(self.ui.actionFiles.isChecked())
        self.ui.settingsDockWidget.setVisible(self.ui.actionSettings.isChecked())
        self.ui.peaksDockWidget.setVisible(self.ui.actionPeaks.isChecked())
        self.ui.spectraDockWidget.setVisible(self.ui.actionSpectra.isChecked())

    def updateWindowsMenu(self):
        self.ui.actionFiles.setChecked(self.ui.filesDockWidget.isVisible())
        self.ui.actionSettings.setChecked(self.ui.settingsDockWidget.isVisible())
        self.ui.actionPeaks.setChecked(self.ui.peaksDockWidget.isVisible())
        self.ui.actionSpectra.setChecked(self.ui.spectraDockWidget.isVisible())

    def openFolder(self):
        from aston.FileTable import FileTreeModel

        folder = str(QtGui.QFileDialog.getExistingDirectory(self,"Open Folder"))
        if folder == '': return
        self.directory = folder
        self.ftab_mod = FileTreeModel(self.directory,self.ui.fileTreeView,self)

    def chromatogramAsPic(self):
        fname = str(QtGui.QFileDialog.getSaveFileName(self,"Save As..."))
        self.tplot.get_figure().savefig(fname,transparent=True)

    def chromatogramAsCSV(self):
        fname = str(QtGui.QFileDialog.getSaveFileName(self,"Save As..."))
        f = open(fname,'w')
        cgrm = self.ftab_mod.returnSelFile()
        a = [['"Time"'] + [str(i) for i in cgrm.time()]]
        for x in cgrm.info['traces'].split(','):
            if x != '':
                a += [['"'+x+'"'] + [str(i) for i in cgrm.trace(x)]]
        for i in zip(*a):
            f.write(','.join(i) + '\n')
        f.close()

    def spectrumAsCSV(self):
        fname = str(QtGui.QFileDialog.getSaveFileName(self,"Save As..."))
        f = open(fname,'w')
        cgrm = self.ftab_mod.returnSelFile()
        scan = cgrm.scan(self.spec_line.get_xdata()[0])
        mz,abun = scan.keys(),scan.values()
        a = [['mz','abun']]
        a += zip([str(i) for i in mz],[str(i) for i in abun])
        for i in a:
            f.write(','.join(i) + '\n')
        f.close()
        
    def spectrumAsPic(self):
        fname = str(QtGui.QFileDialog.getSaveFileName(self,"Save As..."))
        self.bplot.get_figure().savefig(fname,transparent=True)

    def peakListAsCSV(self):
        fname = str(QtGui.QFileDialog.getSaveFileName(self,"Save As..."))
        f = open(fname,'w')
        for i in self.ptab_mod.peaks:
            f.write(str(i.time()) + ',' + str(i.length()) + ',' + str(i.area()) + '\n')
        f.close()

    def quickIntegrate(self):
        from aston.PeakTable import statSlopeIntegrate
        dt = self.ftab_mod.returnSelFile() 
        ions = [i for i in dt.info['traces'].split(',')]
        self.ptab_mod.beginResetModel()

        #add compounds for ions from the first set
        pks = statSlopeIntegrate(self.ptab_mod,dt,ions[0])
        for pk in pks: 
            self.ptab_mod.addCompoundWithPeak(pk,str(pk.time()))
            self.ptab_mod.addPatchToCanvas(pk)

        #add other ions into first compounds
        for ion in ions[1:]:
            pks = statSlopeIntegrate(self.ptab_mod,dt,ion)
            for pk in pks:
                for cmpd in self.ptab_mod.compounds[1:]:
                    opk = cmpd.getPeaks(self.ptab_mod.fids)[0]
                    if pk.time()-opk.time() < 0.01:
                        cmpd.addPeak(pk)
                        self.ptab_mod.database.addCompound(cmpd)
                        self.ptab_mod.addPatchToCanvas(pk)
                        break
                if pk.ids[1] is None:
                    self.ptab_mod.addCompoundWithPeak(pk,str(pk.time()))
                    self.ptab_mod.addPatchToCanvas(pk)
        self.ptab_mod.endResetModel() 
        self.tcanvas.draw()

    def calculateInfo(self):
        pass

    def removePeriodicNoise(self):
        pass

    def smooth(self):
        from PyQt4.QtGui import QInputDialog
        x = QInputDialog.getItem(self,'Smoothing Type','Aston',['Moving Average','Savitsky-Golay','None'],editable=False)
        if not x[1]: return
        if x[0] == 'Moving Average':
            x = QInputDialog.getInteger(self,'Window Size','Aston',value=5)
            if not x[1]: return
            self.data.setInfo('smooth','moving_average')
            self.data.setInfo('smooth_window',str(x[0]))
        elif x[0] == 'Savitsky-Golay':
            x = QInputDialog.getInteger(self,'Window Size','Aston',value=5)
            if not x[1]: return
            y = QInputDialog.getInteger(self,'Polynomial Order','Aston',value=3)
            if not y[1]: return
            self.data.setInfo('smooth','savitsky_golay')
            self.data.setInfo('smooth_window',str(x[0]))
            self.data.setInfo('smooth_order',str(y[0]))
        else:
            self.data.setInfo('smooth','')

    def alignChrom(self):
        from PyQt4.QtGui import QInputDialog
        x = QInputDialog.getDouble(self, 'Scale by?', 'Aston', value = 1)
        if not x[1]: return
        if x[0] == 0 or x[0] == 1:
            self.data.setInfo('scale','')
        else:
            self.data.setInfo('scale',str(x[0]))

        x = QInputDialog.getDouble(self, 'Offset by?', 'Aston', value = 0)
        if not x[1]: return
        if x[0] == 0:
            self.data.setInfo('offset','')
        else:
            self.data.setInfo('offset',str(x[0]))

    def revertChromChange(self):
        keys = ['scale', 'yscale', 'offset', 'yoffset', 'smooth', \
          'smooth window', 'smooth order', 'remove_periodic_noise']
        for dt in self.ftab_mod.returnSelFiles():
            for key in keys:
                try: del dt.info[key]
                except: pass
            dt.saveChanges()
        self.plotData()

    def plotData(self,**kwargs):
        self.plotter.setColorScheme(self.ui.colorSchemeComboBox.currentText())
        self.plotter.style = str(self.ui.styleComboBox.currentText()).lower()
        if self.ui.legendCheckBox.isChecked():
            self.plotter.style += ' legend'

        datafiles = self.ftab_mod.returnChkFiles()
        if 'updateBounds' in kwargs:
            self.plotter.plotData(datafiles,self.ptab_mod,kwargs['updateBounds'])
        else:
            self.plotter.plotData(datafiles,self.ptab_mod)
        self.tcanvas.draw()

#    def plotData(self,updateBounds=True):
#        #get the files that have been checked to be visible
#        datafiles = self.ftab_mod.returnChkFiles()
#
#        if not updateBounds:
#            bnds = self.tplot.get_xlim(),self.tplot.get_ylim()
#
#        #plot all of the datafiles
#        self.tplot.cla()
#        for x in datafiles:
#            for y in x.info['traces'].split(','):
#                if y != '': self.tplot.plot(x.time(),x.trace(y),label=x.name+' '+y)
#
#        #add a legend and make it pretty
#        if self.ui.legendCheckBox.isChecked():
#            leg = self.tplot.legend(frameon=False)
#            #leg.get_frame().edgecolor = None
#            clrs = [i.get_color() for i in leg.get_lines()]
#            for i,j in enumerate(clrs):
#                leg.get_texts()[i].set_color(j)
#            for i in leg.get_lines():
#                i.set_linestyle('')
#
#        if updateBounds:
#            #update the view bounds in the navbar's history
#            self.tnavbar._views.clear()
#            self.tnavbar._positions.clear()
#            self.tnavbar.push_current()
#        else:
#            self.tplot.set_xlim(bnds[0])
#            self.tplot.set_ylim(bnds[1])
#
#        #draw peaks
#        if self.ptab_mod is not None: self.ptab_mod.drawPeaks()
#
#        #redraw the canvas
#        self.tcanvas.draw()

    def updateSearch(self,text):
        self.ftab_mod.proxyMod.setFilterFixedString(text)

    def mousedown(self, event):
        if event.button == 3 and self.tnavbar.mode != 'align':
            #get the specral data of the current point
            cur_file = self.ftab_mod.returnSelFile()
            if cur_file is None: return
            if not cur_file.visible: return
            scan = cur_file.scan(event.xdata)

            #plot it in the area below
            self.bplot.cla()
            self.bplot.vlines(scan.keys(),[0],scan.values())
            self.bplot.set_ylim(bottom=0)
            self.bcanvas.draw()
            
            # draw a line on the main plot for the location
            try: self.tplot.lines.remove(self.spec_line)
            except: pass
            self.spec_line = self.tplot.axvline(event.xdata,color='black')
            self.tcanvas.draw()
    
    def mousescroll(self,event):
        xmin,xmax = self.tplot.get_xlim()
        ymin,ymax = self.tplot.get_ylim()
        if event.button == 'up': #zoom in
            self.tplot.set_xlim(event.xdata-(event.xdata-xmin)/2.,event.xdata+(xmax-event.xdata)/2.)
            self.tplot.set_ylim(event.ydata-(event.ydata-ymin)/2.,event.ydata+(ymax-event.ydata)/2.)
        elif event.button == 'down': #zoom out
            xmin, xmax = event.xdata-2*(event.xdata-xmin),event.xdata+2*(xmax-event.xdata)
            xmin, xmax = max(xmin,self.tnavbar._views.home()[0][0]), min(xmax,self.tnavbar._views.home()[0][1])
            ymin, ymax = event.ydata-2*(event.ydata-ymin),event.ydata+2*(ymax-event.ydata)
            ymin, ymax = max(ymin,self.tnavbar._views.home()[0][2]), min(ymax,self.tnavbar._views.home()[0][3])
            self.tplot.axis([xmin,xmax,ymin,ymax])
        self.tcanvas.draw()

if __name__ == "__main__":
    import sys

    #standard QT stuff to set up
    app = QtGui.QApplication(sys.argv)
    myapp = AstonWindow()
    myapp.show()
    sys.exit(app.exec_())
