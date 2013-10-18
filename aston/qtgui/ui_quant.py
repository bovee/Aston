# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_quant.ui'
#
# Created: Thu Jun  6 22:58:37 2013
#      by: PyQt4 UI code generator 4.10
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName(_fromUtf8("Dialog"))
        Dialog.resize(573, 431)
        self.verticalLayout_3 = QtGui.QVBoxLayout(Dialog)
        self.verticalLayout_3.setObjectName(_fromUtf8("verticalLayout_3"))
        self.toolBox = QtGui.QToolBox(Dialog)
        self.toolBox.setObjectName(_fromUtf8("toolBox"))
        self.page = QtGui.QWidget()
        self.page.setGeometry(QtCore.QRect(0, 0, 555, 309))
        self.page.setObjectName(_fromUtf8("page"))
        self.horizontalLayout = QtGui.QHBoxLayout(self.page)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.tableView = QtGui.QTableView(self.page)
        self.tableView.setObjectName(_fromUtf8("tableView"))
        self.horizontalLayout.addWidget(self.tableView)
        self.toolBox.addItem(self.page, _fromUtf8(""))
        self.page_3 = QtGui.QWidget()
        self.page_3.setGeometry(QtCore.QRect(0, 0, 555, 335))
        self.page_3.setObjectName(_fromUtf8("page_3"))
        self.verticalLayout_5 = QtGui.QVBoxLayout(self.page_3)
        self.verticalLayout_5.setObjectName(_fromUtf8("verticalLayout_5"))
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))
        self.tableView_3 = QtGui.QTableView(self.page_3)
        self.tableView_3.setObjectName(_fromUtf8("tableView_3"))
        self.horizontalLayout_3.addWidget(self.tableView_3)
        self.quantPlotLayout = QtGui.QVBoxLayout()
        self.quantPlotLayout.setObjectName(_fromUtf8("quantPlotLayout"))
        self.horizontalLayout_3.addLayout(self.quantPlotLayout)
        self.verticalLayout_5.addLayout(self.horizontalLayout_3)
        self.toolBox.addItem(self.page_3, _fromUtf8(""))
        self.page_2 = QtGui.QWidget()
        self.page_2.setGeometry(QtCore.QRect(0, 0, 555, 309))
        self.page_2.setObjectName(_fromUtf8("page_2"))
        self.verticalLayout_4 = QtGui.QVBoxLayout(self.page_2)
        self.verticalLayout_4.setObjectName(_fromUtf8("verticalLayout_4"))
        self.checkBox = QtGui.QCheckBox(self.page_2)
        self.checkBox.setObjectName(_fromUtf8("checkBox"))
        self.verticalLayout_4.addWidget(self.checkBox)
        self.line = QtGui.QFrame(self.page_2)
        self.line.setFrameShape(QtGui.QFrame.HLine)
        self.line.setFrameShadow(QtGui.QFrame.Sunken)
        self.line.setObjectName(_fromUtf8("line"))
        self.verticalLayout_4.addWidget(self.line)
        self.checkBox_2 = QtGui.QCheckBox(self.page_2)
        self.checkBox_2.setObjectName(_fromUtf8("checkBox_2"))
        self.verticalLayout_4.addWidget(self.checkBox_2)
        self.checkBox_3 = QtGui.QCheckBox(self.page_2)
        self.checkBox_3.setObjectName(_fromUtf8("checkBox_3"))
        self.verticalLayout_4.addWidget(self.checkBox_3)
        self.label_2 = QtGui.QLabel(self.page_2)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.verticalLayout_4.addWidget(self.label_2)
        self.horizontalLayout_4 = QtGui.QHBoxLayout()
        self.horizontalLayout_4.setObjectName(_fromUtf8("horizontalLayout_4"))
        self.tableView_2 = QtGui.QTableView(self.page_2)
        self.tableView_2.setObjectName(_fromUtf8("tableView_2"))
        self.horizontalLayout_4.addWidget(self.tableView_2)
        self.linearityPlotLayout = QtGui.QVBoxLayout()
        self.linearityPlotLayout.setObjectName(_fromUtf8("linearityPlotLayout"))
        self.horizontalLayout_4.addLayout(self.linearityPlotLayout)
        self.verticalLayout_4.addLayout(self.horizontalLayout_4)
        self.line_2 = QtGui.QFrame(self.page_2)
        self.line_2.setFrameShape(QtGui.QFrame.HLine)
        self.line_2.setFrameShadow(QtGui.QFrame.Sunken)
        self.line_2.setObjectName(_fromUtf8("line_2"))
        self.verticalLayout_4.addWidget(self.line_2)
        self.checkBox_4 = QtGui.QCheckBox(self.page_2)
        self.checkBox_4.setObjectName(_fromUtf8("checkBox_4"))
        self.verticalLayout_4.addWidget(self.checkBox_4)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.label = QtGui.QLabel(self.page_2)
        self.label.setObjectName(_fromUtf8("label"))
        self.horizontalLayout_2.addWidget(self.label)
        self.lineEdit = QtGui.QLineEdit(self.page_2)
        self.lineEdit.setObjectName(_fromUtf8("lineEdit"))
        self.horizontalLayout_2.addWidget(self.lineEdit)
        self.label_3 = QtGui.QLabel(self.page_2)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.horizontalLayout_2.addWidget(self.label_3)
        self.lineEdit_2 = QtGui.QLineEdit(self.page_2)
        self.lineEdit_2.setObjectName(_fromUtf8("lineEdit_2"))
        self.horizontalLayout_2.addWidget(self.lineEdit_2)
        self.verticalLayout_4.addLayout(self.horizontalLayout_2)
        self.toolBox.addItem(self.page_2, _fromUtf8(""))
        self.page_4 = QtGui.QWidget()
        self.page_4.setObjectName(_fromUtf8("page_4"))
        self.toolBox.addItem(self.page_4, _fromUtf8(""))
        self.verticalLayout_3.addWidget(self.toolBox)

        self.retranslateUi(Dialog)
        self.toolBox.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "Dialog", None))
        self.toolBox.setItemText(self.toolBox.indexOf(self.page), _translate("Dialog", "Peaks", None))
        self.toolBox.setItemText(self.toolBox.indexOf(self.page_3), _translate("Dialog", "Quant Standards", None))
        self.checkBox.setText(_translate("Dialog", "Drift (for Imported Peaks)", None))
        self.checkBox_2.setText(_translate("Dialog", "Linearity (Height)", None))
        self.checkBox_3.setText(_translate("Dialog", "Linearity (Mol. Wgt.)", None))
        self.label_2.setText(_translate("Dialog", "Linearity Correction Peaks", None))
        self.checkBox_4.setText(_translate("Dialog", "Correction for Derivitization Agent", None))
        self.label.setText(_translate("Dialog", "delta13C", None))
        self.label_3.setText(_translate("Dialog", "# of Carbons", None))
        self.toolBox.setItemText(self.toolBox.indexOf(self.page_2), _translate("Dialog", "Isotopes", None))
        self.toolBox.setItemText(self.toolBox.indexOf(self.page_4), _translate("Dialog", "Export", None))

