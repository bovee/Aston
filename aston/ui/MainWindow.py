import os.path as op
import pkg_resources
from PyQt4 import QtGui

from aston.ui.aston_ui import Ui_MainWindow
from aston.ui.FilterWindow import FilterWindow
from aston.ui.MainPlot import Plotter
from aston.ui.SpecPlot import SpecPlotter

from aston.Database import AstonFileDatabase
from aston.Database import AstonDatabase
from aston.FileTable import FileTreeModel
import aston.ui.MenuOptions
from aston.Math.Integrators import merge_ions, update_peaks
from aston.Math.PeakFinding import event_peak_find


class AstonWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        #my icon!
        icn_path = pkg_resources.resource_filename(__name__, \
          op.join('icons', 'logo.png'))
        self.setWindowIcon(QtGui.QIcon(icn_path))

        #quick fix for Mac OS menus
        self.ui.actionSettings.setMenuRole(QtGui.QAction.NoRole)

        #set up the list of files in the current directory
        self.directory = op.expanduser(self.getPref('Default.FILE_DIRECTORY'))
        file_db = AstonFileDatabase(op.join(self.directory, 'aston.sqlite'))
        self.obj_tab = FileTreeModel(file_db, self.ui.fileTreeView, self)

        #connect the menu logic
        self.ui.actionOpen.triggered.connect(self.openFolder)
        self.ui.actionExportChromatogram.triggered.connect( \
          self.exportChromatogram)
        self.ui.actionExportSpectra.triggered.connect(self.exportSpectrum)
        self.ui.actionExportSelectedItems.triggered.connect(self.exportItems)
        self.ui.actionIntegrate.triggered.connect(self.integrate)
        self.ui.actionEditFilters.triggered.connect(self.showFilterWindow)
        self.ui.actionRevert.triggered.connect(self.revertChromChange)
        self.ui.actionQuit.triggered.connect(QtGui.qApp.quit)

        #hook up the windows to the menu
        for ac in [self.ui.actionFiles, self.ui.actionSettings, \
          self.ui.actionSpectra, self.ui.actionMethods, \
          self.ui.actionCompounds]:
            ac.triggered.connect(self.updateWindows)

        #set up the grouping for the dock widgets and
        #hook the menus up to the windows
        for ac in [self.ui.filesDockWidget, self.ui.spectraDockWidget, \
          self.ui.settingsDockWidget, self.ui.methodDockWidget,
          self.ui.compoundDockWidget]:
            if ac is not self.ui.filesDockWidget:
                self.tabifyDockWidget(self.ui.filesDockWidget, ac)
            ac.visibilityChanged.connect(self.updateWindowsMenu)
        self.ui.filesDockWidget.raise_()
        self.ui.settingsDockWidget.setVisible(False)
        self.ui.compoundDockWidget.setVisible(False)
        self.ui.methodDockWidget.setVisible(False)

        #hook up the search box
        self.ui.lineEdit.textChanged.connect(self.updateSearch)

        #create the things that keep track of how the plots should look
        self.plotter = Plotter(self)
        self.specplotter = SpecPlotter(self)

        #make integrator options
        peak_find_menu = QtGui.QMenu(self.ui.menuChromatogram)
        v = aston.ui.MenuOptions.peak_finders.keys()[0]
        self._add_opts_to_menu(peak_find_menu, \
          aston.ui.MenuOptions.peak_finders.keys(),
          lambda: None, v)
        self.ui.actionPeak_Finder.setMenu(peak_find_menu)

        integrator_menu = QtGui.QMenu(self.ui.menuChromatogram)
        v = aston.ui.MenuOptions.integrators.keys()[0]
        self._add_opts_to_menu(integrator_menu, \
          aston.ui.MenuOptions.integrators.keys(),
          lambda: None, v)
        self.ui.actionIntegrator.setMenu(integrator_menu)

        menu_gp = QtGui.QActionGroup(self)
        for ac in self.ui.menuIntegrand.actions():
            menu_gp.addAction(ac)

        #flesh out the settings menu
        color_menu = QtGui.QMenu(self.ui.menuSettings)
        v = self.obj_tab.db.get_key('color_scheme', dflt='Spectral')
        v = self.plotter._colors[v]
        self.plotter.setColorScheme(v)
        self._add_opts_to_menu(color_menu, \
          self.plotter.availColors(), self.set_color_scheme, v)
        self.ui.actionColor_Scheme.setMenu(color_menu)

        self.ui.actionLegend.triggered.connect(self.set_legend)
        self.ui.actionGraphFxnCollection.triggered.connect(self.set_legend)
        self.ui.actionGraphFIA.triggered.connect(self.set_legend)
        self.ui.actionGraphIRMS.triggered.connect(self.set_legend)
        self.ui.actionGraph_Peaks_Found.triggered.connect(self.set_legend)

        style_menu = QtGui.QMenu(self.ui.menuSettings)
        v = self.obj_tab.db.get_key('graph_style', dflt='default')
        v = self.plotter._styles[v]
        self.plotter.setStyle(v)
        self._add_opts_to_menu(style_menu, \
          self.plotter.availStyles(), self.set_graph_style, v)
        self.ui.actionGraph_Style.setMenu(style_menu)

        #plot data
        self.plotData()

        #set up the compound database
        cmpd_db = AstonDatabase(self.getPref('Default.COMPOUND_DB'))
        self.cmpd_tab = FileTreeModel(cmpd_db, self.ui.compoundTreeView, self)

    def _add_opts_to_menu(self, menu, opts, fxn, dflt=None):
        menu_gp = QtGui.QActionGroup(self)
        for opt in opts:
            act = menu.addAction(opt, fxn)
            act.setData(opt)
            act.setCheckable(True)
            if opt == dflt:
                act.setChecked(True)
            menu_gp.addAction(act)
        pass

    def updateWindows(self):
        """
        Update the tab windows to match the menu.
        """
        self.ui.filesDockWidget.setVisible(self.ui.actionFiles.isChecked())
        self.ui.settingsDockWidget.setVisible( \
          self.ui.actionSettings.isChecked())
        self.ui.spectraDockWidget.setVisible(self.ui.actionSpectra.isChecked())
        self.ui.methodDockWidget.setVisible(self.ui.actionMethods.isChecked())
        self.ui.compoundDockWidget.setVisible( \
          self.ui.actionCompounds.isChecked())

    def updateWindowsMenu(self):
        """
        Update the windows menu to match the tab.
        """
        self.ui.actionFiles.setChecked(self.ui.filesDockWidget.isVisible())
        self.ui.actionSettings.setChecked( \
          self.ui.settingsDockWidget.isVisible())
        self.ui.actionSpectra.setChecked(self.ui.spectraDockWidget.isVisible())
        self.ui.actionMethods.setChecked(self.ui.methodDockWidget.isVisible())
        self.ui.actionCompounds.setChecked( \
          self.ui.compoundDockWidget.isVisible())

    def show_status(self, msg):
        self.statusBar().showMessage(msg, 2000)

    def getPref(self, key):
        try:
            import configparser
        except ImportError:
            import ConfigParser as configparser
        cp = configparser.SafeConfigParser()
        for cfg in (op.expanduser('~/.aston.ini'), './aston.ini'):
            if op.exists(cfg):
                cp.readfp(open(cfg))
                break
        else:
            pass
            #TODO: write out this file?
        try:
            return cp.get(key.split('.')[0], key.split('.')[1])
        except:
            return ''

    def openFolder(self):
        folder = str(QtGui.QFileDialog.getExistingDirectory(self, \
          self.tr("Open Folder")))
        if folder == '':
            return
        self.directory = folder

        #need to discard old connections
        self.ui.fileTreeView.clicked.disconnect()
        self.ui.fileTreeView.customContextMenuRequested.disconnect()
        self.ui.fileTreeView.header().customContextMenuRequested.disconnect()
        self.ui.fileTreeView.header().sectionMoved.disconnect()

        #load everything
        file_db = AstonFileDatabase(op.join(self.directory, 'aston.sqlite'))
        self.obj_tab = FileTreeModel(file_db, self.ui.fileTreeView, self)
        self.plotData()

    def set_color_scheme(self):
        v = self.plotter.setColorScheme(self.sender().data())
        self.obj_tab.db.set_key('color_scheme', v)
        self.plotData(updateBounds=False)

    def set_legend(self):
        self.plotter.legend = self.ui.actionLegend.isChecked()
        self.plotData(updateBounds=False)

    def set_graph_style(self):
        v = self.plotter.setStyle(self.sender().data())
        self.obj_tab.db.set_key('graph_style', v)
        self.plotData()

    def exportChromatogram(self):
        fopts = self.tr("Bitmap Image (*.png *.pgf *.raw *rgba);;" + \
          "Vector Image (*.svg *.emf *.eps *.pdf *.ps *.svgz);;" + \
          "Comma-Delimited Text (*.csv)")
        fname = str(QtGui.QFileDialog.getSaveFileName(self, \
          self.tr("Save As..."), filter=fopts))
        if fname == '':
            return
        elif fname[-4:].lower() == '.csv':
            dt = self.obj_tab.active_file()
            ts = None
            for ion in dt.info['traces'].split(','):
                if ts is None:
                    ts = dt.trace(ion)
                else:
                    ts &= dt.trace(ion)

            with open(fname, 'w') as f:
                f.write(self.tr('Time') + ',' + ','.join(ts.ions) + ',\n')
                for t, d in zip(ts.times, ts.data):
                    f.write(str(t) + ',' + ','.join(str(i) \
                      for i in d) + '\n')
        else:
            self.plotter.plt.get_figure().savefig(fname, transparent=True)

    def exportSpectrum(self):
        #TODO: this needs to be updated when SpecPlot becomes better
        fopts = self.tr("Bitmap Image (*.png *.pgf *.raw *rgba);;" + \
          "Vector Image (*.svg *.emf *.eps *.pdf *.ps *.svgz);;" + \
          "Comma-Delimited Text (*.csv)")
        fname = str(QtGui.QFileDialog.getSaveFileName(self, \
          self.tr("Save As..."), filter=fopts))
        if fname == '':
            return
        elif fname[-4:].lower() == '.csv':
            if '' not in self.specplotter.scans:
                return
            with open(fname, 'w') as f:
                scan = self.specplotter.scans['']
                f.write(self.tr('mz') + ',' + self.tr('abun') + '\n')
                for mz, abun in scan.T:
                    f.write(str(mz) + ',' + str(abun) + '\n')
        else:
            self.specplotter.plt.get_figure().savefig(fname, transparent=True)

    def exportItems(self):
        #TODO: options for exporting different delimiters (e.g. tab) or
        #exporting select items as pictures (e.g. selected spectra)
        fname = str(QtGui.QFileDialog.getSaveFileName(self, \
          self.tr("Save As...")))
        f = open(fname, 'w')
        sel = self.obj_tab.returnSelFiles()
        f.write(self.obj_tab.items_as_csv(sel))
        f.close()

    def find_peaks_top_trace(self):
        #TODO: clunky copy of code from integrate, but
        # needed for display "peaks found" on graph
        dt = self.obj_tab.active_file()
        ion = dt.info['traces'].split(',')[0]

        submnu = self.ui.actionPeak_Finder.menu().children()
        opt = [i for i in submnu if i.isChecked()][0].text()
        peak_find = aston.ui.MenuOptions.peak_finders[opt]

        if peak_find == event_peak_find:
            return []
        else:
            return peak_find(dt.trace(ion))

    def integrate(self):
        dt = self.obj_tab.active_file()
        ions = [i for i in dt.info['traces'].split(',')]

        submnu = self.ui.actionPeak_Finder.menu().children()
        opt = [i for i in submnu if i.isChecked()][0].text()
        peak_find = aston.ui.MenuOptions.peak_finders[opt]

        submnu = self.ui.actionIntegrator.menu().children()
        opt = [i for i in submnu if i.isChecked()][0].text()
        integrate = aston.ui.MenuOptions.integrators[opt]

        int_name = peak_find.__name__ + ',' + integrate.__name__

        if self.ui.actionTop_Trace.isChecked():
            tss = [dt.trace(ions[0])]
        elif self.ui.actionTop_File_Vis_Traces.isChecked():
            tss = [dt.trace(i) for i in ions]
        elif self.ui.actionTop_File_All_Traces.isChecked():
            tss = [dt.trace(i) for i in dt.data.ions]

        all_pks = []
        for ts in tss:
            if peak_find == event_peak_find:
                tpks = peak_find(ts, dt.events())
            else:
                tpks = peak_find(ts)
            pks = integrate(ts, tpks)
            update_peaks(pks, dt, str(ts.ions[0]), \
                         ptype='Sample', created=int_name)
            all_pks += pks
        mrg_pks = merge_ions(all_pks)
        self.obj_tab.addObjects(dt, mrg_pks)
        dt.info.del_items('s-peaks')
        self.plotter.redraw()

    def showFilterWindow(self):
        if self.obj_tab.active_file() is not None:
            self.dlg = FilterWindow(self)
            self.dlg.show()

    def revertChromChange(self):
        """
        Delete all of the info keys related to display transformations.
        """
        for dt in self.obj_tab.returnSelFiles('file'):
            dt.info.del_items('t-')
        self.plotData()

    def plotData(self, **kwargs):
        datafiles = self.obj_tab.returnChkFiles()

        if 'updateBounds' in kwargs:
            self.plotter.plotData(datafiles, kwargs['updateBounds'])
        else:
            self.plotter.plotData(datafiles)

        # add all the peaks
        pks = []
        for dt in datafiles:
            pks += dt.getAllChildren('peak')
        self.plotter.add_peaks(pks)

    def updateSearch(self, text):
        """
        If the search box changes, update the file table.
        """
        self.obj_tab.proxyMod.setFilterFixedString(text)
