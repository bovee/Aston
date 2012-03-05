from PyQt4 import QtCore, QtGui

from aston_ui import Ui_MainWindow
from aston.ui.FilterWindow import FilterWindow
from aston.ui.MainPlot import Plotter
from aston.ui.SpecPlot import SpecPlotter

from aston.FileTable import FileTreeModel
from aston.Math.Integrators import waveletIntegrate, statSlopeIntegrate
from aston.Features import Spectrum

class AstonWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        ##my icon! TODO: make an icon
        #icn_path = op.join(op.curdir,'aston','ui','icons','aston.png')
        #self.setIcon(QtGui.QIcon(icn_path))

        #quick fix for Mac OS menus
        self.ui.actionSettings.setMenuRole(QtGui.QAction.NoRole)

        #set up the grouping for the dock widgets
        self.tabifyDockWidget(self.ui.filesDockWidget,self.ui.settingsDockWidget)
        self.tabifyDockWidget(self.ui.filesDockWidget,self.ui.spectraDockWidget)
        self.tabifyDockWidget(self.ui.filesDockWidget,self.ui.methodDockWidget)
        self.tabifyDockWidget(self.ui.filesDockWidget,self.ui.compoundDockWidget)
        self.ui.filesDockWidget.raise_()

        #connect the menu logic
        self.ui.actionOpen.triggered.connect(self.openFolder)
        self.ui.actionPeak_List_as_CSV.triggered.connect(self.peakListAsCSV)
        self.ui.actionChromatogram_as_Picture.triggered.connect(self.chromatogramAsPic)
        self.ui.actionChromatogram_as_CSV.triggered.connect(self.chromatogramAsCSV)
        self.ui.actionSpectra_as_Picture.triggered.connect(self.spectrumAsPic)
        self.ui.actionSpectra_as_CSV.triggered.connect(self.spectrumAsCSV)
        self.ui.actionIntegrate.triggered.connect(self.quickIntegrate)
        self.ui.actionEditFilters.triggered.connect(self.showFilterWindow)
        self.ui.actionRevert.triggered.connect(self.revertChromChange)
        self.ui.actionQuit.triggered.connect(QtGui.qApp.quit)

        #hook up the windows to the menu
        self.ui.actionFiles.triggered.connect(self.updateWindows)
        self.ui.actionSettings.triggered.connect(self.updateWindows)
        self.ui.actionSpectra.triggered.connect(self.updateWindows)
        self.ui.actionMethods.triggered.connect(self.updateWindows)
        self.ui.actionCompounds.triggered.connect(self.updateWindows)
        self.ui.filesDockWidget.visibilityChanged.connect(self.updateWindowsMenu)
        self.ui.settingsDockWidget.visibilityChanged.connect(self.updateWindowsMenu)
        self.ui.spectraDockWidget.visibilityChanged.connect(self.updateWindowsMenu)
        self.ui.methodDockWidget.visibilityChanged.connect(self.updateWindowsMenu)
        self.ui.compoundDockWidget.visibilityChanged.connect(self.updateWindowsMenu)
        self.ui.compoundDockWidget.setVisible(False)
        self.ui.methodDockWidget.setVisible(False)

        #hook up the search box
        self.ui.lineEdit.textChanged.connect(self.updateSearch)

        #create the things that keep track of how the plots should look
        self.plotter = Plotter(self)
        self.specplotter = SpecPlotter(self)

        #add stuff to the combo boxes
        self.ui.colorSchemeComboBox.addItems(self.plotter.availColors())
        self.ui.styleComboBox.addItems(self.plotter.availStyles())

        #make the buttons update the graph
        self.ui.legendCheckBox.clicked.connect(self.plotData)
        self.ui.colorSchemeComboBox.currentIndexChanged.connect(self.plotData)
        self.ui.styleComboBox.currentIndexChanged.connect(self.plotData)

        #set up the list of files in the current directory
        self.directory = '.'
        self.obj_tab = FileTreeModel(self.directory,self.ui.fileTreeView,self)
        self.plotData()

    def updateWindows(self):
        'Update the tab windows to match the menu.'
        self.ui.filesDockWidget.setVisible(self.ui.actionFiles.isChecked())
        self.ui.settingsDockWidget.setVisible(self.ui.actionSettings.isChecked())
        self.ui.spectraDockWidget.setVisible(self.ui.actionSpectra.isChecked())
        self.ui.methodDockWidget.setVisible(self.ui.actionMethods.isChecked())
        self.ui.compoundDockWidget.setVisible(self.ui.actionCompounds.isChecked())

    def updateWindowsMenu(self):
        'Update the windows menu to match the tab.'
        self.ui.actionFiles.setChecked(self.ui.filesDockWidget.isVisible())
        self.ui.actionSettings.setChecked(self.ui.settingsDockWidget.isVisible())
        self.ui.actionSpectra.setChecked(self.ui.spectraDockWidget.isVisible())
        self.ui.actionMethods.setChecked(self.ui.methodDockWidget.isVisible())
        self.ui.actionCompounds.setChecked(self.ui.compoundDockWidget.isVisible())

    def openFolder(self):
        folder = str(QtGui.QFileDialog.getExistingDirectory(self,"Open Folder"))
        if folder == '': return
        self.directory = folder
        
        #need to discard old connections
        self.ui.fileTreeView.clicked.disconnect()
        self.ui.fileTreeView.customContextMenuRequested.disconnect()
        self.ui.fileTreeView.header().customContextMenuRequested.disconnect()
        self.ui.fileTreeView.header().sectionMoved.disconnect()
        
        #load everything
        self.obj_tab = FileTreeModel(self.directory,self.ui.fileTreeView,self)
        self.plotData()

    def chromatogramAsPic(self):
        fname = str(QtGui.QFileDialog.getSaveFileName(self,"Save As..."))
        self.plotter.plt.get_figure().savefig(fname,transparent=True)

    def chromatogramAsCSV(self):
        fname = str(QtGui.QFileDialog.getSaveFileName(self,"Save As..."))
        f = open(fname,'w')
        dt = self.obj_tab.returnSelFile()
        a = [['"Time"'] + [str(i) for i in dt.time()]]
        for x in dt.info['traces'].split(','):
            if x != '':
                a += [['"'+x+'"'] + [str(i) for i in cgrm.trace(x)]]
        for i in zip(*a):
            f.write(','.join(i) + '\n')
        f.close()

    def spectrumAsCSV(self):
        #FIXME
        fname = str(QtGui.QFileDialog.getSaveFileName(self,"Save As..."))
        f = open(fname,'w')
        cgrm = self.obj_tab.returnSelFile()
        scan = cgrm.scan(self.spec_line.get_xdata()[0])
        mz,abun = scan.keys(),scan.values()
        a = [['mz','abun']]
        a += zip([str(i) for i in mz],[str(i) for i in abun])
        for i in a:
            f.write(','.join(i) + '\n')
        f.close()
        
    def spectrumAsPic(self):
        fname = str(QtGui.QFileDialog.getSaveFileName(self,"Save As..."))
        self.specplotter.plt.get_figure().savefig(fname, transparent=True)

    def peakListAsCSV(self):
        #FIXME
        fname = str(QtGui.QFileDialog.getSaveFileName(self,"Save As..."))
        f = open(fname,'w')
        for i in self.ptab_mod.peaks:
            f.write(str(i.time()) + ',' + str(i.length()) + ',' + str(i.area()) + '\n')

        f.close()

    def quickIntegrate(self):
        #TODO: group peaks by time
        dt = self.obj_tab.returnSelFile() 
        ions = [i for i in dt.info['traces'].split(',')]

        #add compounds for ions from the first set
        for ion in ions:
            pks = waveletIntegrate(dt, ion)
            #pks = statSlopeIntegrate(dt, ion)
            self.obj_tab.addObjects(dt, pks)
        dt.delInfo('s-peaks')
        self.plotter.redraw()

    def showFilterWindow(self):
        if self.obj_tab.returnSelFile() is not None:
            self.dlg = FilterWindow(self)
            self.dlg.show()

    def revertChromChange(self):
        'Delete all of the info keys related to display transformations.'
        for dt in self.obj_tab.returnSelFiles('file'):
            dt.delInfo('t-')
        self.plotData()

    def plotData(self,**kwargs):
        self.plotter.setColorScheme(self.ui.colorSchemeComboBox.currentText())
        self.plotter.style = str(self.ui.styleComboBox.currentText()).lower()
        if self.ui.legendCheckBox.isChecked():
            self.plotter.style += ' legend'

        datafiles = self.obj_tab.returnChkFiles()
        if 'updateBounds' in kwargs:
            self.plotter.plotData(datafiles,kwargs['updateBounds'])
        else:
            self.plotter.plotData(datafiles)

    def updateSearch(self, text):
        '''If the search box changes, update the file table.'''
        self.obj_tab.proxyMod.setFilterFixedString(text)
