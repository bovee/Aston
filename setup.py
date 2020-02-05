#!/usr/bin/env python

from setuptools import setup
import os

from aston import __version__


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

# read in the version number
with open('aston/__init__.py') as f:
    exec(f.read())

options = {
    'name': 'Aston',
    'version': __version__,
    'description': 'Mass/UV Spectral Analysis Program',
    'author': 'Roderick Bovee',
    'author_email': 'rbovee@gmail.com',
    'url': 'https://github.com/bovee/aston',
    'license': 'BSD 3-Clause',
    'platforms': ['Any'],
    'classifiers': [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Topic :: Scientific/Engineering :: Chemistry'
    ],
    'long_description': read('README.md'),
    'packages': [
        'aston', 'aston.calibrations', 'aston.compat', 'aston.peak',
        'aston.spectra', 'aston.trace', 'aston.tracefile'
    ],
    'scripts': [],
    # 'data_files': matplotlib.get_py2exe_datafiles(),
    'package_data': {'aston': []},
    'include_package_data': True,
    'install_requires': ['numpy>=1.16.4', 'scipy>=1.2.0'],
    'extras_require': {
        'plot': ['matplotlib', 'jupyter'],
    }
}

# all the magic happens right here
setup(**options)
