import os
from collections import Mapping
from enum import Enum
from os import path

from PyQt5.QtCore import (Qt, pyqtSignal, QAbstractTableModel, QVariant, QFileInfo, QModelIndex, QMimeDatabase, QUrl)
from PyQt5.QtGui import QIcon, QCursor
from PyQt5.QtWidgets import QTableView, QAbstractItemView, QFileIconProvider, QMenu

import CommonUtils
from TransCoda.Encoda import EncodaStatus
from TransCoda.TransCodaSettings import TransCodaSettings


class OutputDirectoryNotSet(Exception):
    """Raise when the output folder is not set"""


class EncoderNotSelected(Exception):
    """Raise when the Encoder is not selected"""


class ItemKeys(Enum):
    __headers__ = []

    input_file_name = "Input File", True
    input_file_type = "Type", True
    input_file_size = "Initial Size", True
    input_duration = "Duration", True
    input_bitrate = "Bitrate", True
    input_encoder = "Encoding", True
    output_file_dir = "Output Directory", True
    output_file_name = "output_file_name", False
    output_file_size = "Encoded File Size", True
    icon = "Icon", False
    status = "Status", True
    encoder = "Encoder", True
    messages = "Messages", True
    encoder_command = "Encoder Command", False
    percent_compete = "Percent Complete", True
    cpu_time = "CPU Time", True
    compression_ratio = "Compression Ratio", True,
    sample_rate = "Sample Rate", True
    channels = "Channels", True
    album_artist = "Album Artist", True
    artist = "Artist", True
    title = "Title", True
    album = "Album", True
    track = "Track", True
    genre = "Genre", True

    def __init__(self, display_name, header):
        self.display_name = display_name
        if header:
            self.__class__.__headers__.append(self)


class MainPanel(QTableView):
    class InterceptingDict(dict):
        def __init__(self):
            super().__init__()

        def __setitem__(self, key, value):
            if key == ItemKeys.input_file_size or key == ItemKeys.output_file_size:
                value = CommonUtils.human_readable_filesize(value)
            elif key == ItemKeys.input_bitrate:
                value = f"{int(value)/1000:.{0}f} KBit/s"
            elif key == ItemKeys.input_duration or key == ItemKeys.cpu_time:
                value = CommonUtils.human_readable_time(value)
            elif key == ItemKeys.compression_ratio:
                value = f"{value:.{2}f}%"
            super().__setitem__(key, value)

        def update(self, other=None, **kwargs):
            if other is not None:
                for k, v in other.items() if isinstance(other, Mapping) else other:
                    self[k] = v
            for k, v in kwargs.items():
                self[k] = v

    class FileItemModel(QAbstractTableModel):
        _value_not_set = "VALUE NOT SET"
        _encoder_not_set = "Encoder not selected"

        def __init__(self):
            super().__init__()
            self.mime_database = QMimeDatabase()
            self.executor = None
            self.file_items = []
            self.columnHeaders = [ItemKeys.input_file_name,
                                  ItemKeys.input_file_type,
                                  ItemKeys.input_file_size,
                                  ItemKeys.input_bitrate,
                                  ItemKeys.input_duration,
                                  ItemKeys.input_encoder,
                                  ItemKeys.output_file_dir,
                                  ItemKeys.encoder,
                                  ItemKeys.output_file_size,
                                  ItemKeys.compression_ratio,
                                  ItemKeys.cpu_time,
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

        def update_items(self, item_data):
            for item in item_data:
                index = self.find_item(item[ItemKeys.input_file_name])
                if index is not None:
                    file_item = self.file_items[index]
                    file_item.update(item)
                    model_index_from = self.createIndex(index, 0)
                    model_index_to = self.createIndex(index, len(self.columnHeaders))
                    self.dataChanged.emit(model_index_from, model_index_to, [Qt.DisplayRole, Qt.BackgroundRole])

        def update_item_status(self, item_index, new_status):
            model_index_from = self.createIndex(item_index, 0)
            model_index_to = self.createIndex(item_index, len(self.columnHeaders))
            self.file_items[item_index][ItemKeys.status] = new_status
            self.dataChanged.emit(model_index_from, model_index_to, [Qt.BackgroundRole])

        def get_columns(self):
            return self.columnHeaders

        def add_column(self, column):
            self.beginInsertColumns(QModelIndex(), len(self.columnHeaders), len(self.columnHeaders))
            self.columnHeaders.append(column)
            self.endInsertColumns()

        def remove_column(self, column):
            del_index = -1
            for index, col in enumerate(self.columnHeaders):
                if col == column:
                    del_index = index
                    break
            if del_index >= 0:
                self.beginRemoveColumns(QModelIndex(), del_index, del_index)
                del(self.columnHeaders[del_index])
                self.endRemoveColumns()

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

                if not os.path.isdir(local_file) and self.find_item(local_file) is None:
                    info = QFileInfo(local_file)
                    mime = self.mime_database.mimeTypeForFile(local_file).name().upper()
                    if not(mime.startswith("AUDIO") or mime.startswith("VIDEO")):
                        continue
                    item = MainPanel.InterceptingDict()
                    item[ItemKeys.input_file_name] = local_file
                    item[ItemKeys.input_file_type] = self.mime_database.mimeTypeForFile(local_file).name()
                    item[ItemKeys.icon] = QFileIconProvider().icon(info)
                    item[ItemKeys.status] = EncodaStatus.READY

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

        def find_item(self, fname):
            for index, item in enumerate(self.file_items):
                if item[ItemKeys.input_file_name] == fname:
                    return index
            return None

    files_changed_event = pyqtSignal(bool, 'PyQt_PyObject')
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
        self.horizontalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.horizontalHeader().customContextMenuRequested.connect(self.get_header_context_menu)
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
            self.files_changed_event.emit(True, event.mimeData().urls())
        else:
            event.ignore()

    def contextMenuEvent(self, event):
        if self.selectedIndexes() and self.selectedIndexes()[0].row() >= 0:
            self.menu.exec(QCursor.pos())

    def add_qurls(self, qurls):
        total_added = self.file_model.add_rows(qurls)
        self.file_model.layoutChanged.emit()
        self.adjust_columns()
        return total_added

    def remove_files(self, indices):
        self.file_model.remove_rows(indices)
        self.files_changed_event.emit(False, len(indices))

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

    def update_items(self, file_data):
        self.file_model.update_items(file_data)
        self.adjust_columns()

    def update_item_status(self, item_index, new_status):
        self.file_model.update_item_status(item_index, new_status)

    def settings_changed(self, setting, value):
        self.file_model.refresh_all_output_details()

    def menu_item_selected(self, item_name):
        selected = self.selectedIndexes()
        if selected and selected[0].row() >= 0:
            self.menu_item_event.emit(item_name, selected[0].row())

    def get_header_context_menu(self, event):
        # Get Available Headers
        available = sorted(ItemKeys.__headers__, key=lambda key: key.display_name)
        # Get Selected Headers
        selected = self.file_model.get_columns()
        # Build Menu
        menu = QMenu()
        for column in available:
            checked = selected.__contains__(column)
            menu.addAction(CommonUtils.create_action(self, column.display_name,
                                                     self.column_header_selection, checked=checked))
        menu.exec(QCursor.pos())

    def column_header_selection(self, item_name):
        for column in self.file_model.get_columns():
            if column.display_name == item_name:
                # Remove
                self.file_model.remove_column(column)
                return
        # if column was not found, add it
        for column in ItemKeys:
            if column.display_name == item_name:
                self.file_model.add_column(column)
                return


