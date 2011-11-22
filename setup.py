#inspired by http://warp.byu.edu/site/content/128
from distutils.core import setup
import matplotlib
import sys, os

options = {
    'name':'Aston',
    'version':'0.1.1a',
    'description':'Mass/UV Spectral Analysis Program',
    'author':'Roderick Bovee',
    'author_email':'bovee@fas.harvard.edu',
    'url':'http://code.google.com/p/aston',
    'packages':['aston','aston.ui'],
    'scripts':['aston.py'],
    'data_files':matplotlib.get_py2exe_datafiles(),
}

if len(sys.argv) >= 2 and sys.argv[1] == 'py2exe':
    #setup the distutils stuff
    try:
        import py2exe
    except ImportError:
        print 'Could not import py2exe. Windows exe could not be built.'
        sys.exit(0)

    options['windows'] = ['aston.py']
    options['options'] = {
        'py2exe':{'skip_archive': False,
        'dll_excludes':['MSVCP90.dll','tcl85.dll','tk85.dll'],
        'includes':['sip'],
        'excludes':['_gtkagg','_tkagg','tcl','Tkconstants','Tkinter']}
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
        print 'Could not import py2app. Mac bundle could not be built.'
        sys.exit(0)

    options['app'] = ['aston.py']
    options['setup_requires'] = ['py2app']
    options['options'] = {'py2app':{
        'argv_emulation':False,
        'includes':['sip','PyQt4','PyQt4.QtCore','PyQt4.QtGui','matplotlib','numpy','scipy'],
        'excludes':['PyQt4.QtDesigner','PyQt4.QtNetwork','PyQt4.QtOpenGL','PyQt4.QtScript','PyQt4.QtSql','PyQt4.QtTest','PyQt4.QtWebKit','PyQt4.QtXml','PyQt4.phonon','PyQt4.QtHelp','PyQt4.QtMultimedia','PyQt4.QtXmlPatterns','matplotlib.tests','scipy.weave']
    }}

    #clean up stuff
    os.system('rm -rf build')

print options

#all the magic happens right here
setup(**options)

if len(sys.argv) >= 2 and sys.argv[1] == 'py2exe':
    #TODO: test this out
    #os.system('copy c:\\python27\\lib\\site-packages\\wx-2.8-msw-unicode\\wx\\MSVCP71.dll dist\\')
    os.system('rmdir build /s /q')
    os.system('mkdir dist\\aston')
    os.system('mkdir dist\\aston\\ui')
    os.system('mkdir dist\\aston\\ui\\icons')
    os.system('copy aston\\ui\\icons\\*.png dist\\aston\\ui\\icons\\')
    #TODO: create an install wizard
elif len(sys.argv) >= 2 and sys.argv[1] == 'py2app':
    os.system('rm -rf build')
    os.system('cp -rf data/dist-files/qt_menu.nib dist/Aston.app/Contents/Resources/')
    os.system('cp data/dist-files/qt.conf dist/Aston.app/Contents/Resources/')
    os.system('mkdir dist/Aston.app/Contents/Resources/aston')
    os.system('mkdir dist/Aston.app/Contents/Resources/aston/ui')
    os.system('mkdir dist/Aston.app/Contents/Resources/aston/ui/icons')
    os.system('copy aston/ui/icons/*.png dist/Aston.app/Contents/Resources/aston/ui/icons/')
    #remove stuff from "dist/Aston.app/Contents/Resources/lib/python2.7"
    #matplotlib.tests and scipy.weave
    #remove other stuff from package

    #The following doesn't seem to work?
    #os.system('rm -rf dist_mac')
    #os.system('mkdir dist_mac')
    #os.system('hdiutil create -fs HFS+ -volname "Aston" -srcfolder dist dist_mac/Aston.dmg')
