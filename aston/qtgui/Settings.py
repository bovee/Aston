from PyQt5 import QtGui, QtWidgets
from aston.qtgui.ui_settings import Ui_Form
#from aston.database.Database import AstonDatabase
#from aston.database.Compound import get_compound_db
from aston.qtgui.TableFile import FileTreeModel
from aston.qtgui.MenuOptions import peak_models
from aston.spectra.Isotopes import delta13C_constants
from aston.database.User import User


class SettingsWidget(QtWidgets.QWidget):
    def __init__(self, parent=None, db=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.parent = parent
        self.db = db

        if db is None:
            return

        self.load_opts()
        self.ui.pushButtonCopyDB.clicked.connect(self.load_other_db)

        # set up the isotope combo boxes
        m = ['santrock', 'craig']
        idx = m.index(self.get_key('d13c_method', 'santrock'))
        self.ui.comboIsotopeMethod.setCurrentIndex(idx)
        self.ui.comboIsotopeMethod.activated.connect(self.set_isotope)

        ks = [k for k in delta13C_constants()]
        idx = ks.index(self.get_key('d13c_const', 'Santrock'))
        self.ui.comboIsotopeKs.setCurrentIndex(idx)
        self.ui.comboIsotopeKs.activated.connect(self.set_isotope)

        # fill out the leastsq integration peak model combobox
        self.ui.comboLeastSqPeakModel.addItems( \
            [m for m in peak_models if peak_models[m] is not None])
        pkmod = self.get_key('integrate_leastsq_f', dflt='gaussian')
        ci = [peak_models[m] for m in peak_models].index(pkmod) - 1
        self.ui.comboLeastSqPeakModel.setCurrentIndex(ci)
        self.ui.comboLeastSqPeakModel.activated.connect(self.set_lsqmod)

        self.ui.btnOpenCompoundDB.clicked.connect(self.load_cmpd_db)
        self.ui.lineCompoundDB.setText(self.get_key('db_compound', dflt=''))
        self.ui.btnOpenMethodDB.clicked.connect(self.load_meth_db)
        self.ui.lineMethodDB.setText(self.get_key('db_method', dflt=''))

    def set_lsqmod(self):
        ci = self.ui.comboLeastSqPeakModel.currentIndex()
        pkmod = [peak_models[m] for m in peak_models][ci + 1]
        self.set_key('integrate_leastsq_f', pkmod)

    def set_isotope(self):
        m = ['santrock', 'craig'][self.ui.comboIsotopeMethod.currentIndex()]
        self.set_key('d13c_method', m)

        d13c_k_opts = [ks for ks in delta13C_constants()]
        ks = d13c_k_opts[self.ui.comboIsotopeKs.currentIndex()]
        self.set_key('d13c_const', ks)

    def numeric_opts(self):
        k_to_b = {'peakfind_simple_startslope': self.ui.doubleSimpleStartSlope,
                  'peakfind_simple_initslope': self.ui.doubleSimpleInitSlope,
                  'peakfind_simple_endslope': self.ui.doubleSimpleEndSlope,
                  'peakfind_simple_maxwidth': self.ui.doubleSimpleMaxPeakWidth,
                  'peakfind_simple_minheight': self.ui.doubleSimpleMinPeakHgt,
                  'peakfind_wavelet_minsnr': self.ui.doubleWaveletMinSNR,
                  'peakfind_wavelet_asssig': self.ui.doubleWaveletAssSig,
                  'peakfind_wavelet_gapthresh': self.ui.doubleWaveletGapThresh,
                  'peakfind_wavelet_maxdist': self.ui.doubleWaveletMaxDist,
                  'peakfind_wavelet_minlength': self.ui.doubleWaveletMinLength,
                  'peakfind_event_adjust': self.ui.checkEventAdjust,
                  'integrate_periodic_offset': self.ui.doublePeriodicOffset,
                  'integrate_periodic_period': self.ui.doublePeriodicPeriod,
                  'db_remove_deleted': self.ui.checkDBRemoveDeleted,
                  'db_reload_on_open': self.ui.checkDBRescan,
                  'multiprocessing': self.ui.checkMultiprocessing}
        return k_to_b

    def load_opts(self):
        k_to_b = self.numeric_opts()
        for k in k_to_b:
            v = self.get_key(k, dflt=None)
            if type(k_to_b[k]) == QtWidgets.QDoubleSpinBox:
                if v is not None:
                    k_to_b[k].setValue(float(v))
                #k_to_b[k].valueChanged.connect(self.save_opts(k))
                k_to_b[k].editingFinished.connect(self.save_opts(k))
            elif type(k_to_b[k]) == QtWidgets.QCheckBox:
                if v is not None:
                    k_to_b[k].setChecked(v)
                k_to_b[k].stateChanged.connect(self.save_opts(k))

    def save_opts(self, k):
        def wrapped_f():
            k_to_b = self.numeric_opts()
            if type(k_to_b[k]) == QtGui.QDoubleSpinBox:
                self.set_key(k, str(k_to_b[k].value()))
            elif type(k_to_b[k]) == QtGui.QCheckBox:
                if k_to_b[k].isChecked():
                    self.set_key(k, True)
                else:
                    self.set_key(k, False)
            if k.startswith('peakfind_'):
                if self.parent.ui.actionGraph_Peaks_Found.isChecked():
                    self.parent.plotData(updateBounds=False)
                pass
        return wrapped_f

    def load_other_db(self):
        path = str(QtWidgets.QFileDialog.getOpenFileName(self,
          self.tr('Open DB'), '', self.tr('AstonDB (aston.sqlite)')))
        if path == '':
            return
        #other_db_vals = AstonDatabase(path).all_keys()
        #for k in other_db_vals:
        #    self.set_key(k, other_db_vals[k])

    def load_cmpd_db(self):
        #TODO: relative to DB path if possible?
        fopts = self.tr('AstonDB (*.sqlite);;AMDIS DB (*.msl)')
        path = str(QtWidgets.QFileDialog.getOpenFileName(self, \
          self.tr('Open DB'), '', fopts))
        if path == '':
            return

        self.set_key('db_compound', path)
        self.ui.lineCompoundDB.setText(path)

        #cmpd_db = get_compound_db(path)
        #self.parent.cmpd_tab = FileTreeModel(cmpd_db, \
        #                              self.parent.ui.compoundTreeView, self)

    def load_meth_db(self):
        #TODO: relative to DB path if possible?
        fopts = self.tr('AstonDB (*.sqlite);')
        path = str(QtWidgets.QFileDialog.getOpenFileName(self, \
          self.tr('Open DB'), '', fopts))
        if path == '':
            return

        self.set_key('db_method', path)
        self.ui.lineMethodDB.setText(path)

    def get_key(self, key, dflt=None):
        return self.db.query(User).first().prefs.get(key, dflt)

    def set_key(self, key, val):
        def_user = self.db.query(User).first()
        def_user.prefs[key] = val
        self.db.commit()
