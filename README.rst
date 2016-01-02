*****
Aston
*****

Aston is a cross-platform, open source program for the analysis of chromatographic data. It's named for Francis William Aston, creator of the first fully functional mass spectrometer, and written using Python, Numpy, Scipy, Matplotlib, SqlAlchemy and PyQt.

Getting Started
***************

Choose "Open Folder" from the file menu, select a directory, and Aston will load all the data files in that directory into the "Files" tab.

pyuic5 ./aston/qtgui/ui/ui_mainwindow.ui > ./aston/qtgui/ui_mainwindow.py
pyuic5 ./aston/qtgui/ui/ui_filterwindow.ui > ./aston/qtgui/ui_filterwindow.py
pyuic5 ./aston/qtgui/ui/ui_quant.ui > ./aston/qtgui/ui_quant.py
pyuic5 ./aston/qtgui/ui/ui_settings.ui > ./aston/qtgui/ui_settings.py
