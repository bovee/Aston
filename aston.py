#!/usr/bin/python2.7

#for compatibility with Python 2
import sip
sip.setapi('QVariant', 2)

#all the other imports
import sys
import PyQt4
from aston.ui.MainWindow import AstonWindow

#standard QT stuff to set up
app = PyQt4.QtGui.QApplication(sys.argv)
myapp = AstonWindow()
myapp.show()
sys.exit(app.exec_())
