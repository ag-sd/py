from PyQt5.QtCore import QAbstractTableModel, Qt, QVariant, QModelIndex
from PyQt5.QtWidgets import QFileIconProvider
from datetime import datetime

STR_DATE_TIME_FORMAT = '%c'


class FileItemModel(QAbstractTableModel):
    def __init__(self):
        super().__init__()
        self.file_items = []
        self.columnHeaders = ["File Name", "File Path", "File Size",
                              "Start", "Finish", "Encoder"]

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
                return item.file_name
            elif index.column() == 1:
                return item.file_path
            elif index.column() == 2:
                return item.file_size
            elif index.column() == 3:
                if type(item.start_time) is datetime:
                    return item.start_time.strftime(STR_DATE_TIME_FORMAT)
                return "-"
            elif index.column() == 4:
                if type(item.end_time) is datetime:
                    return item.end_time.strftime(STR_DATE_TIME_FORMAT)
                return "-"
            elif index.column() == 5:
                return item.codec
            else:
                return QVariant()

        elif role == Qt.DecorationRole:
            item = self.file_items[index.row()]
            if index.column() == 0:
                return QFileIconProvider().icon(item.file_info)

    def headerData(self, p_int, orientation, role=None):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self.columnHeaders[p_int]
            elif orientation == Qt.Vertical:
                return p_int

    def appendRow(self, entry):
        last_index = len(self.file_items)
        self.beginInsertRows(QModelIndex(), last_index, last_index + 1)
        self.file_items.append(entry)
        self.endInsertRows()

    def updateView(self, index):
        self.dataChanged.emit(QModelIndex(), QModelIndex(), [])

