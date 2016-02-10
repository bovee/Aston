# -*- coding: utf-8 -*-

#    Copyright 2011-2014 Roderick Bovee
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
# pylint: disable=C0103

from __future__ import unicode_literals
import json
import os.path as op
from collections import OrderedDict
from PyQt5 import QtGui, QtCore, QtWidgets
from aston.resources import resfile
from aston.qtgui.Fields import aston_fields, aston_groups
from aston.database.File import Project, Run  # , Analysis
from aston.qtgui.TableModel import TableModel


class FileTreeModel(TableModel):
    """
    Handles interfacing with QTreeView and other file-related duties.
    """
    def __init__(self, database=None, tree_view=None, master_window=None,
                 *args):
        super(FileTreeModel, self).__init__(database, tree_view,
                                            master_window, *args)

        # TODO: load custom fields from the database
        self.fields = ['name', 'sel', 'r-filenames', 'r-analyses', 'other']

        # create a list with all of the root items in it
        self._children = self.db.query(Project).filter(Project.name != '').all()
        prj = self.db.query(Project).filter_by(name='').first()
        if prj is None:
            self._children = []
        else:
            q = self.db.query(Run)
            self._children += q.filter_by(_project_id=prj._project_id).all()

        # set up selections
        tree_view.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        tree_view.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)  # noqa
        # TODO: this works, but needs to be detached when opening a new folder
        tree_view.selectionModel().currentChanged.connect(self.itemSelected)
        # tree_view.clicked.connect(self.itemSelected)

        # #set up key shortcuts
        # delAc = QtGui.QAction("Delete", tree_view, \
        #     shortcut=QtCore.Qt.Key_Backspace, triggered=self.delItemKey)
        # delAc = QtGui.QAction("Delete", tree_view, \
        #     shortcut=QtCore.Qt.Key_Delete, triggered=self.delItemKey)
        # tree_view.addAction(delAc)

        # #set up right-clicking
        # tree_view.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        # tree_view.customContextMenuRequested.connect(self.click_main)
        # tree_view.header().setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        # tree_view.header().customContextMenuRequested.connect( \
        #     self.click_head)
        # tree_view.header().setStretchLastSection(False)

        # #set up drag and drop
        # tree_view.setDragEnabled(True)
        # tree_view.setAcceptDrops(True)
        # tree_view.setDragDropMode(QtGui.QAbstractItemView.DragDrop)
        # tree_view.dragMoveEvent = self.dragMoveEvent

        # keep us aware of column reordering
        self.tree_view.header().sectionMoved.connect(self.colsChanged)

        # #deal with combo boxs in table
        # self.cDelegates = {}
        # self.enableComboCols()

        # prettify
        tree_view.collapseAll()
        tree_view.setColumnWidth(0, 300)
        tree_view.setColumnWidth(1, 60)
        self.proxy_mod.invalidate()

        # update_db = self.db.get_key('db_reload_on_open', dflt=True)
        # if type(database) == AstonFileDatabase and update_db:
        #     self.loadthread = LoadFilesThread(self.db)
        #     self.loadthread.file_updated.connect(self.update_obj)
        #     self.loadthread.start()

    def dragMoveEvent(self, event):
        # TODO: files shouldn't be able to be under peaks
        # index = self.proxy_mod.mapToSource(self.tree_view.indexAt(event.pos()))  # noqa
        if event.mimeData().hasFormat('application/x-aston-file'):
            QtGui.QTreeView.dragMoveEvent(self.tree_view, event)
        else:
            event.ignore()

    def mimeTypes(self):
        types = QtCore.QStringList()
        types.append('text/plain')
        types.append('application/x-aston-file')
        return types

    def mimeData(self, indexList):
        data = QtCore.QMimeData()
        objs = [i.internalPointer() for i in indexList if i.column() == 0]
        data.setText(self.items_as_csv(objs))

        id_lst = [str(o.db_id) for o in objs]
        data.setData('application/x-aston-file', ','.join(id_lst))
        return data

    def dropMimeData(self, data, action, row, col, parent):
        # TODO: drop files into library?
        # TODO: deal with moving objects between tables
        #  i.e. copy from compounds table into file table
        fids = data.data('application/x-aston-file')
        if not parent.isValid():
            new_parent = self.db
        else:
            new_parent = parent.internalPointer()
        for db_id in [int(i) for i in fids.split(',')]:
            obj = self.db.object_from_id(db_id)
            if obj is not None:
                obj._parent = new_parent
        return True

    def supportedDropActions(self):
        return QtCore.Qt.MoveAction

    def data(self, index, role):
        fld = self.fields[index.column()]
        obj = index.internalPointer()
        rslt = None
        if type(obj) is Project:
            if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
                if fld == 'name':
                    rslt = obj.name
            elif role == QtCore.Qt.DecorationRole and index.column() == 0:
                # TODO: icon for projects
                pass
        elif type(obj) is Run:
            if fld == 'sel' and role == QtCore.Qt.CheckStateRole:
                if self.master_window.pal_tab.has_run(obj, enabled=True):
                    rslt = QtCore.Qt.Checked
                else:
                    rslt = QtCore.Qt.Unchecked
            elif role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
                if fld == 'name':
                    rslt = obj.name
                elif fld == 'r-filenames':
                    # TODO: shorten path?
                    rslt = ','.join([op.split(a.path)[1] for a in obj.analyses])
                elif fld == 'r-analyses':
                    rslt = ','.join([a.trace.strip('#*') for a in obj.analyses])
                elif fld == 'other':
                    rslt = json.dumps(obj.info)
                else:
                    rslt = obj.info.get(fld, '')
            elif role == QtCore.Qt.DecorationRole and index.column() == 0:
                loc = resfile('aston/qtgui', 'icons/file.png')
                rslt = QtGui.QIcon(loc)
        # elif type(obj) is Analysis:
        #     if role == QtCore.Qt.DisplayRole:
        #         if fld == 'name':
        #             return obj.name
        return rslt

    def setData(self, index, data, role):
        data = str(data)
        col = self.fields[index.column()].lower()
        obj = index.internalPointer()

        if col == 'sel':
            # handle this slightly differently b/c it's in a diff table
            # TODO: use the current palette
            if data == '2':
                self.master_window.pal_tab.add_run(obj)
            else:
                self.master_window.pal_tab.del_run(obj)
        elif col == 'name':
            obj.name = data
            self.db.merge(obj)
            self.db.commit()
        elif type(obj) is Run and col != 'sel':
            obj.info[col] = data
            self.db.merge(obj)
            self.db.commit()
        self.dataChanged.emit(index, index)
        return True

    def flags(self, index):
        col = self.fields[index.column()]
        obj = index.internalPointer()
        dflags = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        dflags |= QtCore.Qt.ItemIsDropEnabled
        if not index.isValid():
            return dflags
        dflags |= QtCore.Qt.ItemIsDragEnabled
        if col == 'sel' and type(obj) is Run:
            dflags |= QtCore.Qt.ItemIsUserCheckable
        elif col in ['r-filenames', 'vis']:
            pass
        else:
            dflags |= QtCore.Qt.ItemIsEditable
        return dflags

    def itemSelected(self):
        # TODO: update an info window?
        # remove the current spectrum
        self.master_window.plotter.clear_highlight()

        # remove all of the peak patches from the
        # main plot and add new ones in
        sel = self.returnSelFile()
        self.master_window.specplotter.libscans = []
        if sel is not None:
            pass
