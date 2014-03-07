#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

#    Copyright 2011-2014 Roderick Bovee
#
#    This file is part of Aston.
#
#    Aston is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Aston is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Aston.  If not, see <http://www.gnu.org/licenses/>.

'''Loads and runs the Aston application.'''
#pylint: disable=C0103
import sys

if len(sys.argv) > 1:
    import argparse
    parser = argparse.ArgumentParser(description='Chromatogram processor.')

    parser.add_argument('-v', '--version', action='store_true')
    subp = parser.add_subparsers(dest='cmd')

    parser_gui = subp.add_parser('gui')
    parser_gui.add_argument('-d', '--directory')

    parser_conv = subp.add_parser('convert')
    parser_conv.add_argument('infile')
    parser_conv.add_argument('outfile')

    parser_plot = subp.add_parser('plot')
    parser_conv.add_argument('file')
    parser_conv.add_argument('-p', '--plotfile')

    parser_info = subp.add_parser('info')
    parser_conv.add_argument('file')

    args = parser.parse_args()

    startx = args.cmd == 'gui'
else:
    startx = True

if startx:
    #for compatibility with Python 2
    import sip
    sip.setapi('QVariant', 2)

    # to make some error messages go away
    import matplotlib
    matplotlib.use('Qt4Agg')

    import numpy
    numpy.seterr(divide='raise', invalid='raise', over='raise')

    # for multiprocessing to work on Windows
    import multiprocessing
    multiprocessing.freeze_support()

    #all the other imports
    import sys
    import PyQt4
    from aston.ui.MainWindow import AstonWindow
    qt = PyQt4.QtGui.QApplication(sys.argv)

    # translation stuff
    import locale
    import pkg_resources
    from aston.ui.resources import resfile
    try:
        locale.setlocale(locale.LC_ALL, '')
        if locale.getlocale()[0] is not None:
            lang = locale.getlocale()[0]
            tlate = PyQt4.QtCore.QTranslator(qt)
            tlate.load('aston_' + lang + '.qm', resfile('aston', 'i18n'))
            qt.installTranslator(tlate)
    except locale.Error:
        pass

    # set up the main window and start
    aston = AstonWindow()
    aston.show()
    sys.exit(qt.exec_())
