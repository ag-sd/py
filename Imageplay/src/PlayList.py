from os import path

from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QImageReader
from PyQt5.QtWidgets import QTableView, QAbstractItemView, QAction, QVBoxLayout, QWidget, QToolBar, \
    QSizePolicy

import Imageplay
from CommonUtils import FileScanner
from Imageplay.src.model.FileItemModel import FileItemModel
from SettingsDialog import SettingsDialog
from model.Animation import AnimationHandler
from model.History import InfiniteHistoryStack


class PlayListController(QWidget):

    __PLAY = "⊳"
    __PREV = "←"
    __NEXT = "→"
    __LOOP = "∞"
    __SHUFFLE = "⧓"
    __PREFERENCES = "≡"
    __CROP_START = "CROP"
    __CROP_START = "CANCEL"

    image_change_event = pyqtSignal(object)
    image_crop_event = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.playing = False
        self.playPause_action = self.create_action(PlayListController.__PLAY, "F5",
                                                   self.play_or_pause, "Play/Pause", True)
        self.previous_action = self.create_action(PlayListController.__PREV, "Left",
                                                  self.previous, "Previous image")
        self.next_action = self.create_action(PlayListController.__NEXT, "Right",
                                              self.next, "Next image")
        self.loop_action = self.create_action(PlayListController.__LOOP, "L",
                                              self.loop, "Toggle playlist looping", True,
                                              Imageplay.settings.get_setting("loop"))
        self.shuffle_action = self.create_action(PlayListController.__SHUFFLE, "S",
                                                 self.shuffle, "Shuffle play order", True,
                                                 Imageplay.settings.get_setting("shuffle"))
        self.options_action = self.create_action(PlayListController.__PREFERENCES, "Ctrl+P",
                                                 self.preferences, "Open preferences")
        self.crop_action = self.create_action(PlayListController.__CROP_START, "Ctrl+X",
                                              self.crop, "Crop Image")
        self.playlist = PlayList(self.shuffle_action.isChecked(),
                             self.loop_action.isChecked())
        self.playlist.image_change_event.connect(self.image_changed)
        self.playlist.play_state_change_event.connect(self.play_state_changed)
        self.initUI()
        Imageplay.logger.info("Ready")

    def initUI(self):
        toolbar = QToolBar()
        dummy1 = QWidget()
        dummy1.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        dummy2 = QWidget()
        dummy2.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        toolbar.addWidget(dummy1)
        toolbar.addAction(self.previous_action)
        toolbar.addAction(self.playPause_action)
        toolbar.addAction(self.next_action)
        toolbar.addSeparator()
        toolbar.addAction(self.loop_action)
        toolbar.addAction(self.shuffle_action)
        toolbar.addSeparator()
        toolbar.addAction(self.crop_action)
        toolbar.addWidget(dummy2)
        toolbar.addAction(self.options_action)
        toolbar.setStyleSheet("QToolButton{font-size: 15px;}")
        toolbar.setContentsMargins(0, 0, 0, 0)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.playlist)
        layout.addWidget(toolbar)

        self.setLayout(layout)

    def image_changed(self, image):
        self.image_change_event.emit(image)

    def play_state_changed(self, play_state):
        self.playing = play_state
        if self.playPause_action.isChecked() != play_state:
            self.playPause_action.setChecked(play_state)

    def play_or_pause(self):
        if self.playing:
            self.playlist.stop()
        else:
            self.playlist.play()

    def previous(self):
        self.playlist.previous()

    def next(self):
        self.playlist.next()

    def loop(self):
        Imageplay.settings.apply_setting("loop", self.loop_action.isChecked())

    def shuffle(self):
        Imageplay.settings.apply_setting("shuffle", self.shuffle_action.isChecked())

    def crop(self):
        self.playlist.stop()
        self.image_crop_event.emit()

    @staticmethod
    def preferences():
        SettingsDialog().exec()

    @staticmethod
    def create_action(text, shortcut, slot, tooltip, checkable=False, checked=False):
        action = QAction(text)
        action.setShortcut(shortcut)
        action.setCheckable(checkable)
        action.setChecked(checked)
        action.setToolTip(tooltip + "  (" + shortcut + ")")
        if slot is not None:
            action.triggered.connect(slot)
        return action


