from PyQt5.QtCore import QAbstractTableModel, QVariant, Qt, QModelIndex


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
            if index.column() < len(self.columnHeaders):
                return item[index.column()]
            else:
                return QVariant()

        elif role == Qt.DecorationRole:
            # item = self.file_items[index.row()]
            # if index.column() == 0:
            #     return QFileIconProvider().icon(item.file_info)
            print("TODO-Sheldon - Generate Image thumbnails - in a separate thread")

    def headerData(self, p_int, orientation, role=None):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self.columnHeaders[p_int]
            elif orientation == Qt.Vertical:
                return p_int

    def append_row(self, file_dir, file_name):
        last_index = len(self.file_items)
        self.beginInsertRows(QModelIndex(), last_index, last_index + 1)
        self.file_items.append((file_dir, file_name))
        self.endInsertRows()

    def update_view(self, index):
        self.dataChanged.emit(QModelIndex(), QModelIndex(), [])
