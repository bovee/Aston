from PyQt4 import QtCore, QtGui
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg

from aston_ui import Ui_MainWindow
from aston.ui.Navbar import AstonNavBar
from aston.ui.FilterWindow import FilterWindow

from aston.Plotting import Plotter, SpecPlotter
from aston.FileTable import FileTreeModel
from aston.Integrators import statSlopeIntegrate
from aston.Features import Spectrum

class AstonWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
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
        #self.connect(self.ui.actionSubtractAddChromatogram, QtCore.SIGNAL('triggered()'), self.calculateInfo)
        self.ui.actionEditFilters.triggered.connect(self.showFilterWindow)
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
        self.tcanvas.mpl_connect('button_press_event',self.mousedown)
        self.tcanvas.mpl_connect('scroll_event',self.mousescroll)

        #create the canvas for spectral plotting
        bfig = Figure()
        self.bcanvas = FigureCanvasQTAgg(bfig)
        self.ui.specArea.addWidget(self.bcanvas)

        self.bplot = bfig.add_subplot(111)
        self.bcanvas.mpl_connect('button_press_event',self.specmousedown)
        self.bcanvas.mpl_connect('scroll_event',self.specmousescroll)

        #create the things that keep track of how the plots should look
        self.plotter = Plotter(self.tplot, self.tcanvas, self.tnavbar)
        self.specplotter = SpecPlotter(self.bplot, self.bcanvas)

        #add stuff to the combo boxes
        self.ui.colorSchemeComboBox.addItems(self.plotter.availColors())
        self.ui.styleComboBox.addItems(self.plotter.availStyles())

        #make the buttons update the graph
        self.ui.legendCheckBox.clicked.connect(self.plotData)
        self.ui.colorSchemeComboBox.currentIndexChanged.connect(self.plotData)
        self.ui.styleComboBox.currentIndexChanged.connect(self.plotData)

    def updateWindows(self):
        #this updates the tab windows to match the menu
        self.ui.filesDockWidget.setVisible(self.ui.actionFiles.isChecked())
        self.ui.settingsDockWidget.setVisible(self.ui.actionSettings.isChecked())
        self.ui.peaksDockWidget.setVisible(self.ui.actionPeaks.isChecked())
        self.ui.spectraDockWidget.setVisible(self.ui.actionSpectra.isChecked())

    def updateWindowsMenu(self):
        #this updates the windows menu to match the tab
        self.ui.actionFiles.setChecked(self.ui.filesDockWidget.isVisible())
        self.ui.actionSettings.setChecked(self.ui.settingsDockWidget.isVisible())
        self.ui.actionPeaks.setChecked(self.ui.peaksDockWidget.isVisible())
        self.ui.actionSpectra.setChecked(self.ui.spectraDockWidget.isVisible())

    def openFolder(self):

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
        #TODO: does this still work?
        fname = str(QtGui.QFileDialog.getSaveFileName(self,"Save As..."))
        f = open(fname,'w')
        for i in self.ptab_mod.peaks:
            f.write(str(i.time()) + ',' + str(i.length()) + ',' + str(i.area()) + '\n')
        f.close()

    def quickIntegrate(self):
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

    def showFilterWindow(self):
        if self.ftab_mod.returnSelFile() is not None:
            self.dlg = FilterWindow(self)
            self.dlg.show()

    def revertChromChange(self):
        '''Go through and delete all of the info keys related to 
        display properties.'''
        keys = ['scale', 'yscale', 'offset', 'yoffset', 'smooth', \
          'smooth window', 'smooth order', 'remove noise']
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

    def updateSearch(self,text):
        '''If the search box changes, update the file table.'''
        self.ftab_mod.proxyMod.setFilterFixedString(text)

    def mousedown(self, event):
        if event.button == 3 and self.tnavbar.mode != 'align':
            #TODO: make this work for click and drag too
            #get the specral data of the current point
            cur_file = self.ftab_mod.returnSelFile()
            if cur_file is None: return
            if not cur_file.visible: return
            scan = cur_file.scan(event.xdata)
            
            self.specplotter.addSpec(scan)
            self.specplotter.plotSpec()
            self.specplotter.specTime = event.xdata
            
            # draw a line on the main plot for the location
            self.plotter.drawSpecLine(event.xdata,linestyle='-')
    
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

    def specmousedown(self,event):
        if event.button == 1:
            dlim = self.bplot.dataLim.get_points()
            self.bplot.axis([dlim[0][0],dlim[1][0],dlim[0][1],dlim[1][1]])
            self.bcanvas.draw()
        elif event.button == 3:
            #TODO: make the spec window work better
            menu = QtGui.QMenu(self.bcanvas)
            for i in self.specplotter.scans:
                if i == '':
                    ac = menu.addAction('current')
                else:
                    ac = menu.addAction(i)
                submenu = QtGui.QMenu(menu)
                sac = submenu.addAction('Display',self.togSpc)
                sac.setCheckable(True)
                sac.setChecked(i in self.specplotter.scansToDisp)
                sac.setData(i)
                sac = submenu.addAction('Label',self.spcLbl)
                sac.setCheckable(True)
                sac.setChecked(i in self.specplotter.scansToLbl)
                sac.setData(i)
                sac = submenu.addAction('Save',self.saveSpc)
                sac.setData(i)
                ac.setMenu(submenu)
                
            if not menu.isEmpty():
                menu.exec_(self.bcanvas.mapToGlobal(
                  QtCore.QPoint(event.x,self.bcanvas.height()-event.y)))

    def togSpc(self):
        scn_nm = str(self.sender().data())
        if scn_nm in self.specplotter.scansToDisp:
            self.specplotter.scansToDisp.remove(scn_nm)
        else:
            self.specplotter.scansToDisp.append(scn_nm)
        self.specplotter.plotSpec()

    def spcLbl(self):
        scn_nm = str(self.sender().data())
        if scn_nm in self.specplotter.scansToLbl:
            self.specplotter.scansToLbl.remove(scn_nm)
        else:
            self.specplotter.scansToLbl.append(scn_nm)
        self.specplotter.plotSpec()

    def saveSpc(self):
        scn_nm = str(self.sender().data())
        scn = self.specplotter.scans[scn_nm]
        spc = Spectrum(scn,None)
        spc.ids[2] = self.ftab_mod.returnSelFile().fid[1]
        self.ptab_mod.addFeats([spc])
    
    def specmousescroll(self,event):
        xmin,xmax = self.bplot.get_xlim()
        ymin,ymax = self.bplot.get_ylim()
        if event.button == 'up': #zoom in
            self.bplot.set_xlim(event.xdata-(event.xdata-xmin)/2.,event.xdata+(xmax-event.xdata)/2.)
            self.bplot.set_ylim(event.ydata-(event.ydata-ymin)/2.,event.ydata+(ymax-event.ydata)/2.)
        elif event.button == 'down': #zoom out
            dlim = self.bplot.dataLim.get_points()
            xmin = max(event.xdata-2*(event.xdata-xmin),dlim[0][0])
            xmax = min(event.xdata+2*(xmax-event.xdata),dlim[1][0])
            ymin = max(event.ydata-2*(event.ydata-ymin),dlim[0][1])
            ymax = min(event.ydata+2*(ymax-event.ydata),dlim[1][1])
            self.bplot.axis([xmin,xmax,ymin,ymax])
        self.bcanvas.draw()