class PlayList(QTableView):
    image_change_event = pyqtSignal('PyQt_PyObject')
    play_state_change_event = pyqtSignal(bool)

    def __init__(self, shuffle, loop):
        super().__init__()
        self.initUI()
        self.isShuffle = shuffle
        self.isLoop = loop

        self.queue = InfiniteHistoryStack(0)
        self.playedSoFar = 0
        self.animation_handler = None
        self.image_delay = Imageplay.settings.get_setting("image_delay")
        self.animation_delay = Imageplay.settings.get_setting("gif_delay")
        self.recurse = Imageplay.settings.get_setting("recurse_subdirs")
        self.supported_formats = []
        self.doubleClicked.connect(self.doubleClicked_event)
        for _format in QImageReader.supportedImageFormats():
            self.supported_formats.append(f".{str(_format, encoding='ascii')}")

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.play)
        Imageplay.settings.settings_change_event.connect(self.updateSettings)

    def initUI(self):
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.verticalHeader().hide()
        self.horizontalHeader().setHighlightSections(False)
        self.setModel(FileItemModel())
        self.horizontalHeader().setStretchLastSection(True)

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
            self.files_added(event.mimeData().urls())
        else:
            event.ignore()

    def files_added(self, file_urls):
        # Use existing model if available
        if isinstance(self.model(), FileItemModel):
            item_model = self.model()
        else:
            item_model = FileItemModel()

        item_model.append_rows(
            FileScanner(file_urls, self.recurse, self.supported_formats).files)

        self.setModel(item_model)
        self.resizeColumnToContents(0)
        self.resizeRowsToContents()
        if item_model.rowCount(self):
            self.queue.resize(item_model.rowCount(self))
            self.playedSoFar = 0
            self.play()

    def doubleClicked_event(self, qModelIndex):
        self.play(qModelIndex.row())

    def time_changed(self):
        self.play()

    def previous(self):
        self.play(self.queue.prev())

    def next(self):
        self.play(self.queue.next(self.isShuffle))

    def updateSettings(self, key, value):
        Imageplay.logger.debug(f"New setting applied {key}: {value}")
        if key == "gif_delay":
            self.animation_delay = value
            if self.animation_handler is not None:
                self.timer.setInterval(self.animation_delay)
        elif key == "image_delay":
            self.image_delay = value
        elif key == "loop":
            self.isLoop = value
        elif key == "shuffle":
            self.isShuffle = value
            if self.isShuffle:
                self.queue.reset()
        elif key=="recurse_subdirs":
            self.recurse = value

    def stop(self):
        self.play_state_change_event.emit(False)
        self.timer.stop()

    def play(self, index=-1):
        if index < 0:
            if self.animation_handler is not None:
                Imageplay.logger.debug("In animation...")
                if self.animation_handler.has_next():
                    self.image_change_event.emit(self.animation_handler.next_frame())
                    return
                else:
                    # Discard the animation handler and chose next file
                    self.animation_handler = None

            if self.playedSoFar >= self.model().rowCount(self):
                if self.isLoop:
                    self.playedSoFar = 0
                else:
                    self.timer.stop()
                    self.play_state_change_event.emit(False)
                    return

            index = self.queue.next(self.isShuffle)

        file = path.join(self.model().index(index, 0).data(), self.model().index(index, 1).data())
        Imageplay.logger.debug(file)
        if file.upper().endswith(".GIF"):
            Imageplay.logger.debug("Entering GIF Mode")
            self.animation_handler = AnimationHandler(file)
            self.timer.start(self.animation_delay)
            self.play_state_change_event.emit(True)
        else:
            self.animation_handler = None
            self.image_change_event.emit(file)
            self.timer.start(self.image_delay)
            self.play_state_change_event.emit(True)

        self.playedSoFar = self.playedSoFar + 1
        self.selectRow(index)

