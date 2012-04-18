# -*- coding: utf-8 -*-
#pylint: disable=C0103
'''Model for handling display of open files.'''

import os.path as op
import json
from PyQt4 import QtGui, QtCore

from aston.ui.Fields import aston_fields, aston_groups, aston_field_opts

class FileTreeModel(QtCore.QAbstractItemModel):
    '''Handles interfacing with QTreeView and other file-related duties.'''
    def __init__(self, database=None, treeView=None, masterWindow=None, *args): 
        QtCore.QAbstractItemModel.__init__(self, *args) 
        
        self.db = database
        self.treehead = self.db.getChildren() #TODO: can this be removed?
        self.masterWindow = masterWindow
        self.fields = json.loads(self.db.getKey('main_cols'))

        if treeView is not None:
            self.treeView = treeView
            
            #set up proxy model
            self.proxyMod = FilterModel()
            self.proxyMod.setSourceModel(self)
            self.proxyMod.setDynamicSortFilter(True)
            self.proxyMod.setFilterKeyColumn(0)
            self.proxyMod.setFilterCaseSensitivity(False)
            treeView.setModel(self.proxyMod)
            treeView.setSortingEnabled(True)

            #set up selections
            treeView.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
            treeView.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
            treeView.clicked.connect(self.itemSelected)
            
            #set up right-clicking
            treeView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
            treeView.customContextMenuRequested.connect(self.rClickMenu)
            treeView.header().setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
            treeView.header().customContextMenuRequested.connect( \
              self.rClickHead)
            treeView.header().setStretchLastSection(False)
            
            #set up drag and drop
            treeView.setDragEnabled(True)
            treeView.setAcceptDrops(True)
            treeView.setDragDropMode(QtGui.QAbstractItemView.DragDrop)
            treeView.dragMoveEvent = self.dragMoveEvent
            
            #keep us aware of column reordering
            self.treeView.header().sectionMoved.connect(self.colsChanged)
            
            #deal with combo boxs in table
            self.cDelegates = {}
            self.enableComboCols()
            
            #prettify
            treeView.expandAll()
            treeView.resizeColumnToContents(0)
            treeView.resizeColumnToContents(1)

    def dragMoveEvent(self, event):
        #TODO: files should be able to be under peaks
        index = self.proxyMod.mapToSource(self.treeView.indexAt(event.pos()))
        if event.mimeData().hasFormat('application/x-aston-file'):
            QtGui.QTreeView.dragMoveEvent(self.treeView, event)
        else:
            event.ignore()

    def mimeTypes(self):
        types = QtCore.QStringList()
        types.append('text/plain')
        types.append('application/x-aston-file')
        return types

    def mimeData(self, indexList, incHeaders=False):
        row_lst = []
        id_lst = []
        flds = [self.fields[self.treeView.header().logicalIndex(fld)] \
                    for fld in range(len(self.fields))]
        for i in indexList:
            if i.column() == 0:
                id_lst.append(str(i.internalPointer().db_id))
                col_lst = []
                for col in flds:
                    if col not in ['vis']:
                        col_lst.append(i.internalPointer().getInfo(col))
                row_lst.append('\t'.join(col_lst))
        data = QtCore.QMimeData()
        if incHeaders:
            data.setText(','.join(flds)+'\n'+'\n'.join(row_lst))
        else:
            data.setText('\n'.join(row_lst))
        data.setData('application/x-aston-file',','.join(id_lst))
        return data

    def dropMimeData(self, data, action, row, col, parent):
        #TODO: drop files into library?
        fids = data.data('application/x-aston-file')
        if not parent.isValid():
            new_parent_id = None
        else:
            new_parent_id = parent.internalPointer().db_id
        self.beginResetModel()
        for db_id in [int(i) for i in fids.split(',')]:
            obj = self.db.getObjectByID(db_id)
            if obj in self.treehead and new_parent_id is not None:
                del self.treehead[self.treehead.index(obj)]
            obj.parent_id = new_parent_id
            obj.saveChanges()
        self.endResetModel()
        return True
        
    def supportedDropActions(self):
        return QtCore.Qt.MoveAction
    
    def enableComboCols(self):
        for c in aston_field_opts.keys():
            if c in self.fields and c not in self.cDelegates:
                #new column, need to add combo support in
                opts = aston_field_opts[c]
                self.cDelegates[c] = (self.fields.index(c), ComboDelegate(opts))
                self.treeView.setItemDelegateForColumn(*self.cDelegates[c])
            elif c not in self.fields and c in self.cDelegates:
                #column has been deleted, remove from delegate list
                self.treeView.setItemDelegateForColumn( \
                  self.cDelegates[c][0], self.treeView.itemDelegate())
                del self.cDelegates[c]

    def index(self, row, column, parent):
        if row < 0 or column < 0 or column > len(self.fields):
            return QtCore.QModelIndex()
        elif not parent.isValid() and row < len(self.treehead):
            return self.createIndex(row, column, self.treehead[row])
        elif parent.column() == 0:
            sibs = parent.internalPointer().children
            if row > len(sibs):
                return QtCore.QModelIndex()
            return self.createIndex(row, column, sibs[row])
        return QtCore.QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()
        elif index.internalPointer() in self.treehead or \
          index.internalPointer() is None:
            return QtCore.QModelIndex()
        else:
            me = index.internalPointer()
            pa = me.parent
            if pa is None:
                row = self.treehead.index(me)
            else:
                row = pa.children.index(me)
            return self.createIndex(row, 0, pa)

    def rowCount(self, parent):
        if not parent.isValid():
            return len(self.treehead)
        elif parent.column() == 0:
            return len(parent.internalPointer().children)
        else:
            return 0

    def columnCount(self, parent):
        return len(self.fields)

    def data(self, index, role):
        rslt = None

        fld = self.fields[index.column()].lower()
        f = index.internalPointer()
        if f is None:
            rslt = None
        elif fld == 'vis' and f.db_type == 'file':
            if role == QtCore.Qt.CheckStateRole:
                if f.getInfo('vis') == 'y':
                    rslt = QtCore.Qt.Checked
                else:
                    rslt = QtCore.Qt.Unchecked
        elif role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            rslt = f.getInfo(fld)
        elif role == QtCore.Qt.DecorationRole and index.column() == 0:
            if f.db_type == 'file':
                icn_path = op.join(op.curdir,'aston','ui','icons','file.png')
                return QtGui.QIcon(icn_path)
            elif f.db_type == 'peak':
                icn_path = op.join(op.curdir,'aston','ui','icons','peak.png')
                return QtGui.QIcon(icn_path)
            elif f.db_type == 'spectrum':
                icn_path = op.join(op.curdir,'aston','ui','icons','spectrum.png')
                return QtGui.QIcon(icn_path)
        return rslt

    def headerData(self, col, orientation, role):
        if orientation == QtCore.Qt.Horizontal and \
                  role == QtCore.Qt.DisplayRole:
            if self.fields[col] in aston_fields:
                return aston_fields[self.fields[col]]
            else:
                return self.fields[col]
        else:
            return None

    def setData(self, index, data, role):
        data = str(data)
        col = self.fields[index.column()].lower()
        obj = index.internalPointer()
        if col == 'vis':
            obj.info['vis'] = ('y' if data == '2' else 'n')
            #redraw the main plot
            self.masterWindow.plotData()
        elif col == 'traces' or col[:2] == 't-':
            obj.info[col] = data
            if obj.getInfo('vis') == 'y':
                self.masterWindow.plotData()
        elif col == 'p-model':
            obj.setInfo(col, data)
            prt = obj.getParentOfType('file')
            if prt is not None:
                if prt.getInfo('vis') == 'y':
                    self.masterWindow.plotData()
        else:
            obj.setInfo(col, data)
        obj.saveChanges()
        self.dataChanged.emit(index, index)
        return True
        
    def flags(self, index):
        col = self.fields[index.column()].lower()
        obj = index.internalPointer()
        dflags = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        dflags |= QtCore.Qt.ItemIsDropEnabled
        if not index.isValid():
            return dflags
        dflags |= QtCore.Qt.ItemIsDragEnabled
        if col == 'vis' and obj.db_type == 'file':
            dflags |= QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsUserCheckable
        elif col in ['r-filename'] or col[:2] == 's-' or col == 'vis':
            pass
        elif obj.db_type == 'file' and (col[:2] == 'p-' or col[:3] == 'sp-'):
            pass
        elif obj.db_type != 'file' and (col[:2] == 't-' or col[:2] == 'r-'):
            pass
        else:
            dflags |= QtCore.Qt.ItemIsEditable
        return dflags

    def itemSelected(self):
        #TODO: update an info window?
        #remove the current spectrum
        self.masterWindow.plotter.drawSpecLine(None)

        #remove all of the peak patches from the
        #main plot and add new ones in
        sel = self.returnSelFile()
        if sel is not None:
            if sel.db_type == 'file':
                self.masterWindow.plotter.clearPeaks()
                if sel.getInfo('vis') == 'y':
                    self.masterWindow.plotter.addPeaks( \
                        sel.getAllChildren('peak'))
            elif sel.db_type == 'spectrum':
                self.masterWindow.specplotter.addSpec(dict(sel.data),'lib')
                self.masterWindow.specplotter.plotSpec()
        
    def colsChanged(self, *_): #don't care about the args
        flds = [self.fields[self.treeView.header().logicalIndex(fld)] \
                    for fld in range(len(self.fields))]
        self.db.setKey('main_cols', json.dumps(flds))

    def rClickMenu(self, point):
        index = self.proxyMod.mapToSource(self.treeView.indexAt(point))
        menu = QtGui.QMenu(self.treeView)
        sel = self.returnSelFiles()
        
        #Things we can do with peaks
        peaks = [s for s in sel if s.db_type == 'peak']
        if len(peaks) > 0:
            ac = menu.addAction(self.tr('Create Spec.'), self.createSpec)
            ac.setData(','.join([str(o.db_id) for o in peaks]))
            
        #Things we can do with everything
        if len(sel) > 0:
            ac = menu.addAction(self.tr('Delete Items'), self.deleteItem)
            ac.setData(','.join([str(o.db_id) for o in sel]))
            ac = menu.addAction(self.tr('Debug'), self.debug)
            ac.setData(','.join([str(o.db_id) for o in sel]))

        if not menu.isEmpty():
            menu.exec_(self.treeView.mapToGlobal(point))
            
    def deleteItem(self):
        db_list = str(self.sender().data()).split(',')
        objs = [self.db.getObjectByID(int(obj)) for obj in db_list]
        self.delObjects(objs)

    def debug(self):
        db_list = str(self.sender().data()).split(',')
        objs = [self.db.getObjectByID(int(obj)) for obj in db_list]
        pks = [o for o in objs if o.db_type == 'peak']
        for pk in pks:
            x = pk.data[:,0]
            y = pk.as_gaussian()
            plt = self.masterWindow.plotter.plt
            plt.plot(x,y,'-')
            self.masterWindow.plotter.canvas.draw()
        
    def createSpec(self):
        db_list = str(self.sender().data()).split(',')
        objs = [self.db.getObjectByID(int(obj)) for obj in db_list]
        for obj in objs:
             self.addObjects(obj, [obj.createSpectrum()])

    def rClickHead(self,point):
        menu = QtGui.QMenu(self.treeView)
        subs = dict([(n, QtGui.QMenu(menu)) for n in aston_groups])
        
        for fld in aston_fields:
            if fld == 'name': continue
            grp = fld.split('-')[0]
            if grp in subs:
                ac = subs[grp].addAction(aston_fields[fld], \
                                         self.rClickHeadHandler)
            else:
                ac = menu.addAction(aston_fields[fld], \
                                    self.rClickHeadHandler)
            ac.setData(fld)
            ac.setCheckable(True)
            if fld in self.fields:
                ac.setChecked(True)
            
        for grp in subs:
            ac = menu.addAction(aston_groups[grp])
            ac.setMenu(subs[grp])

        menu.exec_(self.treeView.mapToGlobal(point))
    
    def rClickHeadHandler(self):
        fld = str(self.sender().data())
        if fld == 'name': return
        if fld in self.fields:
            indx = self.fields.index(fld)
            self.beginRemoveColumns(QtCore.QModelIndex(), indx, indx)
            for i in range(len(self.treehead)):
                self.beginRemoveColumns( \
                  self.index(i, 0, QtCore.QModelIndex()), indx, indx)
            self.fields.remove(fld)
            for i in range(len(self.treehead) + 1):
                self.endRemoveColumns()
        else:
            cols = len(self.fields)
            self.beginInsertColumns(QtCore.QModelIndex(), cols, cols)
            for i in range(len(self.treehead)):
                self.beginInsertColumns( \
                  self.index(i, 0, QtCore.QModelIndex()), cols, cols)
            self.treeView.resizeColumnToContents(len(self.fields)-1)
            self.fields.append(fld)
            for i in range(len(self.treehead) + 1):
                self.endInsertColumns()
        self.enableComboCols()
        self.colsChanged()
            #FIXME: selection needs to be updated to new col too?
            #self.treeView.selectionModel().selectionChanged.emit()
                
    def addObjects(self, head, objs):
        if head is None:
            row = len(self.treehead)
        else:
            row = len(head.children)
        self.beginInsertRows(self._objToIndex(head), row, row+len(objs)-1)
        for obj in objs:
            if head is not None:
                obj.parent_id = head.db_id
            else:
                obj.parent_id = None
            self.db.addObject(obj)
        self.endInsertRows()
        self.masterWindow.plotter.addPeaks(objs)

    def delObjects(self, objs):
        for obj in objs:
            if obj in self.treehead:
                row = self.treehead.index(obj)
            else:
                row = obj.parent.children.index(obj)
            self.beginRemoveRows(self._objToIndex(obj.parent), row, row)
            self.db.deleteObject(obj)
            if obj in self.treehead:
                del self.treehead[self.treehead.index(obj)]
            self.endRemoveRows()
        self.masterWindow.plotter.removePeaks(objs)
    
    def _objToIndex(self, obj):
        if obj is None:
            return QtCore.QModelIndex()
        elif obj in self.treehead:
            row = self.treehead.index(obj)
        else:
            row = obj.parent.children.index(obj)
        return self.createIndex(row, 0, obj)

    def returnChkFiles(self, node=None):
        '''Returns the files checked as visible in the file list.'''
        if node is None:
            node = QtCore.QModelIndex()

        chkFiles = []
        for i in range(self.proxyMod.rowCount(node)):
            prjNode = self.proxyMod.index(i, 0, node)
            f = self.proxyMod.mapToSource(prjNode).internalPointer()
            if f.getInfo('vis') == 'y':
                chkFiles.append(f)
            if self.proxyMod.rowCount(prjNode) > 0:
                chkFiles += self.returnChkFiles(prjNode)
        return chkFiles

    def returnSelFile(self):
        '''Returns the file currently selected in the file list.
        Used for determing which spectra to display on right click, etc.'''
        tab_sel = self.treeView.selectionModel()
        if not tab_sel.currentIndex().isValid:
            return
        
        ind = self.proxyMod.mapToSource(tab_sel.currentIndex())
        if ind.internalPointer() is None:
            return #it's doesn't exist
        return ind.internalPointer()

    def returnSelFiles(self, cls=None):
        '''Returns the files currently selected in the file list.
        Used for displaying the peak list, etc.'''
        tab_sel = self.treeView.selectionModel()
        files = []
        for i in tab_sel.selectedRows():
            obj = i.model().mapToSource(i).internalPointer()
            if cls is None or obj.db_type == cls:
                files.append(obj)
        return files
    
    def itemsAsCSV(self, itms, delim=',', incHeaders=True):
        flds = [self.fields[self.treeView.header().logicalIndex(fld)] \
                    for fld in range(len(self.fields))]
        row_lst = []
        for i in itms:
            col_lst = []
            for col in flds:
                if col not in ['vis']:
                    col_lst.append(i.getInfo(col))
            row_lst.append(delim.join(col_lst))
                
        if incHeaders:
            flds = [aston_fields[i] for i in flds if i not in ['vis']]
            return delim.join(flds)+'\n'+'\n'.join(row_lst)
        else:
            return '\n'.join(row_lst)
    
class FilterModel(QtGui.QSortFilterProxyModel):
    def __init__(self, parent=None):
        super(FilterModel,self).__init__(parent)

    def filterAcceptsRow(self, row, index):
        #if index.internalPointer() is not None:
        #    db_type = index.internalPointer().db_type
        #    if db_type == 'file':
        #        return super(FilterModel, self).filterAcceptsRow(row, index)
        #    else:
        #        return True
        #else:
        return super(FilterModel, self).filterAcceptsRow(row, index)

class ComboDelegate(QtGui.QItemDelegate):
    def __init__(self, opts, *args):
        self.opts = opts
        super(ComboDelegate,self).__init__(*args)
        
    def createEditor(self, parent, option, index):
        cmb = QtGui.QComboBox(parent)
        cmb.addItems(self.opts)
        return cmb
    
    def setEditorData(self, editor, index):
        txt = index.data(QtCore.Qt.EditRole)
        if txt in self.opts:
            editor.setCurrentIndex(self.opts.index(txt))
        else:
            super(ComboDelegate,self).setEditorData(editor, index)
        
    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText(), QtCore.Qt.EditRole)
