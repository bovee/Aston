# -*- coding: utf-8 -*-
#pylint: disable=C0103
'''Model for handling display of open files.'''

import os.path as op
from PyQt4 import QtGui, QtCore

from Method import flds
from aston.Database import AstonDatabase
from aston.PeakTable import PeakTreeModel

class FileTreeModel(QtCore.QAbstractItemModel):
    '''Handles interfacing with QTreeView and other file-related duties.'''
    def __init__(self, database=None, treeView=None, masterWindow=None, *args): 
        QtCore.QAbstractItemModel.__init__(self, *args) 
        
        self.database = AstonDatabase(op.join(database,'aston.sqlite'))
        self.projects = self.database.getProjects()
        self.fields = ['name', 'vis', 'traces', 'r-filename']
        self.masterWindow = masterWindow

        if treeView is not None:
            self.treeView = treeView
            
            #set up proxy model
            self.proxyMod = FilterModel() #QtGui.QSortFilterProxyModel()
            self.proxyMod.setSourceModel(self)
            self.proxyMod.setDynamicSortFilter(True)
            self.proxyMod.setFilterKeyColumn(0)
            self.proxyMod.setFilterCaseSensitivity(False)
            treeView.setModel(self.proxyMod)
            treeView.setSortingEnabled(True)
            #treeView.setModel(self)

            #set up selections
            treeView.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
            treeView.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
            treeView.clicked.connect(self.itemSelected)
            
            #set up right-clicking
            treeView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
            treeView.customContextMenuRequested.connect(self.rightClickMenu)
            treeView.header().setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
            treeView.header().customContextMenuRequested.connect( \
                self.rightClickMenuHead)
            
            #set up drag and drop
            treeView.setDragEnabled(True)
            treeView.setAcceptDrops(True)
            treeView.setDragDropMode(QtGui.QAbstractItemView.DragDrop)
            treeView.dragMoveEvent = self.dragMoveEvent
            
            #keep us aware of column reordering
            self.treeView.header().sectionMoved.connect(self.colMoved)
            
            #prettify
            treeView.expandAll()
            treeView.resizeColumnToContents(0)
            treeView.resizeColumnToContents(1)

    def dragMoveEvent(self, event):
        index = self.proxyMod.mapToSource(self.treeView.indexAt(event.pos()))
        if not index.parent().isValid() and \
           event.mimeData().hasFormat('application/x-aston-file'):
            QtGui.QTreeView.dragMoveEvent(self.treeView,event)
        else:
            event.ignore()

    def mimeTypes(self):
        types = QtCore.QStringList()
        types.append('text/plain')
        types.append('application/x-aston-file')
        return types

    def mimeData(self, indexList):
        fname_lst = []
        fid_lst = []
        for i in indexList:
            if i.column() == 0:
                fname_lst.append(i.internalPointer().filename)
                fid_lst.append(':'.join([str(j) for j in \
                                         i.internalPointer().fid]))
        data = QtCore.QMimeData()
        data.setText('\n'.join(fname_lst))
        data.setData('application/x-aston-file',','.join(fid_lst))
        return data

    def dropMimeData(self, data, action, row, col, parent):
        #TODO: drop files into library?
        fids = data.data('application/x-aston-file')
        if not parent.isValid(): return False
        self.beginResetModel()
        for pid,fid in [i.split(':') for i in fids.split(',')]:
            if pid == 'None': fles = self.database.getProjFiles(None)
            else: fles = self.database.getProjFiles(int(pid))
            for dt in fles:
                if dt.fid[1] == int(fid):
                    dt.fid = (parent.internalPointer()[0],int(fid))
                    self.database.updateFile(dt)
                    break
        self.endResetModel()
        return True
        
    def supportedDropActions(self):
        return QtCore.Qt.MoveAction

    def index(self, row, column, parent):
        if row < 0 or column < 0 or column > len(self.fields):
            return QtCore.QModelIndex()
        if not parent.isValid() and row < len(self.projects):
            projid = self.projects[row]
            return self.createIndex(row, column, projid)
        elif parent.column() == 0:
            projid = parent.internalPointer()[0]
            datafiles = self.database.getProjFiles(projid)
            if row > len(datafiles):
                return QtCore.QModelIndex()
            return self.createIndex(row, column, datafiles[row])
        return QtCore.QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()
        elif type(index.internalPointer()) is list or \
                  index.internalPointer() is None:
            return QtCore.QModelIndex()
        else:
            projid = index.internalPointer().fid[0]
            row = [i[0] for i in self.projects].index(projid)
            #figure out the project row and projid of the given fileid
            return self.createIndex(row, 0, self.projects[row])

    def rowCount(self,parent):
        if not parent.isValid():
            #top level: return number of projects
            return len(self.projects)
        elif type(parent.internalPointer()) is list:
            #return number of files in a given project
            projid = parent.internalPointer()[0]
            return len(self.database.getProjFiles(projid))
        else:
            return 0

    def columnCount(self, parent):
        return len(self.fields)

    def data(self, index, role):
        rslt = None

        fld = self.fields[index.column()].lower()
        if not index.parent().isValid():
            #return info about a project
            if fld == 'name' and role == QtCore.Qt.DisplayRole:
                rslt = self.projects[index.row()][1]
        else:
            #return info about a file
            f = index.internalPointer()
            if fld == 'vis' and role == QtCore.Qt.CheckStateRole:
                if f.visible:
                    rslt = QtCore.Qt.Checked
                else:
                    rslt = QtCore.Qt.Unchecked
            elif role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
                rslt = f.getInfo(fld)
        return rslt

    def headerData(self, col, orientation, role):
        rslt = None
        if orientation == QtCore.Qt.Horizontal and \
                  role == QtCore.Qt.DisplayRole:
            if self.fields[col] in flds:
                rslt = flds[self.fields[col]]
            else:
                rslt = self.fields[col]
        return rslt

    def setData(self, index, data, role):
        data = str(data)
        col = self.fields[index.column()].lower()
        if not index.parent().isValid():
            if col == 'name':
                proj_id = index.internalPointer()[0]
                self.database.addProject(data,proj_id)
                self.projects[index.row()][1] = data
        else:
            if col == 'vis':
                index.internalPointer().visible = data == '2'
                #redraw the main plot
                self.masterWindow.plotData()
            elif col == 'traces' or col[:2] == 't-':
                index.internalPointer().info[col] = data
                if index.internalPointer().visible:
                    self.masterWindow.plotData()
            else:
                index.internalPointer().info[col] = data
            index.internalPointer().saveChanges()
        self.dataChanged.emit(index, index)
        return True
        
    def flags(self, index):
        col = self.fields[index.column()].lower()
        dflags = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        if not index.isValid():
            return dflags
        if not index.parent().isValid():
            if index.internalPointer()[0] is not None and col == 'name':
                return  dflags | QtCore.Qt.ItemIsEditable | \
                        QtCore.Qt.ItemIsDropEnabled
            else:
                return dflags | QtCore.Qt.ItemIsDropEnabled
        else:
            dflags = dflags | QtCore.Qt.ItemIsDragEnabled
            if col == 'vis':
                return dflags | QtCore.Qt.ItemIsEditable | \
                       QtCore.Qt.ItemIsUserCheckable
            elif col in ['r-filename'] or col[:2] == 's-':
                return dflags
            else:
                return dflags | QtCore.Qt.ItemIsEditable

    def itemSelected(self):
        #TODO: update an info window?
        #remove the current spectrum
        self.masterWindow.plotter.drawSpecLine(None)

        #remove all of the peak patches from the main plot
        self.masterWindow.plotter.clearPeaks()
        
        #recreate the table of peaks for the new files
        self.masterWindow.ptab_mod = PeakTreeModel(self.database,
          self.masterWindow.ui.peakTreeView,
          self.masterWindow,
          self.masterWindow.ftab_mod.returnSelFiles())
        
    def colMoved(self,x,oldCol,newCol):
        #self.fields[oldCol], self.fields[newCol] = \
        #  self.fields[newCol], self.fields[oldCol]
        print self.fields

    def rightClickMenu(self,point):
        index = self.proxyMod.mapToSource(self.treeView.indexAt(point))
        menu = QtGui.QMenu(self.treeView)

        if index.isValid():
            if not index.parent().isValid():
                menu.addAction(self.tr('New Project'),self.addProject)
                if index.internalPointer()[0] is not None:
                    delAc = menu.addAction(self.tr('Delete Project'),
                                           self.delProject)
                    delAc.setData(index.internalPointer()[0])
            else:
                pass
        else:
            menu.addAction(self.tr('New Project'), self.addProject)

        if not menu.isEmpty():
            menu.exec_(self.treeView.mapToGlobal(point))

    def rightClickMenuHead(self,point):
        menu = QtGui.QMenu(self.treeView)
        m_menu = QtGui.QMenu(menu)
        r_menu = QtGui.QMenu(menu)
        s_menu = QtGui.QMenu(menu)
        t_menu = QtGui.QMenu(menu)
        
        for fld in flds:
            if fld == 'name': continue
            mi = flds[fld]
            if fld[:2] == 'm-':
                ac = m_menu.addAction(mi, self.rightClickMenuHeadHandler)
            elif fld[:2] == 'r-':
                ac = r_menu.addAction(mi, self.rightClickMenuHeadHandler)
            elif fld[:2] == 's-':
                ac = s_menu.addAction(mi, self.rightClickMenuHeadHandler)
            elif fld[:2] == 't-':
                ac = t_menu.addAction(mi, self.rightClickMenuHeadHandler)
            else:
                ac = menu.addAction(mi, self.rightClickMenuHeadHandler)
            ac.setData(fld)
            ac.setCheckable(True)
            if fld in self.fields: ac.setChecked(True)
            
        ac = menu.addAction(self.tr('Method'))
        ac.setMenu(m_menu)
        ac = menu.addAction(self.tr('Run'))
        ac.setMenu(r_menu)
        ac = menu.addAction(self.tr('Stats'))
        ac.setMenu(s_menu)
        ac = menu.addAction(self.tr('Transforms'))
        ac.setMenu(t_menu)
        menu.exec_(self.treeView.mapToGlobal(point))
    
    def rightClickMenuHeadHandler(self):
        fld = str(self.sender().data())
        if fld == 'name': return
        if fld in self.fields:
            indx = self.fields.index(fld)
            self.beginRemoveColumns(QtCore.QModelIndex(), indx, indx)
            for i in range(len(self.projects)):
                self.beginRemoveColumns( \
                  self.index(i, 0, QtCore.QModelIndex()), indx, indx)
            self.fields.remove(fld)
            for i in range(len(self.projects) + 1):
                self.endRemoveColumns()
        else:
            cols = len(self.fields)
            self.beginInsertColumns(QtCore.QModelIndex(), cols, cols)
            for i in range(len(self.projects)):
                self.beginInsertColumns( \
                  self.index(i, 0, QtCore.QModelIndex()), cols, cols)
            self.treeView.resizeColumnToContents(len(self.fields)-1)
            self.fields.append(fld)
            for i in range(len(self.projects) + 1):
                self.endInsertColumns()
            #FIXME: selection needs to be updated to new col too
            #self.treeView.selectionModel().selectionChanged.emit()

    def addProject(self):
        '''Add a project to the list.'''
        indx = len(self.projects)
        #self.beginResetModel()
        self.beginInsertRows(QtCore.QModelIndex(), indx, indx)
        proj_id = self.database.addProject('New Project')
        #self.projects = self.database.getProjects()
        self.projects.append([proj_id,'New Project'])
        self.endInsertRows()
        #self.endResetModel()

    def delProject(self):
        '''Deletes a project from the list.'''
        #TODO: need to update "Unsorted" after this
        proj_id = self.sender().data()
        indx = [i[0] for i in self.projects].index(proj_id)
        self.beginRemoveRows(QtCore.QModelIndex(), indx, indx)
        self.database.delProject(proj_id)
        del self.projects[indx]
        self.endRemoveRows()

    #The following methods are not being overridden, but are here
    #because they rely upon data only know to the file table.

    def returnChkFiles(self):
        '''Returns the files checked as visible in the file list.'''
        chkFiles = []
        for i in range(self.proxyMod.rowCount(QtCore.QModelIndex())):
            prjNode = self.proxyMod.index(i,0,QtCore.QModelIndex())
            for j in range(self.proxyMod.rowCount(prjNode)):
                f = self.proxyMod.mapToSource( \
                    self.proxyMod.index(j, 0, prjNode)).internalPointer()
                if f.visible:
                    chkFiles.append(f)
        return chkFiles

    def returnSelFile(self):
        '''Returns the file currently selected in the file list.
        Used for determing which spectra to display on right click, etc.'''
        tab_sel = self.treeView.selectionModel()
        if not tab_sel.currentIndex().isValid:
            return

        ind = self.proxyMod.mapToSource(tab_sel.currentIndex())
        if ind.internalPointer() is None or type(ind.internalPointer()) is list:
            return #it's either doesn't exist of is a project
        return ind.internalPointer()

    def returnSelFiles(self):
        '''Returns the files currently selected in the file list.
        Used for displaying the peak list, etc.'''
        tab_sel = self.treeView.selectionModel()
        files = []
        for i in tab_sel.selectedRows():
            if i.parent().isValid():
                files.append(i.model().mapToSource(i).internalPointer())
        return files

class FilterModel(QtGui.QSortFilterProxyModel):
    def __init__(self,parent=None):
        super(FilterModel,self).__init__(parent)

    def filterAcceptsRow(self, row, index):
        if not index.isValid():
            return True
        else:
            return super(FilterModel, self).filterAcceptsRow(row, index)
