#!/usr/bin/env python

from setuptools.command.test import test as TestCommand
from setuptools import setup
# import matplotlib
import os
import sys

from aston import __version__


class Tox(TestCommand):
    """
    Shim class to allow `setup.py test` to run tox
    (which in turn calls `setup.py pytest` to run tests)

    from https://testrun.org/tox/latest/example/basic.html
    """
    user_options = [('tox-args=', 'a', "Arguments to pass to tox")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.tox_args = None

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import tox
        import shlex
        args = self.tox_args
        if args:
            args = shlex.split(self.tox_args)
        errno = tox.cmdline(args=args)
        sys.exit(errno)


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
    'long_description': read('README.rst'),
    'packages': [
        'aston', 'aston.calibrations', 'aston.compat', 'aston.peak',
        'aston.spectra', 'aston.trace', 'aston.tracefile'
    ],
    'scripts': [],
    # 'data_files': matplotlib.get_py2exe_datafiles(),
    'package_data': {'aston': []},
    'include_package_data': True,
    'setup_requires': ['pytest-runner'],
    'install_requires': ['scipy', 'numpy'],
    'tests_require': ['numpy', 'scipy', 'pytest', 'tox', 'flake8'],
    'cmdclass': {'test': Tox}
}

# all the magic happens right here
setup(**options)
