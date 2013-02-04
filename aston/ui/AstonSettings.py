from PyQt4 import QtGui
from aston.ui.aston_settings_ui import Ui_Form
from aston.Database import AstonDatabase


class AstonSettings(QtGui.QWidget):
    def __init__(self, parent=None, db=None):
        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.parent = parent
        self.db = db

        if db is not None:
            self.load_opts()
            self.ui.pushButtonCopyDB.clicked.connect(self.load_other_db)
            self.ui.comboIsotopeMethod.activated.connect(self.set_isotope)
            self.ui.comboIsotopeKs.activated.connect(self.set_isotope)

    def set_isotope(self):
        pass

    def numeric_opts(self):
        k_to_b = {'peakfind_simple_startslope': \
                  self.ui.doubleSpinSimpleStartSlope,
                  'peakfind_simple_endslope': \
                  self.ui.doubleSimpleEndSlope,
                  'peakfind_simple_maxwidth': \
                  self.ui.doubleSpinSimpleMaxPeakWidth,
                  'peakfind_simple_minheight': \
                  self.ui.doubleSpinSimpleMinPeakHgt,
                  'peakfind_wavelet_minsnr': \
                  self.ui.doubleSpinWaveletMinSNR,
                  'peakfind_wavelet_asssig': self.ui.doubleSpinWaveletAssSig,
                  'db_remove_deleted': self.ui.checkDBRemoveDeleted,
                  'db_reload_on_open': self.ui.checkDBRescan}
        return k_to_b

    def load_opts(self):
        k_to_b = self.numeric_opts()
        for k in k_to_b:
            v = self.db.get_key(k, dflt=None)
            if type(k_to_b[k]) == QtGui.QDoubleSpinBox:
                if v is not None:
                    k_to_b[k].setValue(float(v))
                k_to_b[k].valueChanged.connect(self.save_opts(k))
            elif type(k_to_b[k]) == QtGui.QCheckBox:
                if v is not None:
                    k_to_b[k].setChecked(v == 'T')
                k_to_b[k].stateChanged.connect(self.save_opts(k))

    def save_opts(self, k):
        def wrapped_f():
            k_to_b = self.numeric_opts()
            if type(k_to_b[k]) == QtGui.QDoubleSpinBox:
                self.db.set_key(k, str(k_to_b[k].value()))
            elif type(k_to_b[k]) == QtGui.QCheckBox:
                if k_to_b[k].isChecked():
                    self.db.set_key(k, 'T')
                else:
                    self.db.set_key(k, 'F')
        return wrapped_f

    def load_other_db(self):
        path = str(QtGui.QFileDialog.getOpenFileName(self,
          self.tr('Open DB'), '', self.tr('AstonDB (aston.sqlite)')))
        if path == '':
            return
        other_db_vals = AstonDatabase(path).all_keys()
        for k in other_db_vals:
            self.db.set_key(k, other_db_vals[k])

    #def set_up_graph(self):
    #    pass
    #    ##TODO: set defaults
    #    #v = self.db.get_key('graph_style', dflt='default')
    #    #v = self.plotter._styles[v]
    #    #self.plotter.setStyle(v)
    #    #styles = self.plotter.availStyles()
    #    #self.ui.comboGraphStyle.addItems(styles)
    #    #self.ui.comboGraphStyle.setCurrentIndex(styles.index(v))

    #    #v = self.db.get_key('color_scheme', dflt='Spectral')
    #    #v = self.plotter._colors[v]
    #    #self.plotter.setColorScheme(v)
    #    #colors = self.plotter.availColors()
    #    #self.ui.comboColorScheme.addItems(colors)
    #    #self.ui.comboColorScheme.setCurrentIndex(colors.index(v))

    #    #self.ui.comboGraphStyle.activated.connect(self.set_graph_style)
    #    #self.ui.comboColorScheme.activated.connect(self.set_color_scheme)
    #    #for chk in [self.ui.checkFIA, self.ui.checkFxnCollection, \
    #    #            self.ui.checkGasPulse, self.ui.checkLegend,
    #    #            self.ui.checkMSMS, self.ui.checkPeaksFound]:
    #    #    chk.clicked.connect(self.set_legend)

    #def set_color_scheme(self):
    #    #v = self.ui.comboColorScheme.currentText()
    #    #v = self.plotter.setColorScheme(v)
    #    #self.db.set_key('color_scheme', v)
    #    #self.parent.plotData(updateBounds=False)

    #def set_legend(self):
    #    self.plotter.legend = self.ui.checkLegend.isChecked()
    #    self.parent.plotData(updateBounds=False)

    #def set_graph_style(self):
    #    #v = self.ui.comboGraphStyle.currentText()
    #    #v = self.plotter.setStyle(v)
    #    #self.db.set_key('graph_style', v)
    #    #self.parent.plotData()
