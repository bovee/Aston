from PyQt5 import QtCore


class QuantPeakTable(QtCore.QAbstractTableModel):
    def __init__(self, parent=None):
        self.parent = parent

    def rowCount(self):
        return len(self.peaks)

    def columnCount(self):
        return 3

    def data(self, idx, role):
        return 'T'

    def headerData(self, col):
        return ['Peak', 'Abund', 'D13C'][col]
