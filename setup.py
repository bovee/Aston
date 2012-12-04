#!/usr/bin/env python
#inspired by http://warp.byu.edu/site/content/128
#from distutils.core import setup
from setuptools import setup
import matplotlib
import sys
import os


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

options = {
    'name': 'Aston',
    'version': '0.4.0',
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
    'packages': ['aston', 'aston.ui', 'aston.Features', \
                'aston.FileFormats', 'aston.Math'],
    'scripts': ['aston.py'],
    'data_files': matplotlib.get_py2exe_datafiles(),
    'package_data': {'aston': \
      ['i18n/*.qm', 'ui/icons/*.png']},
    'include_package_data': True,
    'install_requires': ['numpy', 'scipy', 'matplotlib', 'PyQt4'],
    'test_suite': 'nose.collector'
}

if len(sys.argv) >= 2 and sys.argv[1] == 'py2exe':
    #setup the distutils stuff
    try:
        import py2exe
    except ImportError:
        print('Could not import py2exe. Windows exe could not be built.')
        sys.exit(0)

    options['windows'] = ['aston.py']
    options['options'] = {
        'py2exe': {'skip_archive': False,
        'optimize': '2',
        'dll_excludes': ['MSVCP90.dll', 'tcl85.dll', 'tk85.dll'],
        'includes': ['sip'],
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

    options['app'] = ['aston.py']
    options['setup_requires'] = ['py2app']
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

#if len(sys.argv) >= 2 and sys.argv[1] == 'py2exe':
#    os.system('rmdir build /s /q')
#    os.system('mkdir dist\\aston')
#    os.system('mkdir dist\\aston\\ui')
#    os.system('mkdir dist\\aston\\ui\\icons')
#    os.system('copy aston\\ui\\icons\\*.png dist\\aston\\ui\\icons\\')
#    #TODO: create an install wizard
#elif len(sys.argv) >= 2 and sys.argv[1] == 'py2app':
#    os.system('rm -rf build')
#    os.system('cp -rf data/dist-files/qt_menu.nib dist/Aston.app/Contents/Resources/')
#    os.system('cp data/dist-files/qt.conf dist/Aston.app/Contents/Resources/')
#    os.system('mkdir dist/Aston.app/Contents/Resources/aston')
#    os.system('mkdir dist/Aston.app/Contents/Resources/aston/ui')
#    os.system('mkdir dist/Aston.app/Contents/Resources/aston/ui/icons')
#    os.system('cp aston/ui/icons/*.png dist/Aston.app/Contents/Resources/aston/ui/icons/')
#    #TODO: remove stuff from "dist/Aston.app/Contents/Resources/lib/python2.7"
#    #matplotlib.tests, scipy.weave, numpy.f2py
#    #libQtNetwork.4.dylib, libQtXmlPatterns.4.dylib, libtcl8.5.dylib
#    #libtk8.dylib, libQtDeclarative.dylib, libQtScript, libQtScriptTools
#    #libQtSql, libX11
#
#    #The following doesn't seem to work?
#    #os.system('rm -rf dist_mac')
#    #os.system('mkdir dist_mac')
#    #os.system('hdiutil create -fs HFS+ -volname "Aston" -srcfolder dist dist_mac/Aston.dmg')
