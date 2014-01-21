from PyQt4 import QtGui, QtCore
from aston.qtgui.ui_quant import Ui_Dialog

class QuantDialog(QtGui.QDialog):
    def __init__(self, parent=None, peaks=None):
        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        pass

        self.peaks = peaks
