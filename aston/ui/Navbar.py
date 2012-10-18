import time
import os.path as op
from PyQt4 import QtGui, QtCore
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg

from aston.Features import Peak

class AstonNavBar(NavigationToolbar2QTAgg):
    def __init__(self, canvas, parent=None):
        NavigationToolbar2QTAgg.__init__(self, canvas, parent, False)
        self.parent = parent
        self.ev_time = 0
        self._xypress = []

        #remove the plot adjustment buttons
        self.removeAction(self.actions()[-1])
        self.removeAction(self.actions()[-1])
        self.removeAction(self.actions()[-1])

        #add the alignment tool
        path = op.join(op.curdir,'aston','ui','icons','align.png')
        alignToolAct = QtGui.QAction(QtGui.QIcon(path), \
                                         'Align Chromatogram', self)
        self.addAction(alignToolAct)
        alignToolAct.triggered.connect(self.align)

        self.addSeparator()

        #add the peak tool
        path = op.join(op.curdir,'aston','ui','icons','peak.png')
        peakToolAct = QtGui.QAction(QtGui.QIcon(path), \
                                    'Add/Delete Peak', self)
        self.addAction(peakToolAct)
        peakToolAct.triggered.connect(self.peak)

        #add the spectra tool
        path = op.join(op.curdir,'aston','ui','icons','spectrum.png')
        specToolAct = QtGui.QAction(QtGui.QIcon(path), \
                                        'Get Spectrum', self)
        self.addAction(specToolAct)
        specToolAct.triggered.connect(self.spec)

    def peak(self, *args):
        self._active = 'PEAK'

        self.disconnect_all()
        #if self._active:
        self._idPress = self.canvas.mpl_connect( \
            'button_press_event', self.press_peak)
        self._idRelease = self.canvas.mpl_connect( \
            'button_release_event', self.release_peak)
        self.mode = 'peak'
        #self.canvas.widgetlock(self)
        #else:
        #    self.canvas.widgetlock.release(self)

        for a in self.canvas.figure.get_axes():
            a.set_navigate_mode(self._active)

        self.set_message(self.mode)

    def press_peak(self,event):
        if event.button != 1: return
        self._xypress = event.xdata, event.ydata

    def release_peak(self,event):
        if event.button != 1: return
        dt = self.parent.obj_tab.returnSelFile()
        if dt is None:
            return
        if dt.db_type != 'file' or dt.getInfo('vis') == 'n':
            return
        if time.time() - self.ev_time < 1:
            self.ev_time = time.time()
            if abs(self._xypress[0] - event.xdata) > 0.01:
                return
            for pk in dt.getAllChildren('peak'):
                if pk.contains(event.xdata, event.ydata):
                    self.parent.obj_tab.delObjects([pk])
                    break
        else:
            self.ev_time = time.time()
            if abs(self._xypress[0] - event.xdata) < 0.01:
                return
            ion = dt.getInfo('traces').split(',')[0]

            if self._xypress[0] < event.xdata:
                pt1 = (self._xypress[0], self._xypress[1])
                pt2 = (event.xdata, event.ydata)
            else:
                pt1 = (event.xdata, event.ydata)
                pt2 = (self._xypress[0], self._xypress[1])

            verts = [pt1]
            tme = dt.time(pt1[0], pt2[0])
            verts += zip(tme, dt.trace(ion, pt1[0], pt2[0]))
            verts += [pt2]

            info = {'p-type':'Sample', 'p-created':'manual','p-int':'manual'}
            info['name'] = '{:.2f}-{:.2f}'.format(pt1[0], pt2[0])
            info['p-ion'] = ion
            pk = Peak(dt.db, None, dt.db_id, info, verts)
            self.parent.obj_tab.addObjects(dt, [pk])
            dt.delInfo('s-peaks')

        self._xypress = []
        self.release(event)

    def align(self,*args):
        self._active = 'ALIGN'

        self.disconnect_all()

        #if self._active:
        self._idPress = self.canvas.mpl_connect( \
            'button_press_event', self.press_align)
        self._idDrag = self.canvas.mpl_connect( \
            'motion_notify_event', self.drag_align)
        self._idRelease = self.canvas.mpl_connect( \
            'button_release_event', self.release_align)
        self.mode = 'align'
        #self.canvas.widgetlock(self)
        #else:
        #    self.canvas.widgetlock.release(self)

        for a in self.canvas.figure.get_axes():
            a.set_navigate_mode(self._active)

        self.set_message(self.mode)

    def press_align(self,event):
        dt = self.parent.obj_tab.returnSelFile()
        if dt is None: return
        if dt.db_type != 'file' or dt.getInfo('vis') == 'n': return
        if event.button == 1:
            try: x = float(dt.getInfo('t-offset')) - event.xdata
            except: x = 0 - event.xdata
            try: y = float(dt.getInfo('t-yoffset')) - event.ydata
            except: y = 0 - event.ydata
        elif event.button == 3:
            try: x = float(dt.getInfo('t-scale')) / event.xdata
            except: x = 1 / event.xdata
            try: y = float(dt.getInfo('t-yscale')) / event.ydata
            except: y = 1 / event.ydata
        self._xypress = x,y

    def drag_align(self,event):
        if self._xypress is []: return
        if event.xdata is None or event.ydata is None: return
        dt = self.parent.obj_tab.returnSelFile()
        if dt is None: return
        if event.button == 1:
            dt.info['t-offset'] = str(self._xypress[0] + event.xdata)
            dt.info['t-yoffset'] = str(self._xypress[1] + event.ydata)
        elif event.button == 3:
            dt.info['t-scale'] = str(self._xypress[0] * event.xdata)
            dt.info['t-yscale'] = str(self._xypress[1] * event.ydata)
        self.parent.plotData(updateBounds=False)

    def release_align(self,event):
        if self._xypress is None: return
        dt = self.parent.obj_tab.returnSelFile()
        dt.saveChanges()
        self._xypress = []
        self.release(event)

    def spec(self, *args):
        self._active = 'SPECTRUM'

        self.disconnect_all()
        self._idPress = self.canvas.mpl_connect( \
            'button_press_event', self.press_spectrum)
        self._idRelease = self.canvas.mpl_connect( \
            'button_release_event', self.release_spectrum)
        self.mode = 'spectrum'

        for a in self.canvas.figure.get_axes():
            a.set_navigate_mode(self._active)

        self.set_message(self.mode)

    def press_spectrum(self, event):
        if event.button != 1: return
        #TODO: enable spectra collection over a range

    def release_spectrum(self, event):
        if event.button != 1: return
        #TODO: figure out how to make shift-click save to database
        #get the specral data of the current point
        cur_file = self.parent.obj_tab.returnSelFile()
        if cur_file is None: return
        if cur_file.getInfo('vis') != 'y': return
        scan = cur_file.scan(event.xdata)

        self.parent.specplotter.addSpec(scan)
        self.parent.specplotter.plotSpec()
        self.parent.specplotter.specTime = event.xdata

        # draw a line on the main plot for the location
        self.parent.plotter.drawSpecLine(event.xdata, linestyle='-')

    def disconnect_all(self):
        if self._idPress is not None:
            self._idPress = self.canvas.mpl_disconnect(self._idPress)
        if self._idDrag is not None:
            self._idDrag = self.canvas.mpl_disconnect(self._idDrag)
        if self._idRelease is not None:
            self._idRelease = self.canvas.mpl_disconnect(self._idRelease)
        self.mode = ''
