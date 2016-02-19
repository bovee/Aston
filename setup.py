#!/usr/bin/env python

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

from setuptools import setup
import matplotlib
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
    'url': 'github.com/bovee/aston',
    'license': 'BSD 3-Clause',
    'platforms': ['Any'],
    'classifiers': [
        'Development Status :: 4 - Beta',
        'Environment :: X11 Applications :: Qt',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Topic :: Scientific/Engineering :: Chemistry'
    ],
    'long_description': read('README.rst'),
    'packages': [
        'aston', 'aston.calibrations', 'aston.compat', 'aston.peak',
        'aston.spectra', 'aston.test', 'aston.trace', 'aston.tracefile'
    ],
    'scripts': [],
    'data_files': matplotlib.get_py2exe_datafiles(),
    'package_data': {'aston': []},
    'include_package_data': True,
    'install_requires': ['numpy', 'scipy', 'matplotlib'],
    'test_suite': 'nose.collector',
}

# all the magic happens right here
setup(**options)
