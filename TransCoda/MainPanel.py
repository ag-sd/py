import os
from os import path

from PyQt5.QtCore import (Qt, pyqtSignal, QAbstractTableModel, QVariant, QFileInfo, QModelIndex, QMimeDatabase)
from PyQt5.QtGui import QBrush
from PyQt5.QtWidgets import QTableView, QAbstractItemView, QFileIconProvider

from CommonUtils import human_readable_filesize
from TransCoda.Encoda import EncodaStatus
from TransCoda.TransCodaSettings import TransCodaSettings


class OutputDirectoryNotSet(Exception):
    """Raise when the output folder is not set"""


class EncoderNotSelected(Exception):
    """Raise when the Encoder is not selected"""


class MainPanel(QTableView):

    class FileItemModel(QAbstractTableModel):
        _value_not_set = "VALUE NOT SET"

        def __init__(self):
            super().__init__()
            self.mime_database = QMimeDatabase()
            self.file_items = []
            self.columnHeaders = ["Input File", "Type", "File Size",
                                  "Output File", "Type", "File Size"]

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
                    return item['input_file_name']
                elif index.column() == 1:
                    return item['input_file_type']
                elif index.column() == 2:
                    return item['input_file_size']
                elif index.column() == 3:
                    return item['output_file_name']
                elif index.column() == 4:
                    return item['output_file_type']
                elif index.column() == 5:
                    if "output_file_size" in item:
                        return item['output_file_size']
                else:
                    return QVariant()

            elif role == Qt.DecorationRole:
                item = self.file_items[index.row()]
                if index.column() == 0:
                    return item['icon']

            elif role == Qt.BackgroundRole:
                item = self.file_items[index.row()]
                if item["status"] == EncodaStatus.WAITING:
                    return QBrush(EncodaStatus.WAITING.color)
                elif item["status"] == EncodaStatus.ERROR:
                    return QBrush(EncodaStatus.ERROR.color)
                elif item["status"] == EncodaStatus.SUCCESS:
                    return QBrush(EncodaStatus.SUCCESS.color)

        def headerData(self, p_int, orientation, role=None):
            if role == Qt.DisplayRole:
                if orientation == Qt.Horizontal:
                    return self.columnHeaders[p_int]
                elif orientation == Qt.Vertical:
                    return p_int

        def add_rows(self, urls):
            last_index = len(self.file_items)
            self.beginInsertRows(QModelIndex(), last_index, last_index + len(urls))
            for q_url in urls:
                local_file = q_url.toLocalFile()
                mime_type = self.mime_database.mimeTypeForFile(local_file).name()
                if not os.path.isdir(local_file) and mime_type.upper().startswith("AUDIO"):
                    info = QFileInfo(local_file)
                    item = {
                        "input_file_name": local_file,
                        "input_file_size": human_readable_filesize(info.size()),
                        "input_file_type": self.mime_database.mimeTypeForFile(local_file).name(),
                        "icon": QFileIconProvider().icon(info),
                        "status": EncodaStatus.READY
                    }
                    self.set_output_details(item)
                    self.file_items.append(item)
            self.endInsertRows()

        def encoding_started(self):
            for index, item in enumerate(self.file_items):
                item["status"] = EncodaStatus.WAITING
                model_index_from = self.createIndex(index, 0)
                model_index_to = self.createIndex(index, len(self.columnHeaders))
                self.dataChanged.emit(model_index_from, model_index_to, [Qt.DisplayRole, Qt.BackgroundRole])

        def update_item(self, file_data):
            for index, item in enumerate(self.file_items):
                if item["input_file_name"] == file_data["input_file_name"]:
                    item["status"] = file_data["status"]
                    item["messages"] = file_data["messages"]
                    if path.exists(file_data["output_file_name"]):
                        item["output_file_size"] = human_readable_filesize(path.getsize(file_data["output_file_name"]))
                    model_index_from = self.createIndex(index, 0)
                    model_index_to = self.createIndex(index, len(self.columnHeaders))
                    self.dataChanged.emit(model_index_from, model_index_to, [Qt.DisplayRole, Qt.BackgroundRole])

        def generate_commands(self):
            for file_item in self.file_items:
                yield file_item['input_file_name'], file_item['output_file_name'], file_item['encoder_command']

        def set_output_details(self, file_item):
            output_dir = TransCodaSettings.get_output_dir()
            encoder = TransCodaSettings.get_encoder()
            preserve_dir = TransCodaSettings.get_preserve_dir()
            if output_dir is None or encoder is None:
                file_item['output_file_name'] = self._value_not_set
                file_item['output_file_type'] = self._value_not_set
                return file_item

            _, file_path = path.splitdrive(file_item['input_file_name'])
            file_path, file = path.split(file_path)
            name, ext = os.path.splitext(file)

            if preserve_dir:
                output_path = path.join(output_dir + file_path, name + encoder["extension"])
            else:
                output_path = path.join(output_dir, name + encoder["extension"])

            file_item['output_file_name'] = output_path
            file_item['output_file_type'] = self.mime_database.mimeTypeForFile(output_path).name()
            file_item['encoder_command'] = encoder["command"]
            return file_item

    file_drop_event = pyqtSignal('PyQt_PyObject')

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.verticalHeader().hide()
        self.horizontalHeader().setHighlightSections(False)
        self.file_model = None
        self.clear_table()
        TransCodaSettings.settings_container.settings_change_event.connect(self.settings_changed)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls:
            event.setDropAction(Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls:
            self.file_model.add_rows(event.mimeData().urls())
            # FIXME: Expand directories
            self.file_drop_event.emit(event.mimeData().urls())
            self.adjust_columns()
        else:
            event.ignore()

    def add_files(self, files):
        self.file_model.add_rows(files)
        self.file_model.layoutChanged.emit()
        self.adjust_columns()

    def clear_table(self):
        self.file_model = MainPanel.FileItemModel()
        self.setModel(self.file_model)

    def adjust_columns(self):
        for i in range(self.file_model.columnCount(self)):
            self.resizeColumnToContents(i)

    def generate_commands(self):
        return self.file_model.generate_commands()

    def encoding_started(self):
        self.file_model.encoding_started()

    def update_item(self, file_data):
        self.file_model.update_item(file_data)

    @staticmethod
    def settings_changed(setting, value):
        print(f"Setting {setting} changed to {value}")