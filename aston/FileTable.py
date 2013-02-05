# -*- coding: utf-8 -*-

#    Copyright 2011-2013 Roderick Bovee
#
#    This file is part of Aston.
#
#    Aston is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Aston is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Aston.  If not, see <http://www.gnu.org/licenses/>.

"""
Model for handling display of open files.
"""
#pylint: disable=C0103

import re
import os.path as op
import json
import pkg_resources
from collections import OrderedDict
from PyQt4 import QtGui, QtCore
from aston.ui.Fields import aston_fields, aston_groups, aston_field_opts
from aston.ui.MenuOptions import peak_models
from aston.Database import AstonFileDatabase

peak_models = {str(k): peak_models[k] for k in peak_models}


class FileTreeModel(QtCore.QAbstractItemModel):
    """
    Handles interfacing with QTreeView and other file-related duties.
    """
    def __init__(self, database=None, treeView=None, masterWindow=None, *args):
        QtCore.QAbstractItemModel.__init__(self, *args)

        self.db = database
        self.masterWindow = masterWindow
        if type(database) == AstonFileDatabase:
            def_fields = '["name", "vis", "traces", "r-filename"]'
        else:
            def_fields = '["name"]'
        self.fields = json.loads(self.db.get_key('main_cols', dflt=def_fields))

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

            #set up key shortcuts
            delAc = QtGui.QAction("Delete", treeView, \
              shortcut=QtCore.Qt.Key_Backspace, triggered=self.delItemKey)
            treeView.addAction(delAc)

            #set up right-clicking
            treeView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
            treeView.customContextMenuRequested.connect(self.click_main)
            treeView.header().setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
            treeView.header().customContextMenuRequested.connect( \
              self.click_head)
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
            treeView.collapseAll()
            treeView.setColumnWidth(0, 300)
            treeView.setColumnWidth(1, 60)

    def dragMoveEvent(self, event):
        #TODO: files shouldn't be able to be under peaks
        #index = self.proxyMod.mapToSource(self.treeView.indexAt(event.pos()))
        if event.mimeData().hasFormat('application/x-aston-file'):
            QtGui.QTreeView.dragMoveEvent(self.treeView, event)
        else:
            event.ignore()

    def mimeTypes(self):
        types = QtCore.QStringList()
        types.append('text/plain')
        types.append('application/x-aston-file')
        return types

    def mimeData(self, indexList):
        data = QtCore.QMimeData()
        objs = [i.internalPointer() for i in indexList \
          if i.column() == 0]
        data.setText(self.items_as_csv(objs))

        id_lst = [str(o.db_id) for o in objs]
        data.setData('application/x-aston-file', ','.join(id_lst))
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
            obj.parent_id = new_parent_id
            obj.save_changes()
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
        elif not parent.isValid() and row < len(self.db.root):
            return self.createIndex(row, column, self.db.root[row])
        elif parent.column() == 0:
            sibs = parent.internalPointer().children
            if row > len(sibs):
                return QtCore.QModelIndex()
            return self.createIndex(row, column, sibs[row])
        return QtCore.QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()
        elif index.internalPointer() in self.db.root or \
          index.internalPointer() is None:
            return QtCore.QModelIndex()
        else:
            me = index.internalPointer()
            pa = me.parent
            if pa is None:
                row = self.db.root.index(me)
            else:
                row = pa.children.index(me)
            return self.createIndex(row, 0, pa)

    def rowCount(self, parent):
        if not parent.isValid():
            return len(self.db.root)
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
                if f.info['vis'] == 'y':
                    rslt = QtCore.Qt.Checked
                else:
                    rslt = QtCore.Qt.Unchecked
        elif role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            if fld == 'p-model' and f.db_type == 'peak':
                rpeakmodels = {peak_models[k]: k for k in peak_models}
                rslt = rpeakmodels.get(f.info[fld], 'None')
            else:
                rslt = f.info[fld]
        elif role == QtCore.Qt.DecorationRole and index.column() == 0:
            #TODO: icon for method, compound
            fname = {'file': 'file.png', 'peak': 'peak.png', \
                    'spectrum': 'spectrum.png'}
            loc = pkg_resources.resource_filename(__name__, \
              op.join('ui', 'icons', fname.get(f.db_type, '')))
            rslt = QtGui.QIcon(loc)
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
            if obj.info['vis'] == 'y':
                self.masterWindow.plotData()
        elif col == 'p-model':
            obj.update_model(peak_models[data])
            self.masterWindow.plotter.remove_peaks([obj])
            self.masterWindow.plotter.add_peaks([obj])
        else:
            obj.info[col] = data
        obj.save_changes()
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
            dflags |= QtCore.Qt.ItemIsUserCheckable
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
        self.masterWindow.plotter.draw_spec_line(None, None)

        #remove all of the peak patches from the
        #main plot and add new ones in
        sel = self.returnSelFile()
        self.masterWindow.specplotter.libscans = []
        if sel is not None:
            if sel.db_type == 'file':
            #    self.masterWindow.plotter.clear_peaks()
            #    if sel.getInfo('vis') == 'y':
            #        self.masterWindow.plotter.add_peaks( \
            #            sel.getAllChildren('peak'))
                pass
            elif sel.db_type == 'spectrum':
                self.masterWindow.specplotter.libscans = [sel.data]
                self.masterWindow.specplotter.plot()
        objs_sel = len(self.returnSelFiles())
        self.masterWindow.show_status(str(objs_sel) + ' items selected')

    def colsChanged(self, *_):  # don't care about the args
        flds = [self.fields[self.treeView.header().logicalIndex(fld)] \
                    for fld in range(len(self.fields))]
        self.db.set_key('main_cols', json.dumps(flds))

    def click_main(self, point):
        #index = self.proxyMod.mapToSource(self.treeView.indexAt(point))
        menu = QtGui.QMenu(self.treeView)
        sel = self.returnSelFiles()

        #Things we can do with peaks
        fts = [s for s in sel if s.db_type == 'peak']
        if len(fts) > 0:
            self._add_menu_opt(self.tr('Create Spec.'), self.createSpec, fts, menu)
            #self._add_menu_opt(self.tr('Split Peak'), self.splitPeaks, fts, menu)
            self._add_menu_opt(self.tr('Merge Peaks'), self.merge_peaks, fts, menu)

        ##Things we can do with files
        #fts = [s for s in sel if s.db_type == 'file']
        #if len(fts) > 0:
        #    self._add_menu_opt(self.tr('Copy Method'), self.makeMethod, fts, menu)

        #Things we can do with everything
        if len(sel) > 0:
            self._add_menu_opt(self.tr('Delete Items'), self.delObjects, sel, menu)
            #self._add_menu_opt(self.tr('Debug'), self.debug, sel)

        if not menu.isEmpty():
            menu.exec_(self.treeView.mapToGlobal(point))

    def _add_menu_opt(self, name, func, objs, menu):
        ac = menu.addAction(name, self.click_handler)
        ac.setData((func, objs))

    def click_handler(self):
        func, objs = self.sender().data()
        func(objs)

    def delItemKey(self):
        self.delObjects(self.returnSelFiles())

    def debug(self, objs):
        pks = [o for o in objs if o.db_type == 'peak']
        for pk in pks:
            x = pk.data[:, 0]
            y = pk.as_gaussian()
            plt = self.masterWindow.plotter.plt
            plt.plot(x, y, '-')
            self.masterWindow.plotter.canvas.draw()

    def merge_peaks(self, objs):
        from aston.Math.Integrators import merge_ions
        new_objs = merge_ions(objs)
        self.delObjects([o for o in objs if o not in new_objs])

    def createSpec(self, objs):
        for obj in objs:
            self.addObjects(obj, [obj.createSpectrum()])

    #def makeMethod(self, objs):
    #    self.masterWindow.cmpd_tab.addObjects(None, objs)

    #def splitPeaks(self, pks):
    #    from aston.Features.Peak import Peak
    #    #db_list = str(self.sender().data()).split(',')
    #    #pks = [self.db.getObjectByID(int(o)) for o in db_list]
    #    SPO, Cancel = QtGui.QInputDialog.getDouble(self.masterWindow, "Aston",
    #                                               "Slice Offset", 0.0)
    #    if not Cancel:
    #        return
    #    SPL, Cancel = QtGui.QInputDialog.getDouble(self.masterWindow, "Aston",
    #                                               "Slice Length", 0.2)
    #    if not Cancel:
    #        return

    #    for pk in pks:
    #        ts, te = min(pk.data.times), max(pk.data.times)
    #        if (ts - SPO) % SPL == 0:
    #            t0 = pk.time()[0]
    #        else:
    #            t0 = SPO + SPL * (np.ceil((ts - SPO) / SPL) - 1)
    #        t = t0

    #        def y(tm):
    #            ys, ye = pk.data.y[0], pk.data.y[-1]
    #            return ys + (ye - ys) * (tm - t0) / (te - ts)

    #        pks = []
    #        dt = pk.parent
    #        del pk.info['p-s-']
    #        info = pk.info
    #        info['p-int'] = 'split'
    #        while t < te:
    #            verts = np.column_stack((pk.time(t, t + SPL), \
    #              pk.trace(None, t, t + SPL)))
    #            if t != t0:
    #                #not the first point
    #                verts = np.vstack(([t, y(t)], verts))
    #            if t + SPL < te:
    #                #not the last point
    #                verts = np.vstack((verts, [t + SPL, y(t + SPL)]))
    #            info['name'] = '{:.2f}-{:.2f}'.format(verts[0, 0],\
    #                                                  verts[-1, 0])
    #            pks.append(Peak(dt.db, None, dt.db_id, \
    #                            info.copy(), verts.tolist()))
    #            t += SPL
    #        self.delObjects([pk])
    #        self.addObjects(dt, pks)
    #        del dt.info['s-peaks']

    def click_head(self, point):
        menu = QtGui.QMenu(self.treeView)
        subs = OrderedDict()
        for n in aston_groups:
            subs[n] = QtGui.QMenu(menu)

        for fld in aston_fields:
            if fld == 'name':
                continue
            grp = fld.split('-')[0]
            if grp in subs:
                ac = subs[grp].addAction(aston_fields[fld], \
                  self.click_head_handler)
            else:
                ac = menu.addAction(aston_fields[fld], \
                  self.click_head_handler)
            ac.setData(fld)
            ac.setCheckable(True)
            if fld in self.fields:
                ac.setChecked(True)

        for grp in subs:
            ac = menu.addAction(aston_groups[grp])
            ac.setMenu(subs[grp])

        menu.exec_(self.treeView.mapToGlobal(point))

    def click_head_handler(self):
        fld = str(self.sender().data())
        if fld == 'name':
            return
        if fld in self.fields:
            indx = self.fields.index(fld)
            self.beginRemoveColumns(QtCore.QModelIndex(), indx, indx)
            for i in range(len(self.db.root)):
                self.beginRemoveColumns( \
                  self.index(i, 0, QtCore.QModelIndex()), indx, indx)
            self.fields.remove(fld)
            for i in range(len(self.db.root) + 1):
                self.endRemoveColumns()
        else:
            cols = len(self.fields)
            self.beginInsertColumns(QtCore.QModelIndex(), cols, cols)
            for i in range(len(self.db.root)):
                self.beginInsertColumns( \
                  self.index(i, 0, QtCore.QModelIndex()), cols, cols)
            self.treeView.resizeColumnToContents(len(self.fields) - 1)
            self.fields.append(fld)
            for i in range(len(self.db.root) + 1):
                self.endInsertColumns()
        self.enableComboCols()
        self.colsChanged()
        #FIXME: selection needs to be updated to new col too?
        #self.treeView.selectionModel().selectionChanged.emit()

    def addObjects(self, head, objs):
        if head is None:
            row = len(self.db.root)
        else:
            row = len(head.children)
        self.beginInsertRows(self._objToIndex(head), \
          row, row + len(objs) - 1)
        for obj in objs:
            if head is None:
                obj.parent_id = None
            else:
                obj.parent_id = head.db_id
        self.db.add_objects(objs)
        self.endInsertRows()
        self.masterWindow.plotter.add_peaks(objs)

    def delObjects(self, objs):
        c = self.db.begin_lazy_op()
        for obj in objs:
            if obj in self.db.root:
                row = self.db.root.index(obj)
            else:
                row = obj.parent.children.index(obj)
            self.beginRemoveRows(self._objToIndex(obj.parent), row, row)
            self.db.lazy_delete(c, obj)
            self.endRemoveRows()
        self.db.end_lazy_op(c)
        self.masterWindow.plotter.remove_peaks(objs)

    def _objToIndex(self, obj):
        if obj is None:
            return QtCore.QModelIndex()
        elif obj in self.db.root:
            row = self.db.root.index(obj)
        else:
            row = obj.parent.children.index(obj)
        return self.createIndex(row, 0, obj)

    def active_file(self):
        """
        Returns the file currently selected in the file list.
        If that file is not visible, return the topmost visible file.
        Used for determing which spectra to display on right click, etc.
        """
        dt = self.returnSelFile()
        if dt is not None:
            if dt.db_type == 'file' and dt.info['vis'] == 'y':
                return dt

        dts = self.returnChkFiles()
        if len(dts) == 0:
            return None
        else:
            return dts[0]

    def returnChkFiles(self, node=None):
        """
        Returns the files checked as visible in the file list.
        """
        if node is None:
            node = QtCore.QModelIndex()

        chkFiles = []
        for i in range(self.proxyMod.rowCount(node)):
            prjNode = self.proxyMod.index(i, 0, node)
            f = self.proxyMod.mapToSource(prjNode).internalPointer()
            if f.info['vis'] == 'y':
                chkFiles.append(f)
            if len(f.children) > 0:
                chkFiles += self.returnChkFiles(prjNode)
        return chkFiles

    def returnSelFile(self):
        """
        Returns the file currently selected in the file list.
        Used for determing which spectra to display on right click, etc.
        """
        tab_sel = self.treeView.selectionModel()
        if not tab_sel.currentIndex().isValid:
            return

        ind = self.proxyMod.mapToSource(tab_sel.currentIndex())
        if ind.internalPointer() is None:
            return  # it's doesn't exist
        return ind.internalPointer()

    def returnSelFiles(self, cls=None):
        """
        Returns the files currently selected in the file list.
        Used for displaying the peak list, etc.
        """
        tab_sel = self.treeView.selectionModel()
        files = []
        for i in tab_sel.selectedRows():
            obj = i.model().mapToSource(i).internalPointer()
            if cls is None or obj.db_type == cls:
                files.append(obj)
        return files

    def items_as_csv(self, itms, delim=',', incHeaders=True):
        flds = [self.fields[self.treeView.header().logicalIndex(fld)] \
          for fld in range(len(self.fields))]
        row_lst = []
        block_col = ['vis']
        for i in itms:
            col_lst = [i.info[col] for col in flds \
              if col not in block_col]
            row_lst.append(delim.join(col_lst))

        if incHeaders:
            flds = [aston_fields[i] for i in flds if i not in ['vis']]
            return delim.join(flds) + '\n' + '\n'.join(row_lst)
        else:
            return '\n'.join(row_lst)


