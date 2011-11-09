from PyQt4 import QtGui

class FilterWindow(QtGui.QWidget):
    def __init__(self,parent=None):
        from aston_filterwindow_ui import Ui_filterDialog
        QtGui.QWidget.__init__(self)
        self.parent = parent
        self.ui = Ui_filterDialog()
        self.ui.setupUi(self)
        self.loadInfo(parent.ftab_mod.returnSelFile())

    def loadInfo(self,dt):
        #transfer the ion list

        #transfer the scaling/offset values
        if 'scale' in dt.info:
            self.ui.XScaleBox.setValue(float(dt.info['scale']))
        else:
            self.ui.XScaleBox.setValue(1.0)
        if 'yscale' in dt.info:
            self.ui.YScaleBox.setValue(float(dt.info['yscale']))
        else:
            self.ui.YScaleBox.setValue(1.0)
        if 'offset' in dt.info:
            self.ui.XOffsetBox.setValue(float(dt.info['offset']))
        else:
            self.ui.XOffsetBox.setValue(0.0)
        if 'yoffset' in dt.info:
            self.ui.YOffsetBox.setValue(float(dt.info['yoffset']))
        else:
            self.ui.YOffsetBox.setValue(0.0)
        #transfer the smoothing values
        if 'smooth' in dt.info:
            if 'smooth window' in dt.info:
                pass
            else:
                pass
            if 'smooth order' in dt.info:
                pass
            else:
                pass
        else:
            pass
        #transfer the noise removal values
        if 'remove noise' in dt.info:
            pass
        else:
            pass

    def accept(self):
        self.close()

    def reject(self):
        self.close()
