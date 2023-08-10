import copy
import os
from enum import Enum

from PyQt5.QtCore import QAbstractTableModel, Qt, QModelIndex, QVariant, QMimeDatabase

import CommonUtils
import TransCoda
from TransCoda.core.Encoda import EncoderStatus
from TransCoda.ui import TransCodaSettings


_mime_database = QMimeDatabase()

class DisplayFunctionMapping(Enum):
    FILE_SIZE = 1
    TIME = 2
    BITRATE = 3
    RATIO = 5


class Header(Enum):

    __display_function_map__ = {
        DisplayFunctionMapping.FILE_SIZE: lambda x: CommonUtils.human_readable_filesize(x),
        DisplayFunctionMapping.TIME: lambda x: CommonUtils.human_readable_time(x),
        DisplayFunctionMapping.BITRATE: lambda x: f"{int(x) / 1000:.{0}f} KBit/s",
        DisplayFunctionMapping.RATIO: lambda x: f"{x:.{2}f}%",
    }

    __headers__ = []

    input_file_name = "Input File"
    input_file_type = "Type"
    input_file_size = "Initial Size", DisplayFunctionMapping.FILE_SIZE
    input_duration = "Duration", DisplayFunctionMapping.TIME
    input_bitrate = "Bitrate", DisplayFunctionMapping.BITRATE
    input_encoder = "Encoding"
    output_file_dir = "Output Dir."
    output_file_size = "Encoded Size", DisplayFunctionMapping.FILE_SIZE
    status = "Status"
    encoder = "Encoder"
    messages = "Messages"
    percent_compete = "Progress"
    cpu_time = "CPU Time", DisplayFunctionMapping.TIME
    compression_ratio = "Ratio", DisplayFunctionMapping.RATIO
    sample_rate = "Sample Rate"
    channels = "Channels"
    album_artist = "Album Artist"
    artist = "Artist"
    title = "Title"
    album = "Album"
    track = "Track"
    genre = "Genre"
    start_time = "Start Time"
    end_time = "End Time"
    access_time = "Access Time", DisplayFunctionMapping.TIME
    modify_time = "Modify Time", DisplayFunctionMapping.TIME
    create_time = "Create Time", DisplayFunctionMapping.TIME

    def __init__(self, display_name, display_function=None):
        self.display_name = display_name
        self.display_function = display_function
        self.__class__.__headers__.append(self)

    def extract_value(self, file_item):
        raw_value = self.extract_raw_value(file_item)
        if raw_value is not None and self.display_function is not None:
            return self.__class__.__display_function_map__[self.display_function](raw_value)
        else:
            return raw_value

    def extract_raw_value(self, file_item):
        return self._extract_raw(file_item)

    def _extract_raw(self, file_item):
        if self == Header.input_file_name:
            return file_item.display_name()
        elif self == Header.input_file_type:
            return file_item.mime_type_name
        elif self == Header.status:
            return file_item.status
        elif self == Header.output_file_dir:
            return file_item.output_file_dir
        elif self == Header.encoder:
            return file_item.encoder
        elif self == Header.input_file_size:
            return file_item.file_size
        elif self == Header.output_file_size:
            return file_item.encode_output_size
        elif self == Header.messages:
            return file_item.encode_messages
        elif self == Header.start_time:
            return file_item.encode_start_time
        elif self == Header.end_time:
            return file_item.encode_end_time
        elif self == Header.cpu_time:
            return file_item.encode_cpu_time
        elif self == Header.compression_ratio:
            return file_item.encode_compression_ratio
        elif self == Header.access_time:
            return file_item.access_time
        elif self == Header.modify_time:
            return file_item.modify_time
        elif self == Header.create_time:
            return file_item.create_time
        elif self == Header.percent_compete:
            return file_item.encode_percent
        elif self in file_item.meta_data:
            return file_item.meta_data[self]
        else:
            return None


