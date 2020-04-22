import os
from enum import Enum
from os import path

import mutagen
from PyQt5.QtCore import (Qt, pyqtSignal, QAbstractTableModel, QVariant, QFileInfo, QModelIndex, QMimeDatabase, QUrl)
from PyQt5.QtGui import QIcon, QCursor
from PyQt5.QtWidgets import QTableView, QAbstractItemView, QFileIconProvider, QMenu

import CommonUtils
from CommonUtils import human_readable_filesize, FileScanner
from TransCoda import MediaMetaData
from TransCoda.Encoda import EncodaStatus
from TransCoda.TransCodaSettings import TransCodaSettings


class OutputDirectoryNotSet(Exception):
    """Raise when the output folder is not set"""


class EncoderNotSelected(Exception):
    """Raise when the Encoder is not selected"""


class ItemKeys(Enum):
    input_file_name = "Input File"
    input_file_type = "Type"
    input_file_size = "Initial Size"
    input_duration = "Duration"
    input_bitrate = "Bitrate"
    input_encoder = "Encoding"
    output_file_dir = "Output Directory"
    output_file_name = "output_file_name"
    output_file_size = "Encoded File Size"
    icon = "Icon",
    status = "Status",
    encoder = "Encoder"
    messages = "Messages",
    encoder_command = "Encoder Command"
    percent_compete = "Percent Complete"

    def __init__(self, display_name):
        self.display_name = display_name


