#!/usr/bin/python2.7
'''Loads and runs the Aston application.'''

#for compatibility with Python 2
import sip
sip.setapi('QVariant', 2)

#all the other imports
import sys
import PyQt4
from aston.ui.MainWindow import AstonWindow

#standard QT stuff to set up
qt = PyQt4.QtGui.QApplication(sys.argv)
aston = AstonWindow()
aston.show()
sys.exit(qt.exec_())
