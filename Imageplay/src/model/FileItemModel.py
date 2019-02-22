from os import path

from PyQt5.QtCore import QAbstractTableModel, QVariant, Qt, QModelIndex, QFileInfo
from PyQt5.QtWidgets import QFileIconProvider


class FileItemModel(QAbstractTableModel):

    def __init__(self):
        super().__init__()
        self.file_items = []
        self.columnHeaders = ["File Path", "File Name"]

    def rowCount(self, parent):
        return len(self.file_items)

    def columnCount(self, parent):
        return len(self.columnHeaders)

    def data(self, index, role=None):
        if not index.isValid():
            return QVariant()
        if role == Qt.DisplayRole:
            item = self.file_items[index.row()]
            if index.column() == 0:
                return item.absolutePath()
            elif index.column() == 1:
                return item.fileName()
            else:
                return QVariant()

        elif role == Qt.DecorationRole:
            item = self.file_items[index.row()]
            if index.column() == 0:
                return QFileIconProvider().icon(item)

    def headerData(self, p_int, orientation, role=None):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self.columnHeaders[p_int]
            elif orientation == Qt.Vertical:
                return p_int

    def append_rows(self, files):
        last_index = len(self.file_items)
        self.beginInsertRows(QModelIndex(), last_index, last_index + len(files))
        for file in files:
            self.file_items.append(QFileInfo(file))
        self.endInsertRows()

    def update_view(self, index):
        self.dataChanged.emit(QModelIndex(), QModelIndex(), [])