class MainPanel(QTableView):

    class FileItemModel(QAbstractTableModel):
        _value_not_set = "VALUE NOT SET"
        _encoder_not_set = "Encoder not selected"

        def __init__(self):
            super().__init__()
            self.mime_database = QMimeDatabase()
            self.file_items = []
            self.columnHeaders = [ItemKeys.input_file_name,
                                  ItemKeys.input_file_type,
                                  ItemKeys.input_file_size,
                                  ItemKeys.output_file_dir,
                                  ItemKeys.encoder,
                                  ItemKeys.output_file_size,
                                  ItemKeys.percent_compete]

        def rowCount(self, parent):
            return len(self.file_items)

        def columnCount(self, parent):
            return len(self.columnHeaders)

        def data(self, index, role=None):
            if not index.isValid():
                return QVariant()
            if role == Qt.DisplayRole:
                item = self.file_items[index.row()]
                header = self.columnHeaders[index.column()]
                if header in item:
                    return item[header]
                else:
                    return QVariant()

            elif role == Qt.DecorationRole:
                item = self.file_items[index.row()]
                if index.column() == 0:
                    return item[ItemKeys.icon]

            elif role == Qt.BackgroundRole:
                item = self.file_items[index.row()]
                if ItemKeys.status in item:
                    return item[ItemKeys.status].brush

        def headerData(self, p_int, orientation, role=None):
            if role == Qt.DisplayRole:
                if orientation == Qt.Horizontal:
                    return self.columnHeaders[p_int].display_name
                elif orientation == Qt.Vertical:
                    return p_int

        def add_rows(self, urls):
            items_to_add = self.create_entries(urls)
            last_index = len(self.file_items)
            self.beginInsertRows(QModelIndex(), last_index, last_index + len(items_to_add))
            for item in items_to_add:
                self.file_items.append(item)
            self.endInsertRows()
            return len(items_to_add)

        def remove_rows(self, indices):
            for index in indices:
                self.beginRemoveRows(QModelIndex(), index, index)
                del(self.file_items[index])
                self.endRemoveRows()

        def get_item(self, index, item_type):
            return self.file_items[index][item_type]

        def encoding_started(self, run_index):
            for index, item in enumerate(self.file_items):
                if run_index and index != run_index:
                    continue
                item[ItemKeys.status] = EncodaStatus.WAITING
                model_index_from = self.createIndex(index, 0)
                model_index_to = self.createIndex(index, len(self.columnHeaders))
                self.dataChanged.emit(model_index_from, model_index_to, [Qt.DisplayRole, Qt.BackgroundRole])

        def refresh_all_output_details(self):
            for index, item in enumerate(self.file_items):
                self.set_output_details(item)
                model_index_from = self.createIndex(index, 0)
                model_index_to = self.createIndex(index, len(self.columnHeaders))
                self.dataChanged.emit(model_index_from, model_index_to, [Qt.DisplayRole, Qt.BackgroundRole])

        def update_item(self, file_data):
            for index, item in enumerate(self.file_items):
                if item[ItemKeys.input_file_name] == file_data[ItemKeys.input_file_name]:
                    item[ItemKeys.status] = file_data[ItemKeys.status]
                    item[ItemKeys.messages] = file_data[ItemKeys.messages]
                    if path.exists(file_data[ItemKeys.output_file_name]):
                        item[ItemKeys.output_file_size] = \
                            human_readable_filesize(path.getsize(file_data[ItemKeys.output_file_name]))
                    model_index_from = self.createIndex(index, 0)
                    model_index_to = self.createIndex(index, len(self.columnHeaders))
                    self.dataChanged.emit(model_index_from, model_index_to, [Qt.DisplayRole, Qt.BackgroundRole])
                    # Do not process the rest of the list
                    return

        def update_item_percent_compete(self, input_file_name, total_time, completed_time):
            for index, item in enumerate(self.file_items):
                if item[ItemKeys.input_file_name] == input_file_name:
                    item[ItemKeys.percent_compete] = f"{(completed_time/total_time * 100):.2f}%"
                    model_index_from = self.createIndex(index, 0)
                    model_index_to = self.createIndex(index, len(self.columnHeaders))
                    self.dataChanged.emit(model_index_from, model_index_to, [Qt.DisplayRole])
                    # Do not process the rest of the list
                    return

        def update_item_status(self, item_index, new_status):
            model_index_from = self.createIndex(item_index, 0)
            model_index_to = self.createIndex(item_index, len(self.columnHeaders))
            self.file_items[item_index][ItemKeys.status] = new_status
            self.dataChanged.emit(model_index_from, model_index_to, [Qt.BackgroundRole])

        def generate_commands(self):
            for file_item in self.file_items:
                if ItemKeys.output_file_dir not in file_item \
                        or file_item[ItemKeys.output_file_dir] == self._value_not_set:
                    raise OutputDirectoryNotSet
                elif ItemKeys.encoder not in file_item \
                        or file_item[ItemKeys.encoder] == self._value_not_set:
                    raise EncoderNotSelected
                elif file_item[ItemKeys.status] == EncodaStatus.READY:
                    _input = file_item[ItemKeys.input_file_name]
                    _encoder = TransCodaSettings.get_encoder()
                    _, file = path.split(file_item[ItemKeys.input_file_name])
                    name, _ = path.splitext(file)
                    _output = path.join(file_item[ItemKeys.output_file_dir], name + _encoder.extension)
                    yield _input, _output, _encoder.command

        def create_entries(self, urls):
            items_to_add = []
            for q_url in urls:
                local_file = q_url.toLocalFile()

                tag_data = MediaMetaData.get_metatadata(local_file)
                if not os.path.isdir(local_file) and tag_data is not None:
                    info = QFileInfo(local_file)
                    item = {
                        ItemKeys.input_file_name: local_file,
                        ItemKeys.input_file_size: human_readable_filesize(info.size()),
                        ItemKeys.input_file_type: self.mime_database.mimeTypeForFile(local_file).name(),
                        ItemKeys.icon: QFileIconProvider().icon(info),
                        ItemKeys.status: EncodaStatus.READY,
                        # ItemKeys.input_bitrate: tag_data.info.bitrate,
                        # ItemKeys.input_duration: tag_data.info.length,
                        # if hasattr(tag_data.info, "codec"):
                        #     ItemKeys.input_encoder: tag_data.info.codec
                    }
                    self.set_output_details(item)
                    items_to_add.append(item)
            return items_to_add

        def set_output_details(self, file_item):
            output_dir = TransCodaSettings.get_output_dir()
            encoder = TransCodaSettings.get_encoder_name()
            preserve_dir = TransCodaSettings.get_preserve_dir()

            # Set all default values first
            file_item[ItemKeys.output_file_dir] = self._value_not_set
            file_item[ItemKeys.encoder] = self._value_not_set

            if output_dir is not None:
                _, file_path = path.splitdrive(file_item[ItemKeys.input_file_name])
                file_path, file = path.split(file_path)
                if preserve_dir:
                    file_item[ItemKeys.output_file_dir] = output_dir + file_path
                else:
                    file_item[ItemKeys.output_file_dir] = output_dir

            if encoder is not None:
                file_item[ItemKeys.encoder] = encoder

            return file_item

    files_changed_event = pyqtSignal(bool, int)
    menu_item_event = pyqtSignal(str, int)

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.verticalHeader().hide()
        self.horizontalHeader().setHighlightSections(False)
        self.horizontalHeader().setSectionsMovable(True)
        self.file_model = None
        self.clear_table()
        TransCodaSettings.settings_container.settings_change_event.connect(self.settings_changed)
        self.menu = self.create_context_menu()

    def create_context_menu(self):
        menu = QMenu()
        menu.addAction(CommonUtils.create_action(self, "Open", self.menu_item_selected,
                                                 icon=QIcon.fromTheme("document-open")))
        menu.addAction(CommonUtils.create_action(self, "Remove", self.menu_item_selected,
                                                 icon=QIcon.fromTheme("list-remove")))
        menu.addSeparator()
        menu.addAction(CommonUtils.create_action(self, "Encode", self.menu_item_selected,
                                                 icon=QIcon.fromTheme("media-playback-start")))
        submenu = menu.addMenu("Change Status")
        submenu.addAction(CommonUtils.create_action(self, EncodaStatus.SUCCESS.name, self.menu_item_selected,
                                                    icon=QIcon.fromTheme("face-smile")))
        submenu.addAction(CommonUtils.create_action(self, EncodaStatus.READY.name, self.menu_item_selected,
                                                    icon=QIcon.fromTheme("face-plain")))
        return menu

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
            self.add_files(event.mimeData().urls())
        else:
            event.ignore()

    def contextMenuEvent(self, event):
        if self.selectedIndexes() and self.selectedIndexes()[0].row() >= 0:
            self.menu.exec(QCursor.pos())

    def add_files(self, files):
        scanner = FileScanner(files, recurse=True, is_qfiles=True)
        files_to_add = []
        for file in scanner.files:
            files_to_add.append(QUrl(f"file://{file}"))
        total_items_added = self.file_model.add_rows(files_to_add)
        self.file_model.layoutChanged.emit()
        self.adjust_columns()
        self.files_changed_event.emit(True, total_items_added)

    def remove_files(self, indices):
        self.file_model.remove_rows(indices)

    def clear_table(self):
        self.file_model = MainPanel.FileItemModel()
        self.setModel(self.file_model)

    def adjust_columns(self):
        for i in range(self.file_model.columnCount(self)):
            self.resizeColumnToContents(i)

    def generate_commands(self):
        return self.file_model.generate_commands()

    def encoding_started(self, run_index):
        self.file_model.encoding_started(run_index)

    def update_item(self, file_data):
        self.file_model.update_item(file_data)

    def update_item_percent_compete(self, input_file_name, total_time, completed_time):
        self.file_model.update_item_percent_compete(input_file_name, total_time, completed_time)

    def update_item_status(self, item_index, new_status):
        self.file_model.update_item_status(item_index, new_status)

    def settings_changed(self, setting, value):
        print(f"Setting {setting} changed to {value}")
        self.file_model.refresh_all_output_details()

    def menu_item_selected(self, item_name):
        selected = self.selectedIndexes()
        if selected and selected[0].row() >= 0:
            self.menu_item_event.emit(item_name, selected[0].row())


