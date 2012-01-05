from PyQt4 import QtCore, QtGui
from matplotlib.path import Path
import matplotlib.patches as patches

from aston.Peak import Compound

class PeakTreeModel(QtCore.QAbstractItemModel):
    def __init__(self, database=None, treeView=None, masterWindow=None, selFiles=None, *args): 
        QtCore.QAbstractItemModel.__init__(self, *args)
        self.database = database
        self.fields = ['Name','Type']
        self.masterWindow = masterWindow

        if selFiles is None:
            self.fids = None
            self.compounds = None
        else:
            self.fids = [i.fid[1] for i in selFiles]
            self.compounds = database.getCompounds(self.fids)
        self.patches = {}
        self.drawPeaks()
        
        if treeView is not None:
            self.treeView = treeView
            treeView.setModel(self)

            #set up selections
            self.tab_sel = QtGui.QItemSelectionModel(self,treeView)
            treeView.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
            treeView.setSelectionModel(self.tab_sel)
            self.connect(self.tab_sel, QtCore.SIGNAL("selectionChanged(const QItemSelection &, const QItemSelection &)"), self.itemSelected)
    
            #set up right-clicking
            treeView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
            treeView.customContextMenuRequested.connect(self.rightClickMenu)
            treeView.header().setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
            treeView.header().customContextMenuRequested.connect(self.rightClickMenuHead)

            #prettify
            treeView.resizeColumnToContents(0)
            
    def index(self,row,column,parent):
        if not parent.isValid(): #a compound! (many peaks)
            return self.createIndex(row,column,self.compounds[row])
        else:
        #elif parent.internalPointer() is not None: #a peak!
            peak = parent.internalPointer().getPeaks(self.fids,incSpc=True)[row]
            return self.createIndex(row,column,peak)

    def parent(self,index):
        if not index.isValid():
            return QtCore.QModelIndex()
        elif type(index.internalPointer()) is Compound or index.internalPointer() is None:
            return QtCore.QModelIndex()
        else:
            cmpd_id = index.internalPointer().ids[1]
            row = [i.cmpd_id for i in self.compounds].index(cmpd_id)
            return self.createIndex(row,0,self.compounds[row])

    def rowCount(self,parent):
        if self.compounds is None: return 0
        if not parent.isValid():
            return len(self.compounds)
        elif type(parent.internalPointer()) is Compound:
            return len(parent.internalPointer().getPeaks(self.fids,incSpc=True))
        else:
            return 0

    def columnCount(self,parent):
        return len(self.fields)

    def data(self,index,role):
        rslt = None
        if not index.isValid():
            rslt = None

        fld = self.fields[index.column()].lower()

        if role != QtCore.Qt.DisplayRole: return None
        if not index.parent().isValid():
            if fld == 'name':
                rslt = index.internalPointer().name
            elif fld == 'd13c':
                rslt = str(index.internalPointer().isotopeValue())
        else:
            if index.internalPointer().ion is None:
                #it's a spectra
                if fld == 'name':
                    #TODO: add support for time() so this works
                    rslt = 'Spectra'# @ '
                    #rslt += format(index.internalPointer().time(),'.3f')
                elif fld == 'type':
                    rslt = index.internalPointer().peaktype
            else:
                #it's a peak
                if fld == 'name':
                    rslt = str(index.internalPointer().ion) + '@'
                    rslt += format(index.internalPointer().time(),'.3f')
                elif fld == 'type':
                    rslt = index.internalPointer().peaktype
                elif fld == 'area':
                    rslt = str(index.internalPointer().area())
                elif fld == 'length':
                    rslt = str(index.internalPointer().length())
                elif fld == 'height':
                    rslt = str(index.internalPointer().height())
                elif fld == 'pwhm':
                    rslt = str(index.internalPointer().length(pwhm=True))
                elif fld == 'time':
                    rslt = str(index.internalPointer().time())
        return rslt

    def headerData(self,col,orientation,role):
        rslt = None
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            rslt = self.fields[col]
        return rslt

    def setData(self,index,data,role):
        data = str(data)
        col = self.fields[index.column()].lower()
        if not index.parent().isValid():
            if col == 'name':
                index.internalPointer().name = data
                self.database.addCompound(index.internalPointer())
        self.dataChanged.emit(index,index)
        return True

    def flags(self, index):
        col = self.fields[index.column()].lower()
        dflags = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

        if not index.parent().isValid():
            if index.internalPointer().cmpd_id is not None and col == 'name':
                return dflags | QtCore.Qt.ItemIsEditable
            else:
                return dflags
        else:
            return dflags

    def itemSelected(self):
        #TODO: change the selected peak on the graph?
        tab_sel = self.treeView.selectionModel()
        if not tab_sel.currentIndex().isValid: return

        #pk = self.proxyMod.mapToSource(tab_sel.currentIndex()).internalPointer()
        pk = tab_sel.currentIndex().internalPointer()
        if pk is not None:
            if pk.ion is None:
                #it's a spectrum
                self.masterWindow.specplotter.addSpec(pk.verts,'lib')
                self.masterWindow.specplotter.plotSpec()
            else:
                #it's a peak
                pass

    def rightClickMenu(self,point):
        index = self.treeView.indexAt(point)
        menu = QtGui.QMenu(self.treeView)

        if index.isValid():
            if not index.parent().isValid():
                if index.internalPointer().cmpd_id is not None:
                    delAc = menu.addAction('Delete Compound',self._delCompoundFromMenu)
                    delAc.setData(index.internalPointer().cmpd_id)
                    spcAc = menu.addAction('Attach Current Spectrum',self._attSpcFromMenu)
                    spcAc.setData(index.internalPointer().cmpd_id)
            else:
                delAc = menu.addAction('Delete Peak',self._delPeakFromMenu)
                delAc.setData(index.internalPointer().ids[0])
                if index.internalPointer().ion is not None:
                    newAc = menu.addAction('Make New Compound',self._addCompoundFromMenu)
                    newAc.setData(index.internalPointer().ids[0])
        else:
            pass

        if not menu.isEmpty():
            menu.exec_(self.treeView.mapToGlobal(point))

    def rightClickMenuHead(self,point):
        menu = QtGui.QMenu(self.treeView)
        pos_flds = ['Type','Area','Height','Length','PWHM','Time','d13C']
        for fld in pos_flds:
            ac = menu.addAction(fld,self.rightClickMenuHeadHandler)
            ac.setCheckable(True)
            if fld in self.fields: ac.setChecked(True)
        if not menu.isEmpty(): menu.exec_(self.treeView.mapToGlobal(point))
    
    def rightClickMenuHeadHandler(self):
        fld = str(self.sender().text())
        if fld == 'Name': return
        self.beginResetModel()
        if fld in self.fields:
            self.fields.remove(fld)
        else:
            self.treeView.resizeColumnToContents(len(self.fields)-1)
            self.fields.append(fld)
        self.endResetModel()

    def _delCompoundFromMenu(self):
        cmpd_id = self.sender().data()
        self.delCompound(cmpd_id)

    def _attSpcFromMenu(self):
        cmpd_id = self.sender().data()
        dt = self.masterWindow.ftab_mod.returnSelFile()
        #FIXME: this won't match the current spectra if the user has selected something else
        for cmpd in self.compounds:
            if cmpd.cmpd_id == cmpd_id:
                #TODO: get the actual spectra
                verts = [] #spectrum
                #TODO: make the peak type MS or UV?
                pk = Peak.Peak(verts,None,'spectra')
                pk.ids[2] = dt.fid[1]
                cmpd.addPeak(pk)

    def _addCompoundFromMenu(self):
        pk_id = self.sender().data()
        pk = None
        self.beginResetModel()
        for i in self.compounds:
            for j in i.getPeaks(self.fids):
                if j.ids[0] == pk_id:
                    i.peaks.remove(j)
                    pk = j
                    break
        if pk is None: return
        self.addCompoundWithPeak(pk,'New Compound')
        self.endResetModel()
    
    def _delPeakFromMenu(self):
        pk_id = self.sender().data()
        pk = None
        for i in self.compounds:
            for j in i.peaks:
                if j.ids[0] == pk_id:
                    pk = j
                    break
        if pk is None: return
        self.delPeak(pk)        

    # The following functions are not overriden, but deal
    # with stuff in the peaks database so they're here.

    def addPatchToCanvas(self,pk):
        self.patches[pk.ids[0]] = patches.PathPatch(Path(pk.verts),facecolor='orange',lw=0)
        self.masterWindow.tplot.add_patch(self.patches[pk.ids[0]])

    def findPeak(self,x,y):
        lst = []
        for i in self.compounds:
            for j in i.getPeaks(self.fids):
                if j.contains(x,y):
                    lst.append(j)
        return lst

    def addCompoundWithPeak(self,pk,name):
        new_cmpd = Compound(name,self.database)
        self.database.addCompound(new_cmpd)
        new_cmpd.addPeak(pk)
        self.compounds = self.database.getCompounds(self.fids)

    def delCompound(self,cmpd_id):
        #delete all the patchs assigned to pks belonging to this cmpd
        #TODO: remove this code if peaks are moved to 'Unassigned'
        for cmpd in self.compounds:
            if cmpd.cmpd_id == cmpd_id:
                for peak in cmpd.peaks:
                    if peak.ion is not None:
                        patch = self.patches[peak.ids[0]]
                        self.masterWindow.tplot.patches.remove(patch)
                self.masterWindow.tcanvas.draw()
                break
            
        self.beginResetModel()
        self.database.delCompound(cmpd_id)
        self.compounds = self.database.getCompounds(self.fids)
        self.endResetModel()

    def delPeak(self,peak):
        for cmpd in self.compounds:
            if peak in cmpd.getPeaks(self.fids,incSpc=True):
                if peak.ion is not None:
                    patch = self.patches[peak.ids[0]]
                    self.masterWindow.tplot.patches.remove(patch)
                    self.masterWindow.tcanvas.draw()
                self.beginResetModel()
                if len(cmpd.getPeaks(self.fids)) == 1 and cmpd.cmpd_id is not None:
                    self.database.delCompound(cmpd.cmpd_id)
                    self.compounds = self.database.getCompounds(self.fids)
                else:
                    cmpd.delPeak(peak)
                self.endResetModel()
                break

    def addPeaks(self,pks):
        self.beginResetModel()
        for pk in pks:
            self.compounds[0].addPeak(pk)
            if pk.ion is not None:
                self.addPatchToCanvas(pk)
        self.endResetModel()
        self.masterWindow.tcanvas.draw()

    def drawPeaks(self):
        if self.compounds is None: return
        #generate the patches for peaks in the database
        for i in self.compounds:
            for j in i.getPeaks(self.fids):
                self.addPatchToCanvas(j)
        self.masterWindow.tcanvas.draw()

    def clearPatches(self):
        self.masterWindow.tplot.patches = []
        self.masterWindow.tcanvas.draw()
