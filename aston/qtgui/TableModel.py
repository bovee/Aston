from contextlib import contextmanager
from PyQt5 import QtGui, QtCore, QtWidgets
from aston.qtgui.Fields import aston_fields, aston_field_opts


class TableModel(QtCore.QAbstractItemModel):
    def __init__(self, database=None, tree_view=None,
                 master_window=None, *args):
        #super(TableModel, self).__init__(self, *args)
        QtCore.QAbstractItemModel.__init__(self, *args)

        self.db = database
        self.master_window = master_window

        if tree_view is None:
            return
        else:
            self.tree_view = tree_view

        # inheritors need to set up self.field and self._children
        self.fields = []
        self._children = []

        #tree_view.setModel(self)

        # set up proxy model
        self.proxy_mod = FilterModel()
        self.proxy_mod.setSourceModel(self)
        self.proxy_mod.setDynamicSortFilter(True)
        self.proxy_mod.setFilterKeyColumn(0)
        self.proxy_mod.setFilterCaseSensitivity(False)
        tree_view.setModel(self.proxy_mod)
        tree_view.setSortingEnabled(True)
        self.proxy_mod.sort(0, QtCore.Qt.AscendingOrder)

        ##deal with combo boxs in table
        #self.cDelegates = {}
        #self.enableComboCols()

    def index(self, row, column, parent):
        if row < 0 or column < 0 or column > len(self.fields):
            # item is out of bounds; return blank QModelIndex
            return QtCore.QModelIndex()

        if not parent.isValid() and row < len(self._children):
            # at the root level
            return self.createIndex(row, column, self._children[row])
        elif parent.column() == 0:
            children = parent.internalPointer()._children
            if row >= len(children):
                return QtCore.QModelIndex()
            return self.createIndex(row, column, children[row])

        # just in case something else falls through
        return QtCore.QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()
        obj = index.internalPointer()
        parent = obj._parent
        if parent is None:
            return QtCore.QModelIndex()
        elif parent in self._children:
            row = self._children.index(parent)
        elif parent._parent is not None:
            row = parent._parent._children.index(parent)
        else:
            # fall through
            return QtCore.QModelIndex()
        return self.createIndex(row, 0, parent)

    def rowCount(self, parent):
        if not parent.isValid():
            return len(self._children)
        elif parent.column() == 0:
            return len(parent.internalPointer()._children)
        return 0

    def columnCount(self, parent):
        return len(self.fields)

    def headerData(self, col, orientation, role):
        if orientation == QtCore.Qt.Horizontal and \
                role == QtCore.Qt.DisplayRole:
            if self.fields[col] in aston_fields:
                return aston_fields[self.fields[col]]
            else:
                return self.fields[col]
        else:
            return None

    @contextmanager
    def add_rows(self, parent, nrows):
        if parent is None:
            row = len(self._children)
        else:
            row = len(parent._children)
        pidx = self._obj_to_index(parent)
        self.beginInsertRows(pidx, row, row + nrows - 1)
        yield
        self.endInsertRows()

    @contextmanager
    def del_row(self, obj):
        parent = obj._parent
        if parent is None:
            row = self._children.index(obj)
        else:
            row = parent._children.index(obj)
        pidx = self._obj_to_index(parent)
        self.beginRemoveRows(pidx, row, row)
        yield
        self.endRemoveRows()

    def _obj_to_index(self, obj, col=0):
        if obj is None:
            return QtCore.QModelIndex()
        elif obj in self._children:
            row = self._children.index(obj)
            return self.createIndex(row, col, obj)
        elif obj._parent is not None:
            row = obj._parent._children.index(obj)
            return self.createIndex(row, col, obj)
        else:
            return QtCore.QModelIndex()

    def update_combo_cols(self):
        set_delegate = self.tree_view.setItemDelegateForColumn
        for c in aston_field_opts:
            if c in self.fields and c not in self.combo_delegates:
                # new column, need to add combo support in
                opts = list(aston_field_opts[c].values())
                self.combo_delegates[c] = (self.fields.index(c),
                                           ComboDelegate(opts))
                set_delegate(*self.combo_delegates[c])
            elif c not in self.fields and c in self.combo_delegates:
                # column has been deleted, remove from delegate list
                set_delegate(self.combo_delegates[c][0],
                             self.tree_view.itemDelegate())
                del self.combo_delegates[c]


class FilterModel(QtCore.QSortFilterProxyModel):
    def __init__(self, parent=None):
        super(FilterModel, self).__init__(parent)

#    def filterAcceptsRow(self, row, index):
#        #if index.internalPointer() is not None:
#        #    db_type = index.internalPointer().db_type
#        #    if db_type == 'file':
#        #        return super(FilterModel, self).filterAcceptsRow(row, index)
#        #    else:
#        #        return True
#        #else:
#        return super(FilterModel, self).filterAcceptsRow(row, index)
#
#    def lessThan(self, left, right):
#        def breakup(key):
#            return [int(c) if c.isdigit() else c.lower()
#                    for c in re.split('([0-9]+)', key)]
#        return breakup(str(left.data())) < breakup(str(right.data()))


class ComboDelegate(QtWidgets.QItemDelegate):
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