class FilterModel(QtGui.QSortFilterProxyModel):
    def __init__(self, parent=None):
        super(FilterModel, self).__init__(parent)

    def filterAcceptsRow(self, row, index):
        #if index.internalPointer() is not None:
        #    db_type = index.internalPointer().db_type
        #    if db_type == 'file':
        #        return super(FilterModel, self).filterAcceptsRow(row, index)
        #    else:
        #        return True
        #else:
        return super(FilterModel, self).filterAcceptsRow(row, index)

    def lessThan(self, left, right):
        tonum = lambda text: int(text) if text.isdigit() else text.lower()
        breakup = lambda key: [tonum(c) for c in re.split('([0-9]+)', key)]
        return breakup(str(left.data())) < breakup(str(right.data()))


class ComboDelegate(QtGui.QItemDelegate):
    def __init__(self, opts, *args):
        self.opts = opts
        super(ComboDelegate, self).__init__(*args)

    def createEditor(self, parent, option, index):
        cmb = QtGui.QComboBox(parent)
        cmb.addItems(self.opts)
        return cmb

    def setEditorData(self, editor, index):
        txt = index.data(QtCore.Qt.EditRole)
        if txt in self.opts:
            editor.setCurrentIndex(self.opts.index(txt))
        else:
            super(ComboDelegate, self).setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText(), QtCore.Qt.EditRole)
