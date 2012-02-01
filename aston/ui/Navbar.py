from PyQt4 import QtGui, QtCore
import os.path as op
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg
import time
from aston.Features import Peak

class AstonNavBar(NavigationToolbar2QTAgg):
    def __init__(self, canvas, parent=None):
        NavigationToolbar2QTAgg.__init__(self,canvas,parent,False)
        self.parent = parent
        self.ev_time = 0
        self._xypress = None
        
        #add the peak tool
        #TODO: this next path doesn't work on Windows?
        pkpath = op.join(op.curdir,'aston','ui','icons','peak.png')
        peakToolAct = QtGui.QAction(QtGui.QIcon(pkpath),'Add/Delete Peak',self)
        self.insertAction(self.actions()[4],peakToolAct)
        self.connect(peakToolAct, QtCore.SIGNAL('triggered()'), self.peak)

        #add the alignment tool
        pkpath = op.join(op.curdir,'aston','ui','icons','align.png')
        alignToolAct = QtGui.QAction(QtGui.QIcon(pkpath),'Align Chromatogram',self)
        self.insertAction(self.actions()[4],alignToolAct)
        self.connect(alignToolAct, QtCore.SIGNAL('triggered()'), self.align)

    def peak(self, *args):
        #most of this code is copied from matplotlib
        #if self._active == 'PEAK': self._active = None
        #else:
        self._active = 'PEAK'

        if self._idPress is not None:
            self._idPress = self.canvas.mpl_disconnect(self._idPress)
            self.mode = ''

        if self._idRelease is not None:
            self._idRelease = self.canvas.mpl_disconnect(self._idRelease)
            self.mode = ''

        if self._active:
            self._idPress = self.canvas.mpl_connect(
                'button_press_event', self.press_peak)
            self._idRelease = self.canvas.mpl_connect(
                'button_release_event', self.release_peak)
            self.mode = 'peak'
            self.canvas.widgetlock(self)
        else:
            self.canvas.widgetlock.release(self)

        for a in self.canvas.figure.get_axes():
            a.set_navigate_mode(self._active)

        self.set_message(self.mode)

    def press_peak(self,event):
        self._xypress = event.xdata, event.ydata

    def release_peak(self,event):
        if time.time() - self.ev_time < 1:
            self.ev_time = time.time()
            if abs(self._xypress[0] - event.xdata) > 0.01: return
            pks = self.parent.ptab_mod.findPeak(event.xdata,event.ydata)
            if len(pks) == 0: return
            self.parent.ptab_mod.delFeat(pks[0])
        else:
            self.ev_time = time.time()
            if abs(self._xypress[0] - event.xdata) < 0.01: return

            dt = self.parent.ftab_mod.returnSelFile()
            ion = dt.getInfo('traces').split(',')[0]
            
            if self._xypress[0] < event.xdata:
                pt1, pt2 = (self._xypress[0], self._xypress[1]), (event.xdata, event.ydata)
            else:
                pt1, pt2 = (event.xdata, event.ydata), (self._xypress[0], self._xypress[1])
            
            verts = [pt1]
            verts += zip(dt.time(pt1[0],pt2[0]),dt.trace(ion,pt1[0],pt2[0]))
            verts += [pt2]
            pk = Peak(verts,None,ion)
            pk.ids[2] = dt.fid[1]
            pk.dt = dt
            self.parent.ptab_mod.addFeats([pk])
            dt.delInfo('s-peaks')

        #self.draw()
        self._xypress = None
        self.release(event)

    def align(self,*args):
        self._active = 'ALIGN'

        if self._idPress is not None:
            self._idPress = self.canvas.mpl_disconnect(self._idPress)
            self.mode = ''

        if self._idRelease is not None:
            self._idRelease = self.canvas.mpl_disconnect(self._idRelease)
            self.mode = ''

        if self._active:
            self._idPress = self.canvas.mpl_connect(
                'button_press_event', self.press_align)
            self._idDrag = self.canvas.mpl_connect(
                'motion_notify_event', self.drag_align)
            self._idRelease = self.canvas.mpl_connect(
                'button_release_event', self.release_align)
            self.mode = 'align'
            self.canvas.widgetlock(self)
        else:
            self.canvas.widgetlock.release(self)

        for a in self.canvas.figure.get_axes():
            a.set_navigate_mode(self._active)

        self.set_message(self.mode)

    def press_align(self,event):
        dt = self.parent.ftab_mod.returnSelFile()
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
        if self._xypress is None: return
        if event.xdata is None or event.ydata is None: return
        dt = self.parent.ftab_mod.returnSelFile()
        if event.button == 1:
            dt.info['t-offset'] = str(self._xypress[0] + event.xdata)
            dt.info['t-yoffset'] = str(self._xypress[1] + event.ydata)
        elif event.button == 3:
            dt.info['t-scale'] = str(self._xypress[0] * event.xdata)
            dt.info['t-yscale'] = str(self._xypress[1] * event.ydata)
        self.parent.plotData(updateBounds=False)

    def release_align(self,event):
        if self._xypress is None: return
        dt = self.parent.ftab_mod.returnSelFile()
        dt.saveChanges()
        self._xypress = None
        self.release(event)
