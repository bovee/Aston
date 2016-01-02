from PyQt5 import QtCore, QtGui, QtWidgets
from aston.resources import tr
from aston.qtgui.ui_filterwindow import Ui_filterDialog
from aston.qtgui.Fields import aston_field_opts


class FilterWindow(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self)
        self.parent = parent
        self.ui = Ui_filterDialog()
        self.ui.setupUi(self)
        self.ui.buttonBox.clicked.connect(self.clicked)

        dt = parent.obj_tab.returnSelFile()

        #self.ui.ionList.pressed.connect(self.ionListKeyPressed)
        delAc = QtGui.QAction("Delete", self.ui.ionList, \
          shortcut=QtCore.Qt.Key_Backspace, triggered=self.deleteIon)
        self.ui.ionList.addAction(delAc)
        self.ui.ionList.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.ui.ionList.customContextMenuRequested.connect(self.iClickMenu)

        #TODO: check that all these traces exist?
        ions = ['TIC (X)', 'TIME (T)', 'PRES', 'TEMP', 'FLOW']
        ions += ['MPRES', 'MTEMP', 'MFLOW', 'R45STD', 'R46STD']
        self.ui.definedIonBox.addItems(ions)
        self.ui.addDefinedIonButton.clicked.connect(self.addDefIon)

        dtions = dt._ions()
        if len(dtions) < 32:
            self.ui.singleIonBox.addItems(sorted([str(i) for i in dtions]))
        self.ui.singleIonBox.setEditText('')
        self.ui.singleIonBox.isLeftToRight
        self.ui.addSingleIonButton.clicked.connect(self.addSingleIon)

        self.ui.addRangeIonButton.clicked.connect(self.addRangeIon)
        if len(dtions) > 1:
            self.ui.startRangeIonBox.setRange(min(dtions), max(dtions))
            self.ui.endRangeIonBox.setRange(min(dtions), max(dtions))

        self.ui.addUserIonButton.clicked.connect(self.addUserIon)

        #options for smoothing
        self.ui.smoothComboBox.addItems(aston_field_opts['t-smooth'])
        self.ui.smoothComboBox.currentIndexChanged.connect(self.smoothChanged)

        self.loadInfo(dt)
        self.smoothChanged()

    def loadInfo(self, dt):
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

    def ionListKeyPressed(self, evt):
        print(evt)
        pass

    def iClickMenu(self, point):
        menu = QtGui.QMenu(self.ui.ionList)

        if len(self.ui.ionList.selectedItems()) > 0:
            menu.addAction(tr('Delete'), self.deleteIon)

        if not menu.isEmpty():
            menu.exec_(self.ui.ionList.mapToGlobal(point))

    def deleteIon(self):
        for item in self.ui.ionList.selectedItems():
            self.ui.ionList.takeItem(self.ui.ionList.row(item))

    def addDefIon(self):
        #TODO: error check ion string here?
        ion = str(self.ui.definedIonBox.currentText())
        ion = ion.split('(')[0].strip()
        self.ui.ionList.addItem(ion)

    def addSingleIon(self):
        self.ui.ionList.addItem(self.ui.singleIonBox.currentText())

    def addRangeIon(self):
        ion_range = str(self.ui.startRangeIonBox.text()) + ':' + \
                    str(self.ui.endRangeIonBox.text())
        self.ui.ionList.addItem(ion_range)

    def addUserIon(self):
        ion_str = self.ui.userIonBox.text()
        for i in ion_str.split(','):
            self.ui.ionList.addItem(i)

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

    def clicked(self, btn):
        if btn is self.ui.buttonBox.button(self.ui.buttonBox.RestoreDefaults):
            self.ui.XOffsetBox.setValue(0.0)
            pass

    def accept(self):
        for dt in self.parent.obj_tab.returnSelFiles():
            self._updateFile(dt)
        self.close()

    def _updateFile(self, dt):
        dt.info['traces'] = ','.join([str(self.ui.ionList.item(i).text())
          for i in range(self.ui.ionList.count())])

        if self.ui.offsetBox.isChecked():
            if self.ui.XOffsetBox.value() != 0.0:
                dt.info['t-offset'] = str(self.ui.XOffsetBox.value())
            else:
                self._delInfo(dt, 't-offset')
            if self.ui.YOffsetBox.value() != 0.0:
                dt.info['t-yoffset'] = str(self.ui.YOffsetBox.value())
            else:
                self._delInfo(dt, 't-yoffset')
            if self.ui.XScaleBox.value() != 1.0:
                dt.info['t-scale'] = str(self.ui.XScaleBox.value())
            else:
                self._delInfo(dt, 't-scale')
            if self.ui.YScaleBox.value() != 1.0:
                dt.info['t-yscale'] = str(self.ui.YScaleBox.value())
            else:
                self._delInfo(dt, 't-yscale')
        else:
            for key in ['t-offset', 't-yoffset', 't-scale', 't-yscale']:
                self._delInfo(dt, key)

        if self.ui.smoothBox.isChecked():
            if self.ui.smoothComboBox.currentText() == 'None':
                for key in ['t-smooth', 't-smooth-window', 't-smooth-order']:
                    self._delInfo(dt, key)
            elif self.ui.smoothComboBox.currentText() == 'Moving Average':
                dt.info['t-smooth'] = 'moving average'
                dt.info['t-smooth-window'] = str(self.ui.smoothWindowBox.value())
                self._delInfo(dt, 't-smooth-order')
            elif self.ui.smoothComboBox.currentText() == 'Savitsky-Golay':
                dt.info['t-smooth'] = 'savitsky-golay'
                dt.info['t-smooth-window'] = str(self.ui.smoothWindowBox.value())
                dt.info['t-smooth-order'] = str(self.ui.smoothOrderBox.value())
        else:
            for key in ['t-smooth', 't-smooth-window', 't-smooth-order']:
                self._delInfo(dt, key)

        self.parent.plotData()

    def _delInfo(self, dt, key):
        try:
            del dt.info[key]
        except:
            pass

    def reject(self):
        self.close()
