import codecs
import os.path as op
from PyQt4 import QtGui

from aston.ui.resources import resfile
from aston.ui.ui_mainwindow import Ui_MainWindow
from aston.ui.Settings import SettingsWidget
from aston.ui.FilterWindow import FilterWindow
from aston.ui.MainPlot import Plotter
from aston.ui.SpecPlot import SpecPlotter

from aston.databases.Database import AstonDatabase
from aston.databases.FileDatabase import AstonFileDatabase
from aston.databases.Compound import get_compound_db
from aston.ui.FileTable import FileTreeModel
import aston.ui.MenuOptions
from aston.peaks.PeakFinding import find_peaks
from aston.peaks.Integrators import integrate_peaks


class AstonWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        #my icon!
        icn_path = resfile('aston/ui', 'icons/logo.png')
        self.setWindowIcon(QtGui.QIcon(icn_path))

        #quick fix for Mac OS menus
        self.ui.actionSettings.setMenuRole(QtGui.QAction.NoRole)

        #set up the list of files in the current directory
        fdir = self.getPref('Default.FILE_DIRECTORY')
        if fdir is not None:
            self.directory = op.expanduser(fdir)
            file_db = AstonFileDatabase(op.join(self.directory, \
                                                'aston.sqlite'))
        else:
            file_db = AstonDatabase(None)
        self.obj_tab = FileTreeModel(file_db, self.ui.fileTreeView, self)

        #connect the menu logic
        self.ui.actionOpen.triggered.connect(self.open_folder)
        self.ui.actionExportChromatogram.triggered.connect( \
          self.exportChromatogram)
        self.ui.actionExportSpectra.triggered.connect(self.exportSpectrum)
        self.ui.actionExportSelectedItems.triggered.connect(self.exportItems)
        self.ui.actionIntegrate.triggered.connect(self.integrate)
        self.ui.actionEditFilters.triggered.connect(self.showFilterWindow)
        self.ui.actionRevert.triggered.connect(self.revertChromChange)
        self.ui.actionQuit.triggered.connect(QtGui.qApp.quit)
        self.ui.loadPeakList.triggered.connect(self.load_peaks)

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
        v = list(aston.ui.MenuOptions.peak_finders.keys())[0]
        self._add_opts_to_menu(peak_find_menu, \
          aston.ui.MenuOptions.peak_finders.keys(),
          lambda: None, v)
        self.ui.actionPeak_Finder.setMenu(peak_find_menu)

        integrator_menu = QtGui.QMenu(self.ui.menuChromatogram)
        v = list(aston.ui.MenuOptions.integrators.keys())[0]
        self._add_opts_to_menu(integrator_menu, \
          aston.ui.MenuOptions.integrators.keys(),
          lambda: None, v)
        self.ui.actionIntegrator.setMenu(integrator_menu)

        menu_gp = QtGui.QActionGroup(self)
        for ac in self.ui.menuIntegrand.actions():
            menu_gp.addAction(ac)

        # hook up spectrum menu
        for m in [self.ui.actionSpecLibDisp, self.ui.actionSpecLibLabel,\
                  self.ui.actionSpecMainDisp, self.ui.actionSpecMainLabel, \
                  self.ui.actionSpecPrevDisp, self.ui.actionSpecPrevLabel]:
            m.triggered.connect(self.specplotter.plot)
        self.ui.actionSpecMainSave.triggered.connect( \
          self.specplotter.save_main_spec)
        self.ui.actionSpecPrevSave.triggered.connect( \
          self.specplotter.save_prev_spec)

        #flesh out the settings menu
        color_menu = QtGui.QMenu(self.ui.menuSettings)
        v_cs = self.obj_tab.db.get_key('color_scheme', dflt='Spectral')
        v = self.plotter._colors[v_cs]
        self.plotter.setColorScheme(v)
        self._add_opts_to_menu(color_menu, \
          self.plotter.availColors(), self.set_color_scheme, v)
        self.ui.actionColor_Scheme.setMenu(color_menu)

        self.ui.actionLegend.triggered.connect(self.set_legend)
        self.ui.actionGraphGrid.triggered.connect(self.set_legend)
        self.ui.actionGraphLogYAxis.triggered.connect(self.set_legend)
        self.ui.actionGraphFxnCollection.triggered.connect(self.set_legend)
        self.ui.actionGraphFIA.triggered.connect(self.set_legend)
        self.ui.actionGraphIRMS.triggered.connect(self.set_legend)
        self.ui.actionGraph_Peaks_Found.triggered.connect(self.set_legend)

        style_menu = QtGui.QMenu(self.ui.menuSettings)
        v_gs = self.obj_tab.db.get_key('graph_style', dflt='default')
        v = self.plotter._styles[v_gs]
        self.plotter.setStyle(v)
        self._add_opts_to_menu(style_menu, \
          self.plotter.availStyles(), self.set_graph_style, v)
        self.ui.actionGraph_Style.setMenu(style_menu)

        # add settings widget in
        self.settingsWidget = SettingsWidget(self, db=file_db)
        self.ui.verticalLayout_settings.addWidget(self.settingsWidget)

        #plot data
        self.plotData()

        #set up the compound database
        cmpd_loc = self.obj_tab.db.get_key('db_compound', dflt='')
        if cmpd_loc != '':
            cmpd_db = get_compound_db(cmpd_loc)
            self.cmpd_tab = FileTreeModel(cmpd_db, self.ui.compoundTreeView, \
                                          self)

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
            return None

    def open_folder(self):
        folder = str(QtGui.QFileDialog.getExistingDirectory(self, \
          self.tr("Open Folder")))
        if folder == '':
            return
        self.directory = folder

        #need to discard old connections
        #self.ui.fileTreeView.clicked.disconnect()
        self.ui.fileTreeView.selectionModel().currentChanged.disconnect()
        self.ui.fileTreeView.customContextMenuRequested.disconnect()
        self.ui.fileTreeView.header().customContextMenuRequested.disconnect()
        self.ui.fileTreeView.header().sectionMoved.disconnect()

        file_loc = op.join(self.directory, 'aston.sqlite')
        self.load_new_file_db(file_loc)

    def load_new_file_db(self, file_loc):
        #TODO: this should be called by init too so opening a new file_db
        # will load all the preferences from that file_db (like what happens in
        # init now

        #load everything
        file_db = AstonFileDatabase(file_loc)
        self.obj_tab = FileTreeModel(file_db, self.ui.fileTreeView, self)
        self.settingsWidget.db = file_db
        self.plotData()

        cmpd_loc = file_db.get_key('db_compound', dflt='')
        if cmpd_loc != '':
            cmpd_db = get_compound_db(cmpd_loc)
            self.cmpd_tab = FileTreeModel(cmpd_db, self.ui.compoundTreeView, \
                                          self)

    def load_peaks(self):
        ftypes = 'AMDIS (*.*);;Isodat (*.*)'
        fname = QtGui.QFileDialog.getOpenFileName(self, \
          self.tr("Open File"), '', ftypes)
        if str(fname) == '':
            return
        from aston.peaks.PeakReader import read_peaks
        read_peaks(self.obj_tab.db, str(fname))
        self.plotData(updateBounds=False)

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
        fopts = self.tr('PNG Image (*.png);;PGF Image (*.pgf);;' + \
          'RAW Image (*.raw);;RGBA Image (*.rgba);;SVG Image (*.svg);;' + \
          'EMF Image (*.emf);;EPS Image (*.eps);;' + \
          'Portable Document Format (*.pdf);;Postscript Image (*.ps);;' + \
          'Compressed SVG File (*.svgz);;Comma-Delimited Text (*.csv)')
        fname = str(QtGui.QFileDialog.getSaveFileNameAndFilter(self, \
          self.tr("Save As..."), filter=fopts)[0])
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
        fopts = self.tr('PNG Image (*.png);;PGF Image (*.pgf);;' + \
          'RAW Image (*.raw);;RGBA Image (*.rgba);;SVG Image (*.svg);;' + \
          'EMF Image (*.emf);;EPS Image (*.eps);;' + \
          'Portable Document Format (*.pdf);;Postscript Image (*.ps);;' + \
          'Compressed SVG File (*.svgz);;Comma-Delimited Text (*.csv)')
        fname = str(QtGui.QFileDialog.getSaveFileNameAndFilter(self, \
          self.tr("Save As..."), filter=fopts)[0])
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
        fopts = self.tr('Comma-Delimited Text (*.csv)')
        fname = str(QtGui.QFileDialog.getSaveFileNameAndFilter(self, \
          self.tr("Save As..."), filter=fopts)[0])
        if fname == '':
            return
        sel = self.obj_tab.returnSelFiles()
        with codecs.open(fname, 'w', encoding='utf-8') as f:
            f.write(self.obj_tab.items_as_csv(sel))

    def get_f_opts(self, f):
        gf = lambda k, df: float(self.obj_tab.db.get_key(k, dflt=str(df)))
        gv = lambda k, df: str(self.obj_tab.db.get_key(k, dflt=str(df)))
        p = {}
        fname = f.__name__
        if fname == 'simple_peak_find':
            p['init_slope'] = gf('peakfind_simple_initslope', 500)
            p['start_slope'] = gf('peakfind_simple_startslope', 500)
            p['end_slope'] = gf('peakfind_simple_endslope', 200)
            p['min_peak_height'] = gf('peakfind_simple_minheight', 50)
            p['max_peak_width'] = gf('peakfind_simple_maxwidth', 1.5)
        elif fname == 'wavelet_peak_find':
            p['min_snr'] = gf('peakfind_wavelet_minsnr', 1)
            p['assume_sig'] = gf('peakfind_wavelet_asssig', 4)
        elif fname == 'event_peak_find':
            p['adjust_times'] = gv('peakfind_event_adjust', 'F') == 'T'
        elif fname == 'leastsq_integrate':
            p['f'] = gv('integrate_leastsq_f', 'gaussian')
        elif fname == 'periodic_integrate':
            p['offset'] = gf('integrate_periodic_offset', 0.)
            p['period'] = gf('integrate_periodic_period', 1.)
        return p

    def find_peaks(self, tss, dt, isomode=False):
        submnu = self.ui.actionPeak_Finder.menu().children()
        opt = [i for i in submnu if i.isChecked()][0].text()
        pf_f = aston.ui.MenuOptions.peak_finders[opt]
        pf_fopts = self.get_f_opts(pf_f)
        mp = self.obj_tab.db.get_key('multiprocessing', dflt=True)

        return find_peaks(tss, pf_f, pf_fopts, dt, isomode, mp)

    def integrate_peaks(self, tss, found_peaks, isomode=False):
        submnu = self.ui.actionIntegrator.menu().children()
        opt = [i for i in submnu if i.isChecked()][0].text()
        int_f = aston.ui.MenuOptions.integrators[opt]
        int_fopts = self.get_f_opts(int_f)
        mp = self.obj_tab.db.get_key('multiprocessing', dflt=True)

        return integrate_peaks(tss, found_peaks, int_f, int_fopts, isomode, mp)

    def integrate(self):
        dt = self.obj_tab.active_file()

        isomode = self.ui.actionTop_File_All_Isotopic.isChecked()
        if self.ui.actionTop_Trace.isChecked():
            tss = dt.active_traces(n=0)
        elif self.ui.actionTop_File_Vis_Traces.isChecked():
            tss = dt.active_traces()
        elif self.ui.actionTop_File_All_Traces.isChecked() or isomode:
            tss = dt.active_traces(all_tr=True)

        found_peaks = self.find_peaks(tss, dt, isomode)
        mrg_pks = self.integrate_peaks(tss, found_peaks, isomode)

        with dt.db:
            dt.children += mrg_pks
        dt.info.del_items('s-peaks')
        self.plotData(updateBounds=False)

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

    def updateSearch(self, text):
        """
        If the search box changes, update the file table.
        """
        self.obj_tab.proxyMod.setFilterFixedString(text)
