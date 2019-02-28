from enum import Enum
from functools import partial

from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QAction, QVBoxLayout, QWidget, QToolBar, \
    QSizePolicy, QTableView, QAbstractItemView

import Imageplay
from SettingsDialog import SettingsDialog
from common.CommonUtils import FileScanner


class Mode(Enum):
    PLAYING = 1
    EDITING = 2


class Controller(QWidget):

    __SZ_TRUE = "⊞"
    __SZ_FITS = "⊟"

    __PREV = "←"
    __NEXT = "→"

    __LOOP = "∞"
    __SHFL = "⧓"

    __PREF = "≡"

    def __init__(self, playlist_model):
        super().__init__()
        self.prev_action = self.create_action(Controller.__PREV, "Left",
                                              self.action_event,
                                              "Previous image")
        self.next_action = self.create_action(Controller.__NEXT, "Right",
                                              self.action_event,
                                              "Next image")

        self.loop_action = self.create_action(Controller.__LOOP, "L",
                                              self.action_event,
                                              "Toggle playlist looping", True,
                                              Imageplay.settings.get_setting("loop"))
        self.shfl_action = self.create_action(Controller.__SHFL, "S",
                                              self.action_event,
                                              "Toggle playlist shuffling", True,
                                              Imageplay.settings.get_setting("shuffle"))
        self.opts_action = self.create_action(Controller.__PREF, "Ctrl+P",
                                              self.action_event,
                                              "Open preferences")

        self.playlist_model = playlist_model
        self.playlist_table = PlayList(playlist_model)
        self.toolbar = QToolBar()
        self.initUI()
        self.set_playing_mode()
        Imageplay.logger.info("Ready")

    def initUI(self):
        self.toolbar.setStyleSheet("QToolButton{font-size: 16px;}")
        self.toolbar.setContentsMargins(0, 0, 0, 0)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.playlist_table)
        self.setLayout(layout)

    def action_event(self, action, opt1):
        if action == Controller.__PREV:
            self.playlist_model.previous()
        elif action == Controller.__NEXT:
            self.playlist_model.next(
                Imageplay.settings.get_setting("shuffle", False),
                Imageplay.settings.get_setting("loop", False),
            )
        elif action == Controller.__LOOP:
            Imageplay.settings.apply_setting("loop", opt1)
        elif action == Controller.__SHFL:
            Imageplay.settings.apply_setting("shuffle", opt1)
        elif action == Controller.__PREF:
            SettingsDialog().exec()

    def files_from_args(self, files, start_file=None):
        urls = []
        for file in files:
            urls.append(QUrl.fromLocalFile(file))
        self.playlist_model.add_files(
            FileScanner(urls,
                        Imageplay.settings.get_setting("recurse_subdirs", False),
                        Imageplay.supported_formats).files)
        index = -1 if start_file is None else self.playlist_model.find_file(start_file)
        self.playlist_model.next(
            Imageplay.settings.get_setting("shuffle", False),
            Imageplay.settings.get_setting("loop", False),
            index)

    def set_playing_mode(self):
        self.toolbar.clear()
        dummy1 = QWidget()
        dummy1.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        dummy2 = QWidget()
        dummy2.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.toolbar.addAction(self.prev_action)
        self.toolbar.addAction(self.next_action)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.loop_action)
        self.toolbar.addAction(self.shfl_action)
        self.toolbar.addWidget(dummy2)
        self.toolbar.addAction(self.opts_action)

    def set_editing_mode(self):
        self.toolbar.clear()

    @staticmethod
    def create_action(text, shortcut, slot, tooltip, checkable=False, checked=False, icon=None):
        action = QAction(text)
        action.setShortcut(shortcut)
        action.setCheckable(checkable)
        action.setChecked(checked)
        action.setToolTip(tooltip + "  (" + shortcut + ")")
        if slot is not None:
            action.triggered.connect(partial(slot, text))
        if icon is not None:
            action.setIcon(icon)
        return action

