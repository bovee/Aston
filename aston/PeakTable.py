from PyQt4 import QtCore, QtGui

from aston.Features import Spectrum, Peak, Compound

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

        self.masterWindow.plotter.loadCompounds(self.compounds, self.fids)
        
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
            treeView.expandAll()
            treeView.resizeColumnToContents(0)
            
    def index(self,row,column,parent):
        if not parent.isValid(): #a compound! (many peaks)
            return self.createIndex(row,column,self.compounds[row])
        else:
        #elif parent.internalPointer() is not None: #a peak!
            ft = parent.internalPointer().getFeats(self.fids)[row]
            return self.createIndex(row,column,ft)

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
            return len(parent.internalPointer().getFeats(self.fids))
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
            ft = index.internalPointer()
            if isinstance(ft, Spectrum):
                #it's a spectra
                if fld == 'name':
                    #TODO: add support for time() so this works
                    rslt = 'Spectra'# @ '
                    #rslt += format(index.internalPointer().time(),'.3f')
                elif fld == 'type':
                    rslt = ft.cls
            else:
                #it's a peak
                if fld == 'name':
                    rslt = str(ft.ion) + '@' + format(ft.time(),'.3f')
                elif fld == 'type':
                    rslt = ft.cls
                elif fld == 'area':
                    rslt = str(ft.area())
                elif fld == 'length':
                    rslt = str(ft.length())
                elif fld == 'height':
                    rslt = str(ft.height())
                elif fld == 'pwhm':
                    rslt = str(ft.length(pwhm=True))
                elif fld == 'time':
                    rslt = str(ft.time())
                elif fld == 's':
                    t = float(ft.dt.getInfo('s-peaks-en')) - \
                      float(ft.dt.getInfo('s-peaks-st'))
                    rslt = str(t / ft.length() + 1)
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

        ft = tab_sel.currentIndex().internalPointer()
        if ft is not None:
            if isinstance(ft,Spectrum):
                #it's a spectrum
                self.masterWindow.specplotter.addSpec(dict(ft.data),'lib')
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
                    delAc = menu.addAction(self.tr('Delete Compound'),
                                           self._delCompoundFromMenu)
                    delAc.setData(index.internalPointer().cmpd_id)
                    spcAc = menu.addAction(self.tr('Attach Current Spectrum'), self._attSpcFromMenu)
                    spcAc.setData(index.internalPointer().cmpd_id)
            else:
                delAc = menu.addAction(self.tr('Delete Feature'),self._delFeatFromMenu)
                delAc.setData(index.internalPointer().ids[0])
                if isinstance(index.internalPointer(), Peak):
                    newAc = menu.addAction(self.tr('Make New Compound'),self._addCompoundFromMenu)
                    newAc.setData(index.internalPointer().ids[0])
        else:
            pass

        if not menu.isEmpty():
            menu.exec_(self.treeView.mapToGlobal(point))

    def rightClickMenuHead(self,point):
        menu = QtGui.QMenu(self.treeView)
        pos_flds = ['Type','Area','Height','Length','PWHM', \
                    'Time','d13C','S']
        for fld in pos_flds:
            ac = menu.addAction(fld,self.rightClickMenuHeadHandler)
            ac.setCheckable(True)
            if fld in self.fields: ac.setChecked(True)
        if not menu.isEmpty(): menu.exec_(self.treeView.mapToGlobal(point))
    
    def rightClickMenuHeadHandler(self):
        fld = str(self.sender().text())
        if fld == 'Name': return
        #self.beginResetModel()
        if fld in self.fields:
            indx = self.fields.index(fld)
            self.beginRemoveColumns(QtCore.QModelIndex(), indx, indx)
            for i in range(len(self.compounds)):
                self.beginRemoveColumns( \
                  self.index(i, 0, QtCore.QModelIndex()), indx, indx)
            self.fields.remove(fld)
            for i in range(len(self.compounds) + 1):
                self.endRemoveColumns()
        else:
            cols = len(self.fields)
            self.beginInsertColumns(QtCore.QModelIndex(), cols, cols)
            for i in range(len(self.compounds)):
                self.beginInsertColumns( \
                  self.index(i, 0, QtCore.QModelIndex()), cols, cols)
            self.treeView.resizeColumnToContents(len(self.fields)-1)
            self.fields.append(fld)
            for i in range(len(self.compounds) + 1):
                self.endInsertColumns()
        #self.endResetModel()

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
                data = [] #spectrum
                #TODO: make the peak type MS or UV?
                ft = Spectrum(data,None)
                ft.ids[2] = dt.fid[1]
                cmpd.addFeat(ft)
                #TODO: make this update the Peak Table

    def _addCompoundFromMenu(self):
        ft_id = self.sender().data()
        ft = None
        self.beginResetModel()
        for i in self.compounds:
            for j in i.getFeats(self.fids):
                if j.ids[0] == ft_id:
                    i.feats.remove(j)
                    ft = j
                    break
        if ft is None: return
        self.addCompoundWithFeat(ft,self.tr('New Compound'))
        self.endResetModel()
    
    def _delFeatFromMenu(self):
        ft_id = self.sender().data()
        ft = None
        for i in self.compounds:
            for j in i.feats:
                if j.ids[0] == ft_id:
                    ft = j
                    break
        if ft is None: return
        self.delFeat(ft)        

    # The following functions are not overriden, but deal
    # with stuff in the peaks database so they're here.

    def findPeak(self, x, y):
        lst = []
        for i in self.compounds:
            for j in i.getPeaks(self.fids):
                if j.contains(x, y):
                    lst.append(j)
        return lst

    def addCompoundWithFeat(self, ft, name):
        new_cmpd = Compound(name,self.database)
        self.database.addCompound(new_cmpd)
        new_cmpd.addFeat(ft)
        #TODO: this next line is going to slow this down if
        #we use it in an batch integrator
        self.compounds = self.database.getCompounds(self.fids)

    def delCompound(self, cmpd_id):
        #delete all the patchs assigned to pks belonging to this cmpd
        #also make sure all the datafiles are updated
        pks = []
        for cmpd in self.compounds:
            if cmpd.cmpd_id == cmpd_id:
                for ft in cmpd.feats:
                    if isinstance(ft, Peak):
                        pks.append(ft)
                        ft.dt.delInfo('s-peaks')
                self.masterWindow.plotter.removePeaks(pks)
                break
            
        self.beginResetModel()
        self.database.delCompound(cmpd_id)
        self.compounds = self.database.getCompounds(self.fids)
        self.endResetModel()

    def delFeat(self, ft):
        #TODO: factor plotter code into plotter
        for cmpd in self.compounds:
            if ft in cmpd.getFeats(self.fids):
                if isinstance(ft, Peak):
                    self.masterWindow.plotter.removePeaks([ft])
                    ft.dt.delInfo('s-peaks')
                self.beginResetModel()
                if len(cmpd.getFeats(self.fids)) == 1 and \
                   cmpd.cmpd_id is not None:
                    self.database.delCompound(cmpd.cmpd_id)
                    self.compounds = self.database.getCompounds(self.fids)
                else:
                    cmpd.delFeat(ft)
                self.endResetModel()
                break

    def addFeats(self,fts):
        self.beginResetModel()
        for ft in fts:
            self.compounds[0].addFeat(ft)
            if isinstance(ft, Peak):
                self.masterWindow.plotter.addPeak(ft)
        self.endResetModel()
        self.masterWindow.plotter.redraw()
