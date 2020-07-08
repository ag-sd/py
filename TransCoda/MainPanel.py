import os
from collections import Mapping
from enum import Enum

from PyQt5.QtCore import (Qt, pyqtSignal, QAbstractTableModel, QVariant, QFileInfo, QModelIndex, QMimeDatabase,
                          QMargins)
from PyQt5.QtGui import QIcon, QCursor, QPalette
from PyQt5.QtWidgets import QTableView, QAbstractItemView, QFileIconProvider, QMenu, QStyledItemDelegate, \
    QStyleOptionProgressBar, QApplication, QStyle

import CommonUtils
from TransCoda import TransCodaSettings
from TransCoda.Encoda import EncodaStatus
from TransCoda.TransCodaSettings import SettingsKeys


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
    output_file_dir = "Output Dir.", True
    output_file_name = "output_file_name", False
    output_file_size = "Encoded Size", True
    icon = "Icon", False
    status = "Status", True
    encoder = "Encoder", True
    messages = "Messages", True
    encoder_command = "Encoder Command", False
    percent_compete = "Progress", True
    cpu_time = "CPU Time", True
    compression_ratio = "Ratio", True,
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

    class ProgressBarDelegate(QStyledItemDelegate):
        def __init__(self, parent=None):
            super().__init__(parent)

        def paint(self, painter, option, index):
            column_key = self.parent().get_column_key(index.column())
            if column_key == ItemKeys.percent_compete:
                column_value = self.parent().get_items(index=index.row(), item_type=column_key)
                if not column_value:
                    # If no progress value, just let the system draw the value
                    super().paint(painter, option, index)
                    return
                progressbar_options = QStyleOptionProgressBar()
                progressbar_options.rect = option.rect.marginsRemoved(QMargins(1, 1, 1, 1))
                progressbar_options.minimum = 0
                progressbar_options.maximum = 100
                progressbar_options.textAlignment = Qt.AlignCenter
                progressbar_options.progress = float(column_value.replace("%", ""))
                progressbar_options.text = column_value
                progressbar_options.textVisible = True
                QApplication.style().drawControl(QStyle.CE_ProgressBar, progressbar_options, painter)
            else:
                super().paint(painter, option, index)

    class FileItemModel(QAbstractTableModel):
        _value_not_set = "VALUE NOT SET"
        _encoder_not_set = "Encoder not selected"

        def __init__(self):
            super().__init__()
            self.mime_database = QMimeDatabase()
            self.executor = None
            self.file_items = []
            self.columnHeaders = [ItemKeys.input_file_name,
                                  ItemKeys.input_file_size,
                                  ItemKeys.input_bitrate,
                                  ItemKeys.input_duration,
                                  ItemKeys.percent_compete,
                                  ItemKeys.input_encoder,
                                  ItemKeys.output_file_dir,
                                  ItemKeys.output_file_size,
                                  ItemKeys.compression_ratio,
                                  ItemKeys.cpu_time,
                                  ItemKeys.input_file_type]
            palette = QPalette()
            self._default_foreground = palette.brush(QPalette.Active, QPalette.WindowText)

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
                if ItemKeys.status in item and item[ItemKeys.status].is_background:
                    return item[ItemKeys.status].brush
            elif role == Qt.ForegroundRole:
                item = self.file_items[index.row()]
                if ItemKeys.status in item and item[ItemKeys.status].is_foreground:
                    return item[ItemKeys.status].brush
                else:
                    return self._default_foreground

        def headerData(self, p_int, orientation, role=None):
            if role == Qt.DisplayRole:
                if orientation == Qt.Horizontal:
                    return self.columnHeaders[p_int].display_name
                elif orientation == Qt.Vertical:
                    return p_int

        def sort(self, col, order=Qt.AscendingOrder):
            self.file_items.sort(
                key=lambda x: x[self.columnHeaders[col]],
                reverse=False if order == Qt.AscendingOrder else True)
            self.dataChanged.emit(QModelIndex(), QModelIndex())

        def add_rows(self, urls):
            items_to_add = self.create_entries(urls)
            return self.set_items(items_to_add)

        def remove_rows(self, indices):
            # sort indices and remove the largest first
            for index in sorted(indices, reverse=True):
                self.beginRemoveRows(QModelIndex(), index, index)
                del(self.file_items[index])
                self.endRemoveRows()

        def get_items(self, index=None, item_type=None):
            if index is not None:
                return self.file_items[index][item_type] if item_type in self.file_items[index] else None
            else:
                items_copy = []
                for item in self.file_items:
                    if item_type is not None and item_type in item:
                        copy = item[item_type]
                    else:
                        copy = item.copy()
                        del(copy[ItemKeys.icon])
                    items_copy.append(copy)
                return items_copy

        def set_items(self, items_to_add):
            last_index = len(self.file_items)
            self.beginInsertRows(QModelIndex(), last_index, last_index + len(items_to_add))
            for item in items_to_add:
                # This cannot be pickled, so add it separately
                info = QFileInfo(item[ItemKeys.input_file_name])
                item[ItemKeys.icon] = QFileIconProvider().icon(info)
                self.file_items.append(item)
            self.endInsertRows()
            return len(items_to_add)

        def encoding_started(self, run_index):
            for index, item in enumerate(self.file_items):
                if run_index and index != run_index:
                    continue
                if item[ItemKeys.status] != EncodaStatus.READY:
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
            updated_rows = set()
            for item in item_data:
                index = self.find_item(item[ItemKeys.input_file_name])
                if index is not None:
                    file_item = self.file_items[index]
                    file_item.update(item)
                    model_index_from = self.createIndex(index, 0)
                    model_index_to = self.createIndex(index, len(self.columnHeaders))
                    self.dataChanged.emit(model_index_from, model_index_to, [Qt.DisplayRole, Qt.BackgroundRole])
                    updated_rows.add(index)
            max_row = sorted(updated_rows)[-1]
            return self.createIndex(max_row, 0)

        def update_item_status(self, item_indices, new_status):
            for index in item_indices:
                model_index_from = self.createIndex(index, 0)
                model_index_to = self.createIndex(index, len(self.columnHeaders))
                self.file_items[index][ItemKeys.status] = new_status
                self.dataChanged.emit(model_index_from, model_index_to, [Qt.BackgroundRole])

        def get_column_key(self, index):
            return self.columnHeaders[index]

        def get_columns(self):
            return self.columnHeaders

        def add_column(self, column):
            self.beginInsertColumns(QModelIndex(), len(self.columnHeaders), len(self.columnHeaders))
            self.columnHeaders.append(column)
            self.endInsertColumns()
            return len(self.columnHeaders) - 1

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

        def create_entries(self, urls):
            items_to_add = []
            for q_url in urls:
                local_file = q_url.toLocalFile()

                if not os.path.isdir(local_file) and self.find_item(local_file) is None:
                    # info = QFileInfo(local_file)
                    mime = self.mime_database.mimeTypeForFile(local_file).name().upper()
                    if not(mime.startswith("AUDIO") or mime.startswith("VIDEO")):
                        continue
                    item = MainPanel.InterceptingDict()
                    item[ItemKeys.input_file_name] = local_file
                    item[ItemKeys.input_file_type] = self.mime_database.mimeTypeForFile(local_file).name()
                    # item[ItemKeys.icon] = QFileIconProvider().icon(info)
                    item[ItemKeys.status] = EncodaStatus.READING_METADATA
                    self.set_output_details(item)
                    items_to_add.append(item)
            return items_to_add

        def set_output_details(self, file_item):
            output_dir = TransCodaSettings.get_output_dir()
            encoder = TransCodaSettings.get_encoder_name()

            # Set all default values first
            file_item[ItemKeys.output_file_dir] = self._value_not_set
            file_item[ItemKeys.encoder] = self._value_not_set

            if output_dir is not None:
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
    menu_item_event = pyqtSignal(str, set)

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.verticalHeader().setDefaultSectionSize(self.verticalHeader().fontMetrics().height() + 3)
        self.verticalHeader().hide()
        self.horizontalHeader().setHighlightSections(False)
        self.horizontalHeader().setSectionsMovable(True)
        self.horizontalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.horizontalHeader().customContextMenuRequested.connect(self.get_header_context_menu)
        self.horizontalHeader().setSectionsClickable(True)
        self.setSortingEnabled(True)
        self.file_model = None
        self.clear_table()
        TransCodaSettings.settings.settings_change_event.connect(self.settings_changed)
        self.menu = self.create_context_menu()
        # self.attribute_table_view.setItemDelegateForColumn(column_icon, delegate)
        self.progressbarDelegate = MainPanel.ProgressBarDelegate(parent=self)
        self.setItemDelegate(self.progressbarDelegate)

    def create_context_menu(self):
        menu = QMenu()
        menu.addAction(CommonUtils.create_action(self, "Open", self.menu_item_selected,
                                                 icon=QIcon.fromTheme("document-open")))
        menu.addAction(CommonUtils.create_action(self, "Remove", self.menu_item_selected,
                                                 icon=QIcon.fromTheme("list-remove")))
        menu.addAction(CommonUtils.create_action(self, "Clear All", self.menu_item_selected,
                                                 icon=QIcon.fromTheme("edit-delete")))
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

    # def generate_commands(self):
    #     return self.file_model.generate_commands()

    def encoding_started(self, run_index):
        self.file_model.encoding_started(run_index)

    def get_items(self, index=None, item_type=None):
        return self.file_model.get_items(index, item_type)

    def set_items(self, items):
        self.file_model.set_items(items)
        self.adjust_columns()

    def update_items(self, file_data):
        index = self.file_model.update_items(file_data)
        self.adjust_columns()
        # self.scrollTo(index)

    def update_item_status(self, item_indices, new_status):
        self.file_model.update_item_status(item_indices, new_status)

    def settings_changed(self, setting, _):
        valid_keys = {SettingsKeys.output_dir,
                      SettingsKeys.preserve_dir,
                      SettingsKeys.encoder_path}
        if setting in valid_keys:
            self.file_model.refresh_all_output_details()
            TransCodaSettings.save_encode_list(self.file_model.get_items())

    def menu_item_selected(self, item_name):
        rows = set()
        for selected in self.selectedIndexes():
            rows.add(selected.row())
        if len(rows) > 0:
            self.menu_item_event.emit(item_name, rows)

    def get_header_context_menu(self, _):
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
        for index, column in enumerate(self.file_model.get_columns()):
            if column.display_name == item_name:
                # Remove
                self.file_model.remove_column(column)
                return
        # if column was not found, add it
        for column in ItemKeys:
            if column.display_name == item_name:
                self.file_model.add_column(column)
                return

    def get_column_key(self, index):
        return self.file_model.get_column_key(index)
