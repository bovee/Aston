from PyQt4 import QtGui
from aston_filterwindow_ui import Ui_filterDialog

class FilterWindow(QtGui.QWidget):
    def __init__(self,parent=None):
        QtGui.QWidget.__init__(self)
        self.parent = parent
        self.ui = Ui_filterDialog()
        self.ui.setupUi(self)
        self.ui.buttonBox.clicked.connect(self.clicked)
        #self.ui.addDefinedIonButton.clicked.connect(self.addDefIon)
        #self.ui.addSingleIonButton.clicked.connect(self.addSingIon)
        #self.ui.addRangeIonButton.clicked.connect(self.addRangeIon)
        #self.ui.addUserIonButton.clicked.connect(self.addUserIon)
        self.ui.smoothComboBox.addItems(['None','Moving Average','Savitsky-Golay'])
        self.ui.smoothComboBox.currentIndexChanged.connect(self.smoothChanged)

        self.loadInfo(parent.ftab_mod.returnSelFile())
        self.smoothChanged()

    def loadInfo(self,dt):
        #transfer the ion list
        for i in dt.info['traces'].split(','):
            self.ui.ionList.addItem(i)

        #transfer the scaling/offset values
        offBoxOn = False
        if 't-scale' in dt.info:
            self.ui.XScaleBox.setValue(float(dt.info['t-scale']))
            offBoxOn = True
        else:
            self.ui.XScaleBox.setValue(1.0)
        if 't-yscale' in dt.info:
            self.ui.YScaleBox.setValue(float(dt.info['t-yscale']))
            offBoxOn = True
        else:
            self.ui.YScaleBox.setValue(1.0)
        if 't-offset' in dt.info:
            self.ui.XOffsetBox.setValue(float(dt.info['t-offset']))
            offBoxOn = True
        else:
            self.ui.XOffsetBox.setValue(0.0)
        if 't-yoffset' in dt.info:
            self.ui.YOffsetBox.setValue(float(dt.info['t-yoffset']))
            offBoxOn = True
        else:
            self.ui.YOffsetBox.setValue(0.0)
        self.ui.offsetBox.setChecked(offBoxOn)
        #transfer the smoothing values
        if 't-smooth' in dt.info:
            self.ui.smoothBox.setChecked(True)
            if dt.info['t-smooth'] == 'moving average':
                self.ui.smoothComboBox.setCurrentIndex(1)
            elif dt.info['t-smooth'] == 'savitsky-golay':
                self.ui.smoothComboBox.setCurrentIndex(2)
            else:
                self.ui.smoothComboBox.setCurrentIndex(0)
            if 't-smooth-window' in dt.info:
                self.ui.smoothWindowBox.setValue(int(dt.info['t-smooth-window']))
            else:
                pass
            if 't-smooth-order' in dt.info:
                self.ui.smoothOrderBox.setValue(int(dt.info['t-smooth-order']))
            else:
                pass
        else:
            pass
        #transfer the noise removal values
        if 't-remove-noise' in dt.info:
            self.ui.noiseBox.setChecked(True)
        else:
            pass

    def smoothChanged(self):
        if self.ui.smoothComboBox.currentText() == 'None':
            self.ui.label_2.setEnabled(False)
            self.ui.smoothWindowBox.setEnabled(False)
            self.ui.label_3.setEnabled(False)
            self.ui.smoothOrderBox.setEnabled(False)
        elif self.ui.smoothComboBox.currentText() == 'Moving Average':
            self.ui.label_2.setEnabled(True)
            self.ui.smoothWindowBox.setEnabled(True)
            self.ui.label_3.setEnabled(False)
            self.ui.smoothOrderBox.setEnabled(False)
        elif self.ui.smoothComboBox.currentText() == 'Savitsky-Golay':
            self.ui.label_2.setEnabled(True)
            self.ui.smoothWindowBox.setEnabled(True)
            self.ui.label_3.setEnabled(True)
            self.ui.smoothOrderBox.setEnabled(True)
    
    def clicked(self,btn):
        if btn is self.ui.buttonBox.button(self.ui.buttonBox.RestoreDefaults):
            self.ui.XOffsetBox.setValue(0.0)
            pass

    def accept(self):
        for dt in self.parent.ftab_mod.returnSelFiles():
            self._updateFile(dt)
        self.close()

    def _updateFile(self,dt):
        if self.ui.offsetBox.isChecked():
            if self.ui.XOffsetBox.value() != 0.0:
                dt.info['t-offset'] = str(self.ui.XOffsetBox.value())
            else:
                self._delInfo(dt,'t-offset')
            if self.ui.YOffsetBox.value() != 0.0:
                dt.info['t-yoffset'] = str(self.ui.YOffsetBox.value())
            else:
                self._delInfo(dt,'t-yoffset')
            if self.ui.XScaleBox.value() != 1.0:
                dt.info['t-scale'] = str(self.ui.XScaleBox.value())
            else:
                self._delInfo(dt,'t-scale')
            if self.ui.YScaleBox.value() != 1.0:
                dt.info['t-yscale'] = str(self.ui.YScaleBox.value())
            else:
                self._delInfo(dt,'t-yscale')
        else:
            for key in ['t-offset','t-yoffset','t-scale','t-yscale']:
                self._delInfo(dt,key)

        if self.ui.smoothBox.isChecked():
            if self.ui.smoothComboBox.currentText() == 'None':
                for key in ['t-smooth','t-smooth-window','t-smooth-order']:
                    self._delInfo(dt,key)
            elif self.ui.smoothComboBox.currentText() == 'Moving Average':
                dt.info['t-smooth'] = 'moving average'
                dt.info['t-smooth-window'] = str(self.ui.smoothWindowBox.value())
                self._delInfo(dt,'t-smooth-order')
            elif self.ui.smoothComboBox.currentText() == 'Savitsky-Golay':
                dt.info['t-smooth'] = 'savitsky-golay'
                dt.info['t-smooth-window'] = str(self.ui.smoothWindowBox.value())
                dt.info['t-smooth-order'] = str(self.ui.smoothOrderBox.value())
                pass
        else:
            for key in ['t-smooth','t-smooth-window','t-smooth-order']:
                self._delInfo(dt,key)

        self.parent.plotData()

    def _delInfo(self,dt,key):
        try: del dt.info[key]
        except: pass

    def reject(self):
        self.close()
