from PyQt5.QtCore import QAbstractTableModel, QVariant, Qt, QModelIndex, QFileInfo, pyqtSignal
from PyQt5.QtGui import QImage
from PyQt5.QtWidgets import QFileIconProvider

import Imageplay
from Imageplay import SettingsKeys
from model.Animation import AnimationHandler
from model.History import InfiniteHistoryVariableStack


class PlaylistFileModel(QAbstractTableModel):
    """
    This class maintains a playlist of files that are to be viewed.
    Signals:
        image_changed   - The new image to be viewed - A QImage Object, filename
    Methods:
        next            - Pick and show the next image
        previous        - Show the previous image
        add_files       - Add files to the playlist
        find_file       - Return the index of the first file that matches the given file name
    """
    __columnHeaders = ["File Path", "File Name"]
    image_change_event = pyqtSignal('PyQt_PyObject', str)
    files_update_event = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.file_items = []
        self.history = InfiniteHistoryVariableStack(0)
        self.animation_handler = None

    def previous(self):
        self.next(False, self.history.prev())

    def next(self, shuffle, index=-1):
        if index < 0:
            if self.animation_handler is not None:
                Imageplay.logger.debug("In animation...")
                if self.animation_handler.has_next():
                    self.image_change_event.emit(self.animation_handler.next_frame(),
                                                 self.animation_handler.animation_file)
                    return
                else:
                    # Discard the animation handler and chose next file
                    self.animation_handler = None

            index = self.history.next(shuffle)

        file = self.file_items[index].absoluteFilePath()
        Imageplay.logger.debug(file)
        if file.upper().endswith(".GIF") and Imageplay.settings.get_setting(SettingsKeys.gif_by_frame, False):
            Imageplay.logger.debug("Entering GIF Mode")
            self.animation_handler = AnimationHandler(file)
            self.image_change_event.emit(self.animation_handler.next_frame(),
                                         self.animation_handler.animation_file)
        else:
            self.animation_handler = None
            self.image_change_event.emit(QImage(file), file)

    def rowCount(self, parent):
        return len(self.file_items)

    def columnCount(self, parent):
        return len(PlaylistFileModel.__columnHeaders)

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
                return PlaylistFileModel.__columnHeaders[p_int]
            elif orientation == Qt.Vertical:
                return p_int

    def add_files(self, files):
        last_index = len(self.file_items)
        self.beginInsertRows(QModelIndex(), last_index, last_index + len(files))
        for file in files:
            self.file_items.append(QFileInfo(file))
        self.endInsertRows()
        self.history.resize(len(self.file_items))
        self.files_update_event.emit()

    def find_file(self, file):
        for index, item in enumerate(self.file_items):
            if item.fileName() == file:
                return index
        return -1