#            if sel.db_type == 'file':
#                pass
#            #     self.master_window.plotter.clear_peaks()
#            #     if sel.getInfo('vis') == 'y':
#            #         self.master_window.plotter.add_peaks( \
#            #             sel.getAllChildren('peak'))
#            elif sel.db_type == 'peak':
#                if sel.parent_of_type('file').info['vis'] == 'y':
#                    self.master_window.plotter.draw_highlight_peak(sel)
#            elif sel.db_type == 'spectrum':
#                self.master_window.specplotter.libscans = [sel.data]
#                self.master_window.specplotter.plot()
        objs_sel = len(self.returnSelFiles())
        self.master_window.show_status(str(objs_sel) + ' items selected')

    def colsChanged(self, *_):  # don't care about the args
        flds = [self.fields[self.tree_view.header().logicalIndex(fld)]
                for fld in range(len(self.fields))]
        self.db.set_key('main_cols', json.dumps(flds))

    def click_main(self, point):
        # index = self.proxy_mod.mapToSource(self.tree_view.indexAt(point))
        menu = QtGui.QMenu(self.tree_view)
        sel = self.returnSelFiles()

        def _add_menu_opt(self, name, func, objs, menu):
            ac = menu.addAction(name, self.click_handler)
            ac.setData((func, objs))

        # Things we can do with peaks
        fts = [s for s in sel if s.db_type == 'peak']
        if len(fts) > 0:
            self._add_menu_opt(self.tr('Create Spec.'),
                               self.createSpec, fts, menu)
            self._add_menu_opt(self.tr('Merge Peaks'),
                               self.merge_peaks, fts, menu)

        fts = [s for s in sel if s.db_type in ('spectrum', 'peak')]
        if len(fts) > 0:
            self._add_menu_opt(self.tr('Find in Lib'),
                               self.find_in_lib, fts, menu)

        # #Things we can do with files
        # fts = [s for s in sel if s.db_type == 'file']
        # if len(fts) > 0:
        #     self._add_menu_opt(self.tr('Copy Method'), \
        #                       self.makeMethod, fts, menu)

        # Things we can do with everything
        if len(sel) > 0:
            self._add_menu_opt(self.tr('Delete Items'), self.delete_objects,
                               sel, menu)
            # self._add_menu_opt(self.tr('Debug'), self.debug, sel)

        if not menu.isEmpty():
            menu.exec_(self.tree_view.mapToGlobal(point))

    def click_handler(self):
        func, objs = self.sender().data()
        func(objs)

    def delItemKey(self):
        self.delete_objects(self.returnSelFiles())

    def debug(self, objs):
        pks = [o for o in objs if o.db_type == 'peak']
        for pk in pks:
            x = pk.data[:, 0]
            y = pk.as_gaussian()
            plt = self.master_window.plotter.plt
            plt.plot(x, y, '-')
            self.master_window.plotter.canvas.draw()

    def merge_peaks(self, objs):
        from aston.Math.Integrators import merge_ions
        new_objs = merge_ions(objs)
        self.delete_objects([o for o in objs if o not in new_objs])

    def createSpec(self, objs):
        with self.db:
            for obj in objs:
                obj._children += [obj.as_spectrum()]

    def find_in_lib(self, objs):
        for obj in objs:
            if obj.db_type == 'peak':
                spc = obj.as_spectrum().data
            elif obj.db_type == 'spectrum':
                spc = obj.data
            lib_spc = self.master_window.cmpd_tab.db.find_spectrum(spc)
            if lib_spc is not None:
                obj.info['name'] = lib_spc.info['name']
                obj.save_changes()

    # def makeMethod(self, objs):
    #     self.master_window.cmpd_tab.addObjects(None, objs)

    def click_head(self, point):
        menu = QtGui.QMenu(self.tree_view)
        subs = OrderedDict()
        for n in aston_groups:
            subs[n] = QtGui.QMenu(menu)

        for fld in aston_fields:
            if fld == 'name':
                continue
            grp = fld.split('-')[0]
            if grp in subs:
                ac = subs[grp].addAction(aston_fields[fld],
                                         self.click_head_handler)
            else:
                ac = menu.addAction(aston_fields[fld], self.click_head_handler)
            ac.setData(fld)
            ac.setCheckable(True)
            if fld in self.fields:
                ac.setChecked(True)

        for grp in subs:
            ac = menu.addAction(aston_groups[grp])
            ac.setMenu(subs[grp])

        menu.exec_(self.tree_view.mapToGlobal(point))

    def click_head_handler(self):
        fld = str(self.sender().data())
        if fld == 'name':
            return
        if fld in self.fields:
            indx = self.fields.index(fld)
            self.beginRemoveColumns(QtCore.QModelIndex(), indx, indx)
            for i in range(len(self.db._children)):
                self.beginRemoveColumns(self.index(i, 0, QtCore.QModelIndex()),
                                        indx, indx)
            self.fields.remove(fld)
            for i in range(len(self.db._children) + 1):
                self.endRemoveColumns()
        else:
            cols = len(self.fields)
            self.beginInsertColumns(QtCore.QModelIndex(), cols, cols)
            for i in range(len(self.db._children)):
                self.beginInsertColumns(self.index(i, 0, QtCore.QModelIndex()),
                                        cols, cols)
            self.tree_view.resizeColumnToContents(len(self.fields) - 1)
            self.fields.append(fld)
            for i in range(len(self.db._children) + 1):
                self.endInsertColumns()
        self.enableComboCols()
        self.colsChanged()
        # FIXME: selection needs to be updated to new col too?
        # self.tree_view.selectionModel().selectionChanged.emit()

    def _obj_to_index(self, obj):
        if obj is None or obj == self.db:
            return QtCore.QModelIndex()
        elif obj in self.db._children:
            row = self.db._children.index(obj)
        else:
            row = obj._parent._children.index(obj)
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
        for i in range(self.proxy_mod.rowCount(node)):
            prjNode = self.proxy_mod.index(i, 0, node)
            f = self.proxy_mod.mapToSource(prjNode).internalPointer()
            if f.info['vis'] == 'y':
                chkFiles.append(f)
            if len(f._children) > 0:
                chkFiles += self.returnChkFiles(prjNode)
        return chkFiles

    def returnSelFile(self):
        """
        Returns the file currently selected in the file list.
        Used for determing which spectra to display on right click, etc.
        """
        tab_sel = self.tree_view.selectionModel()
        if not tab_sel.currentIndex().isValid:
            return

        ind = self.proxy_mod.mapToSource(tab_sel.currentIndex())
        if ind.internalPointer() is None:
            return  # it doesn't exist
        return ind.internalPointer()

    def returnSelFiles(self, cls=None):
        """
        Returns the files currently selected in the file list.
        Used for displaying the peak list, etc.
        """
        tab_sel = self.tree_view.selectionModel()
        files = []
        for i in tab_sel.selectedRows():
            obj = i.model().mapToSource(i).internalPointer()
            if cls is None or obj.db_type == cls:
                files.append(obj)
        return files

    def items_as_csv(self, itms, delim=',', incHeaders=True):
        flds = [self.fields[self.tree_view.header().logicalIndex(fld)]
                for fld in range(len(self.fields))]
        row_lst = []
        block_col = ['vis']
        for i in itms:
            col_lst = [i.info[col] for col in flds if col not in block_col]
            row_lst.append(delim.join(col_lst))

        if incHeaders:
            try:  # for python 2
                flds = [unicode(aston_fields[i]) for i in flds
                        if i not in ['vis']]
            except NameError:  # for python 3
                flds = [aston_fields[i] for i in flds if i not in ['vis']]
            header = delim.join(flds) + '\n'
            table = '\n'.join(row_lst)
            return header + table
