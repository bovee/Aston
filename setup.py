#!/usr/bin/env python

#    Copyright 2011-2013 Roderick Bovee
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

from setuptools import setup
from glob import glob
import matplotlib
import sys
import os


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

options = {
    'name': 'Aston',
    'version': '0.6.4a',
    'description': 'Mass/UV Spectral Analysis Program',
    'author': 'Roderick Bovee',
    'author_email': 'bovee@fas.harvard.edu',
    'url': 'http://code.google.com/p/aston',
    'license': 'GPLv3',
    'platforms': ['Any'],
    'classifiers': [
        'Development Status :: 4 - Beta',
        'Environment :: X11 Applications :: Qt',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
        'Topic :: Scientific/Engineering :: Chemistry'
    ],
    'long_description': read('README.rst'),
    'packages': ['aston', 'aston.ui', 'aston.databases', 'aston.features', \
                 'aston.file_adapters', 'aston.peaks', 'aston.spectra', \
                 'aston.test', 'aston.timeseries'],
    'scripts': ['astonx.py'],
    'data_files': matplotlib.get_py2exe_datafiles(),
    'package_data': {'aston': \
      ['i18n/*.qm', 'ui/icons/*.png']},
    'include_package_data': True,
    'install_requires': ['numpy', 'scipy', 'matplotlib'],
    'test_suite': 'nose.collector'
}

if len(sys.argv) >= 2 and sys.argv[1] == 'py2exe':
    #setup the distutils stuff
    try:
        import py2exe
    except ImportError:
        print('Could not import py2exe. Windows exe could not be built.')
        sys.exit(0)

    options['windows'] = ['astonx.py']
    # scipy...._validation is only needed because of bug in scipy
    #options['data_files'] += [('Microsoft.VC90.CRT', \
    #      glob(r'C:\Program Files\Microsoft Visual Studio 9.0' + \
    #      r'\VC\redist\x86\Microsoft.VC90.CRT\*.*'))]
    options['data_files'] += [(r'aston\i18n', \
      glob(os.path.abspath(r'aston\i18n\*.qm')))]
    options['data_files'] += [(r'aston\ui\icons', \
      glob(os.path.abspath(r'aston\ui\icons\*.png')))]
    options['zipfile'] = None
    options['options'] = {
        'py2exe': {'skip_archive': False,
        'bundle_files': 2,
        'compressed': True,
        'optimize': '2',
        'dll_excludes': ['MSVCP90.dll', 'tcl85.dll', 'tk85.dll', 'w9xpopen.exe'],
        'includes': ['sip', 'scipy.sparse.csgraph._validation', 'scipy.io.matlab.streams'],
        'excludes': ['_gtkagg', '_tkagg', 'tcl', 'Tkconstants', 'Tkinter']}
    }

    #clean up stuff
    os.system('rmdir dist /s /q')
    os.system('rmdir build /s /q')
    os.system('rmdir dist_win /s /q')

elif len(sys.argv) >= 2 and sys.argv[1] == 'py2app':
    #setup the distutils stuff
    try:
        import py2app
    except ImportError:
        print('Could not import py2app. Mac bundle could not be built.')
        sys.exit(0)

    options['app'] = ['astonx.py']
    options['setup_requires'] = ['py2app']
    options['iconfile'] = 'aston/ui/icons/logo.icns'
    options['data_files'] += [('aston/i18n', \
      glob(os.path.abspath('aston/i18n/*.qm')))]
    options['data_files'] += [('aston/ui/icons', \
      glob(os.path.abspath('aston/ui/icons/*.png')))]
    options['options'] = {'py2app': {
        'argv_emulation': False,
        'includes': ['sip', 'PyQt4', 'PyQt4.QtCore', \
          'PyQt4.QtGui', 'matplotlib', 'numpy', 'scipy'],
        'excludes': ['PyQt4.QtDesigner', 'PyQt4.QtNetwork', \
          'PyQt4.QtOpenGL', 'PyQt4.QtScript', 'PyQt4.QtSql', \
          'PyQt4.QtTest', 'PyQt4.QtWebKit', 'PyQt4.QtXml', \
          'PyQt4.phonon', 'PyQt4.QtHelp', 'PyQt4.QtMultimedia', \
          'PyQt4.QtXmlPatterns', 'matplotlib.tests', 'scipy.weave']
    }}

    #clean up stuff
    os.system('rm -rf build')

#all the magic happens right here
setup(**options)

if len(sys.argv) >= 2 and sys.argv[1] == 'py2exe':
    os.system('rmdir build /s /q')
    os.system('rmdir dist\\mpl-data\\sample_data /s /q')
    os.system('copy platform\\win\\*.ico dist\\aston\\ui\\icons\\')
    #TODO: create the Microsoft.VC90.CRT folder and copy the DLLs
    # and manifest into it
    #TODO: run the aston.nsi
elif len(sys.argv) >= 2 and sys.argv[1] == 'py2app':
    os.system('rm -rf build')
    os.system('cp -rf platform/mac/qt_menu.nib dist/Aston.app/Contents/Resources/')
    os.system('cp platform/mac/qt.conf dist/Aston.app/Contents/Resources/')
    os.system('cp platform/mac/logo.icns dist/Aston.app/Contents/Resources/PythonApplet.icns')
    os.system('rm -rf dist/Aston.app/Contents/Resources/mpl-data/sample_data')
    os.system('rm -rf dist/Aston.app/Contents/Resources/lib/python2.7/matplotlib/tests')
    os.system('rm -rf dist/Aston.app/Contents/Resources/lib/python2.7/scipy/weave')
    os.system('rm -rf dist/Aston.app/Contents/Resources/lib/python2.7/matplotlib/mpl-data')
    # Delete the following directories
    #/Content/Resources/lib/python2.7/matplotlib/testing
    #/Content/Resources/lib/python2.7/scipy/spatial/tests
    #/Content/Resources/lib/python2.7/email/test
    #/Content/Frameworks/QtXmlPatterns.framework
    #/Content/Frameworks/QtNetwork.framework
    #/Content/Frameworks/QtScript.framework
    #/Content/Frameworks/QtScriptTools.framework
    ##TODO: remove stuff from "dist/Aston.app/Contents/Resources/lib/python2.7"
    ##matplotlib.tests, scipy.weave, numpy.f2py
    ##libQtNetwork.4.dylib, libQtXmlPatterns.4.dylib, libtcl8.5.dylib
    ##libtk8.dylib, libQtDeclarative.dylib, libQtScript, libQtScriptTools
    ##libQtSql, libX11

    #The following doesn't seem to work?
    #os.system('rm -rf dist_mac')
    #os.system('mkdir dist_mac')
    #os.system('hdiutil create -fs HFS+ -volname "Aston" -srcfolder dist dist_mac/Aston.dmg')