# class PlayListController(QWidget):
#
#     __PLAY = "⊳"
#     __PREV = "←"
#     __NEXT = "→"
#
#     __PREF = "≡"
#     __EDIT = "𝐄"
#     __CROP = "◳"  # "۝"
#     __COLR = "◧"  # ""☼"
#     __RESZ = "⊹"
#     __UNDO = __PREV
#     __EXIT = "⨉"
#     __SAVE = "✓"  # "⨀"
#     __FITS_SIZE = "×"
#     __TRUE_SIZE = "+"
#
#     image_change_event = pyqtSignal(object)
#     image_crop_event = pyqtSignal()
#     image_save_event = pyqtSignal()
#     image_exit_event = pyqtSignal()
#     image_scale_event = pyqtSignal(bool)
#
#     def __init__(self):
#         super().__init__()
#
#         self.playing = False
#         self.play_action = self.create_action(PlayListController.__PLAY, "Space",
#                                               self.play_or_pause,
#                                               "Play/Pause", True)
#
#         self.edit_action = self.create_action(PlayListController.__EDIT, "Ctrl+E",
#                                               self.edit,
#                                               "Edit Image")
#         self.crop_action = self.create_action(PlayListController.__CROP, "Ctrl+R",
#                                               self.crop,
#                                               "Crop Image")
#         self.undo_action = self.create_action(PlayListController.__UNDO, "Ctrl+Z",
#                                               self.undo,
#                                               "Undo Last Action")
#         self.save_action = self.create_action(PlayListController.__SAVE, "Ctrl+S",
#                                               self.save,
#                                               "Save changes and close")
#         self.exit_action = self.create_action(PlayListController.__EXIT, "Ctrl+W",
#                                               self.exit,
#                                               "Close without saving changes")
#
#         self.fits_size_action = self.create_action(PlayListController.__FITS_SIZE, "Ctrl+0",
#                                               self.fits_size,
#                                               "Scale to fit window", checkable=True, checked=True)
#
#
#
#         # TODO
#         self.colr_action = self.create_action(PlayListController.__COLR, "Ctrl+B",
#                                               self.colr,
#                                               "Colorize Image - TODO")
#         # TODO
#         self.resz_action = self.create_action(PlayListController.__RESZ, "Ctrl+I",
#                                               self.resz,
#                                               "Resize Image - TODO")
#         self.playlist_model = PlaylistFileModel()
#         self.playlist_table = PlayList(self.playlist_model)
#         # self.playlist.image_change_event.connect(self.image_changed)
#         # self.playlist.play_state_change_event.connect(self.play_state_changed)
#         self.toolbar = QToolBar()
#         self.initUI()
#         Imageplay.logger.info("Ready")
#
#
#
#
#
#     def image_changed(self, image):
#         self.image_change_event.emit(image)
#
#     def play_state_changed(self, play_state):
#         self.playing = play_state
#         if self.play_action.isChecked() != play_state:
#             self.play_action.setChecked(play_state)
#
#     def play_or_pause(self):
#         if self.playing:
#             self.playlist.stop()
#         else:
#             self.playlist.play()
#
#     def prev(self):
#         self.playlist.previous()
#
#     def next(self, foo, bar):
#         self.playlist.next()
#
#     def loop(self):
#         Imageplay.settings.apply_setting("loop", self.loop_action.isChecked())
#
#     def shfl(self):
#         Imageplay.settings.apply_setting("shuffle", self.shfl_action.isChecked())
#
#     def edit(self):
#         if self.playlist.model() is not None and self.playlist.model().rowCount(self.playlist) > 0:
#             self.playlist.stop()
#             self.set_editing_mode()
#
#     def exit(self):
#         self.image_exit_event.emit()
#         self.set_playing_mode()
#         self.playlist.play()
#
#     def save(self):
#         self.image_save_event.emit()
#         self.exit()
#
#     def undo(self):
#         print("Undo")
#         # Pop the stack into the image
#
#     def resz(self):
#         print("Resize")
#
#     def colr(self):
#         print("Colorize")
#
#     def crop(self):
#         self.image_crop_event.emit()
#
#     def fits_size(self):
#         self.image_scale_event.emit(self.fits_size_action.isChecked())
#         if self.fits_size_action.isChecked():
#             self.fits_size_action.setText(PlayListController.__FITS_SIZE)
#         else:
#             self.fits_size_action.setText(PlayListController.__TRUE_SIZE)
#
#     def set_playing_mode(self):
#         self.toolbar.clear()
#         dummy1 = QWidget()
#         dummy1.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
#         dummy2 = QWidget()
#         dummy2.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
#         self.toolbar.addAction(self.fits_size_action)
#         self.toolbar.addWidget(dummy1)
#         self.toolbar.addAction(self.prev_action)
#         # self.toolbar.addAction(self.play_action)
#         self.toolbar.addAction(self.next_action)
#
#         self.toolbar.addSeparator()
#         self.toolbar.addAction(self.edit_action)
#         self.toolbar.addWidget(dummy2)
#         self.toolbar.addAction(self.opts_action)
#         # self.playlist.setEnabled(True)
#
#     def set_editing_mode(self):
#         self.toolbar.clear()
#         dummy1 = QWidget()
#         dummy1.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
#         dummy2 = QWidget()
#         dummy2.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
#         self.toolbar.addAction(self.fits_size_action)
#         self.toolbar.addWidget(dummy1)
#         self.toolbar.addAction(self.resz_action)
#         self.toolbar.addAction(self.colr_action)
#         self.toolbar.addAction(self.crop_action)
#         self.toolbar.addSeparator()
#         # self.toolbar.addAction(self.undo_action)
#         # self.toolbar.addSeparator()
#         self.toolbar.addAction(self.save_action)
#         self.toolbar.addAction(self.exit_action)
#         self.toolbar.addWidget(dummy2)
#         self.toolbar.addAction(self.opts_action)
#         # self.playlist.setEnabled(False)
#
#     @staticmethod
#     def preferences():
#         SettingsDialog().exec()
#
#     @staticmethod
#     def create_action(text, shortcut, slot, tooltip, checkable=False, checked=False, icon=None):
#         action = QAction(text)
#         action.setShortcut(shortcut)
#         action.setCheckable(checkable)
#         action.setChecked(checked)
#         action.setToolTip(tooltip + "  (" + shortcut + ")")
#         if slot is not None:
#             action.triggered.connect(partial(slot, text))
#         if icon is not None:
#             action.setIcon(icon)
#         return action
#
#


class PlayList(QTableView):

    def __init__(self, model):
        super().__init__()
        self.setModel(model)
        model.files_update_event.connect(self.adjust_view)
        self.initUI()

    def initUI(self):
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.verticalHeader().hide()
        self.horizontalHeader().setHighlightSections(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.doubleClicked.connect(self.double_click_event)

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

    def double_click_event(self, qModelIndex):
        self.model().next(
            Imageplay.settings.get_setting("shuffle", False),
            Imageplay.settings.get_setting("loop", False),
            qModelIndex.row()
        )

    def files_added(self, file_urls):
        self.model().add_files(
            FileScanner(file_urls,
                        Imageplay.settings.get_setting("recurse_subdirs", False),
                        Imageplay.supported_formats).files)
        self.adjust_view()

    def adjust_view(self):
        self.resizeColumnToContents(0)
        self.resizeRowsToContents()

