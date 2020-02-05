[![Travis CI](https://travis-ci.org/bovee/Aston.svg?branch=master)](https://travis-ci.org/bovee/Aston/)


Aston
*****

Aston is a cross-platform, open source library for the analysis of chromatographic data. It's named for Francis William Aston, creator of the first fully functional mass spectrometer, and written using Python, Numpy, and Scipy. A graphical front-end is also available at https://github.com/bovee/AstonQt.


Installation
************

Although Aston still supports Python 2, I recommend using it with Python 3. Before you can use Aston, you must install Numpy and Scipy. Because these two packages contain C and Fortran code, installing via `pip` may be difficult (if you take this route, install them separately -- `pip install numpy` then `pip install scipy`) so I recommend installing them with your operating systems native facilities:

Arch: `sudo pacman -Syu python-numpy python-scipy`
Ubuntu/Debian: `sudo apt-get install python3-numpy python3-scipy`
Mac OS X: `brew install numpy` and `brew install scipy` ( you will need Homebrew for this: http://brew.sh/ )
Windows: graphical Anaconda installer @ https://www.continuum.io/downloads

Once these are installed, you can check that everything works by installing tox with `pip install tox` and then running the test suite with `tox`.

Usage
*****
```python
from aston.tracefile import TraceFile
c = TraceFile('./test.cdf')
```