class FileItem:
    def __init__(self, file, url=None):
        self.file = file
        self.file_name = os.path.split(file)[1]
        self.url = url
        mime_type = _mime_database.mimeTypeForFile(file)
        os_info = os.stat(file)
        self.file_size = os_info.st_size
        self.access_time = os_info.st_atime
        self.modify_time = os_info.st_mtime
        self.create_time = os_info.st_ctime
        self.mime_type_name = mime_type.name()
        self.mime_type_icon_name = mime_type.iconName()
        self.status = EncoderStatus.READING_METADATA
        self.output_file_dir = TransCodaSettings.get_output_dir()
        self.encoder = TransCodaSettings.get_encoder_name()
        self.encoder_props = TransCodaSettings.get_encoder() if self.encoder is not None else None
        self.output_file = ""
        self.update_output_file()
        self.history_result = None
        self.encode_start_time = None
        self.encode_end_time = None
        self.encode_output_size = None
        self.encode_command = None
        self.encode_percent = None
        self.encode_messages = None
        self.encode_cpu_time = None
        self.encode_compression_ratio = None
        self.meta_data = {}

    def add_metadata(self, meta_data):
        self.meta_data.update(meta_data)

    def is_supported(self):
        return self.is_url() or self.is_video() or self.is_audio()

    def is_video(self):
        return self.mime_type_name.upper().startswith("VIDEO")

    def is_url(self):
        return self.url is not None

    def is_audio(self):
        return self.mime_type_name.upper().startswith("AUDIO")

    def display_name(self):
        if self.url is None:
            return self.file
        return f"{self.file_name} : {self.url}"

    def output_dir_changed(self):
        self.output_file_dir = TransCodaSettings.get_output_dir()
        self.update_output_file()

    def encoder_setting_changed(self):
        self.encoder = TransCodaSettings.get_encoder_name()
        self.encoder_props = TransCodaSettings.get_encoder()
        self.update_output_file()

    def clone(self):
        return copy.copy(self)

    def clear_execution(self):
        self.encode_start_time = None
        self.encode_end_time = None
        self.encode_output_size = None
        self.encode_command = None
        self.encode_percent = None
        self.encode_messages = None
        self.encode_cpu_time = None

    def update_output_file(self):
        if self.encoder is None or self.output_file_dir is None:
            return

        _, file_path = os.path.splitdrive(self.file)
        file_path, file = os.path.split(file_path)
        name, _ = os.path.splitext(file)
        output_dir = self.output_file_dir + file_path if TransCodaSettings.get_preserve_dir() else self.output_file_dir
        if self.encoder_props["extension"] == "*" or not self.is_supported():
            self.output_file = os.path.join(output_dir, file)
        elif self.encoder_props["extension"] == "":
            self.output_file = os.path.join(output_dir, name)
            TransCoda.logger.warn(f"Encoder props do no specify file extension. "
                                  f"Encoder is expected to create the output file in {self.output_file}")
        else:
            self.output_file = os.path.join(output_dir, name + self.encoder_props["extension"])

    def file_key(self):
        if self.url is None:
            return self.file
        return f"{self.file} : {self.url}"

    def __str__(self):
        return f"{self.display_name()} : {self.status}"


