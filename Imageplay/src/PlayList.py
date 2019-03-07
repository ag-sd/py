from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTableView, QAbstractItemView

import Imageplay
from Settings import SettingsKeys
from common.CommonUtils import FileScanner


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
            qModelIndex.row()
        )

    def files_added(self, file_urls):
        self.model().add_files(
            FileScanner(file_urls,
                        Imageplay.settings.get_setting(SettingsKeys.recurse_subdirs, False),
                        Imageplay.supported_formats).files)
        self.adjust_view()

    def adjust_view(self):
        self.resizeColumnToContents(0)
        self.resizeRowsToContents()

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