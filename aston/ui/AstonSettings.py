from PyQt4 import QtGui
from aston.ui.aston_settings_ui import Ui_Form


class AstonSettings(QtGui.QWidget):
    def __init__(self, parent=None, db=None):
        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.parent = parent
        self.db = db

        if db is not None:
            self.load_numeric_opts()

    def numeric_opts(self):
        k_to_b = {'peakfind_simple_startslope': ('500', \
                  self.ui.doubleSpinSimpleStartSlope),
                  'peakfind_simple_endslope': ('200', \
                  self.ui.doubleSimpleEndSlope),
                  'peakfind_simple_maxwidth': ('1.5', \
                  self.ui.doubleSpinSimpleMaxPeakWidth),
                  'peakfind_simple_minheight': ('50', \
                  self.ui.doubleSpinSimpleMinPeakHgt),
                  'peakfind_wavelet_minsnr': ('1', \
                  self.ui.doubleSpinWaveletMinSNR),
                  'peakfind_wavelet_asssig': ('4', \
                  self.ui.doubleSpinWaveletAssSig)}
        return k_to_b

    def load_numeric_opts(self):
        k_to_b = self.numeric_opts()
        for k in k_to_b:
            v = self.db.get_key(k, dflt=k_to_b[k][0])
            k_to_b[k][1].setValue(float(v))
            k_to_b[k][1].valueChanged.connect(self.save_numeric_opts)

    def save_numeric_opts(self):
        k_to_b = self.numeric_opts()
        c = self.db.begin_lazy_op()
        for k in k_to_b:
            v = k_to_b[k][1].value()
            self.db.lazy_set_key(c, k, str(v))
        self.db.end_lazy_op(c)

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
