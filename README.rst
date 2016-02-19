*****
Aston
*****

Aston is a cross-platform, open source library for the analysis of chromatographic data. It's named for Francis William Aston, creator of the first fully functional mass spectrometer, and written using Python, Numpy, and Scipy. There's also a graphical front-end available.


Installation
************

NumPy and SciPy do not install well into virtual environments ( https://gist.github.com/japsu/6064e85c33c0ff2e7ad8 ), so you may have to link your system's copies into a virtual environment if you are using one, e.g.:
    ln -s /usr/lib/python3.5/site-packages/{numpy,scipy}* venv/lib/python3.5/site-packages/