class FileItemModel(QAbstractTableModel):

    def __init__(self):
        super().__init__()
        self.file_items = []
        self.sort_column = 0
        self.sort_order = Qt.AscendingOrder
        self.columnHeaders = TransCodaSettings.get_columns()
        if not self.columnHeaders:
            self.columnHeaders = [
                Header.input_file_name,
                Header.input_file_size,
                Header.input_bitrate,
                Header.input_duration,
                Header.percent_compete,
                Header.input_encoder,
                Header.output_file_dir,
                Header.output_file_size,
                Header.compression_ratio,
                Header.cpu_time,
                Header.input_file_type]

    def rowCount(self, parent: QModelIndex = None) -> int:
        return len(self.file_items)

    def columnCount(self, parent: QModelIndex = None) -> int:
        return len(self.columnHeaders)

    def data(self, index: QModelIndex, role: int = None):
        if not index.isValid():
            return QVariant()

        item = self.file_items[index.row()]
        color = TransCoda.theme.get_item_color(file_status=item.status, file_is_supported=item.is_supported())
        if role == Qt.DisplayRole:
            header = self.columnHeaders[index.column()]
            value = header.extract_value(item)
            if value is not None:
                return value
        elif role == Qt.DecorationRole and index.column() == 0:
            return TransCoda.theme.get_mime_icon(item.mime_type_icon_name)

        elif role == Qt.ForegroundRole and color.is_foreground_color:
            return color.brush

        return QVariant()

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = None):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self.columnHeaders[section].display_name
            elif orientation == Qt.Vertical:
                return section

    def sort(self, column: int, order: Qt.SortOrder = Qt.AscendingOrder) -> None:
        def sorter(file_item):
            value = header.extract_raw_value(file_item)
            if value is None:
                value = "-"
            print(value)
            return value

        header = self.columnHeaders[column]
        try:
            self.file_items.sort(key=sorter, reverse=False if order == Qt.AscendingOrder else True)
        except TypeError:
            pass
        self.dataChanged.emit(QModelIndex(), QModelIndex())
        self.sort_column = column
        self.sort_order = order

    def refresh_items(self, index_from, index_to):
        model_index_from = self.createIndex(index_from, 0)
        model_index_to = self.createIndex(index_to, len(self.columnHeaders))
        self.dataChanged.emit(model_index_from, model_index_to, [Qt.DisplayRole, Qt.BackgroundRole])

    def add_rows(self, files):
        files_to_add = []
        for file in files:
            if not os.path.isdir(file) and self.find_item(file_item_key=file)[0] is None:
                files_to_add.append(FileItem(file))
        return self.set_items(files_to_add)

    def remove_rows(self, indices):
        # sort indices and remove the largest first
        for index in sorted(indices, reverse=True):
            self.beginRemoveRows(QModelIndex(), index, index)
            del (self.file_items[index])
            self.endRemoveRows()

    def set_items(self, items_to_add):
        last_index = len(self.file_items)
        self.beginInsertRows(QModelIndex(), last_index, last_index + len(items_to_add))
        for item in items_to_add:
            self.file_items.append(item)
        self.endInsertRows()
        return len(items_to_add)

    def update_items(self, items_to_update):
        for updated in items_to_update:
            item, index = self.find_item(updated.file_key())
            if updated.status == EncoderStatus.REMOVE:
                self.remove_rows([index])
            elif item:
                self.file_items[index] = updated
                self.refresh_items(index, index)
                self.createIndex(index, 0)
            else:
                self.set_items([updated])

    def get_items(self, index=None):
        if index is not None:
            return self.file_items[index].clone()
        else:
            items_copy = []
            for item in self.file_items:
                # Create a new copy of the item
                items_copy.append(item.clone())
            return items_copy

    def find_item(self, file_item_key) -> (FileItem, int):
        for index, item in enumerate(self.file_items):
            if item.file_key() == file_item_key:
                return item, index
        return None, -1

    def update_status(self, index, new_status):
        item = self.file_items[index]
        # skip re-updating a field if its already in waiting state
        if item.status == new_status:
            return
        self.file_items[index].status = new_status
        if new_status == EncoderStatus.WAITING:
            self.file_items[index].clear_execution()
        self.refresh_items(index, index)

    def encoder_changed(self):
        for index, item in enumerate(self.file_items):
            item.encoder_setting_changed()
        self.refresh_items(0, len(self.file_items))

    def output_dir_changed(self):
        for index, item in enumerate(self.file_items):
            item.output_dir_changed()
        self.refresh_items(0, len(self.file_items))

    def get_column_key(self, index):
        return self.columnHeaders[index]

    def get_columns(self):
        return self.columnHeaders

    def add_column(self, column):
        self.beginInsertColumns(QModelIndex(), len(self.columnHeaders), len(self.columnHeaders))
        self.columnHeaders.append(column)
        self.endInsertColumns()
        TransCodaSettings.save_columns(self.columnHeaders)
        return len(self.columnHeaders) - 1

    def remove_column(self, column):
        del_index = -1
        for index, col in enumerate(self.columnHeaders):
            if col == column:
                del_index = index
                break
        if del_index >= 0:
            self.beginRemoveColumns(QModelIndex(), del_index, del_index)
            del (self.columnHeaders[del_index])
            self.endRemoveColumns()
            TransCodaSettings.save_columns(self.columnHeaders)

