import os

from PyQt5 import QtCore
from PyQt5.QtCore import QModelIndex, Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QStyledItemDelegate


class DuplicateImageDisplayDelegate(QStyledItemDelegate):

    _dimension_x = 96
    _dimension_y = 96

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.image_cache = {}

    def sizeHint(self, option, index):
        return QtCore.QSize(self._dimension_x + 4, self._dimension_y + 4)

    def paint(self, painter, option, index):
        data = index.data()
        print(data)
        if self.image_cache.__contains__(data):
            painter.drawPixmap(option.rect.topLeft(), self.image_cache[data])
        elif data is not None and os.path.exists(data):
            pixmap = QPixmap(data).scaled(self._dimension_x, self._dimension_y, Qt.KeepAspectRatio)
            self.image_cache[data] = pixmap
            painter.drawPixmap(option.rect.topLeft(), pixmap)


class DuplicateImageDisplayModel(QtCore.QAbstractTableModel):

    def __init__(self):
        super().__init__()
        self.dupes_list = []
        self.column_count = 0

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.dupes_list)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return self.column_count

    def data(self, index, role=None):
        if not index.isValid():
            return QtCore.QVariant()
        if role == QtCore.Qt.DisplayRole:
            if len(self.dupes_list[index.row()]) <= index.column():
                return None
            else:
                return self.dupes_list[index.row()][index.column()]

    def add_items(self, items, cohort):
        self.beginInsertRows(QModelIndex(), cohort, cohort + 1)
        if cohort < len(self.dupes_list):
            # A new cohort was inserted
            self.dupes_list[cohort] = items
        else:
            # An existing cohort was updated
            self.dupes_list.append(items)

        self.endInsertRows()

        items_len = len(items)
        if items_len > self.column_count:
            self.beginInsertColumns(QModelIndex(), self.column_count, items_len)
            self.column_count = items_len
            self.endInsertColumns()
