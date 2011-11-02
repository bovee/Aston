from distutils.core import setup
import py2exe, matplotlib

setup(name='Aston',
      version='0.1 alpha',
      description='Mass/UV Spectral Analysis Program',
      author='Roderick Bovee',
      author_email='bovee@fas.harvard.edu',
      packages=["aston","aston.ui"],
      scripts=['aston.py'],
      windows=['aston.py'],
      data_files=matplotlib.get_py2exe_datafiles(),
      options={'py2exe':{"skip_archive": False, "dll_excludes":["MSVCP90.dll"], "includes": ['sip']}} #,"includes": ["sip","PyQt4.QtGui"]}}
     )
