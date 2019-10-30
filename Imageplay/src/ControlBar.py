from functools import partial

import Imageplay
import actions
from PyQt5.QtCore import QTimer, QUrl, pyqtSignal
from PyQt5.QtWidgets import QWidget, QToolBar, QSizePolicy, QAction
from Settings import SettingsDialog, SettingsKeys
from actions.BaseEditAction import BaseEditAction
from common.CommonUtils import FileScanner
from model.Actions import ActionType


class ControlBar(QToolBar):
    image_edit_complete_event = pyqtSignal(ActionType)
    image_edit_starting_event = pyqtSignal()
    image_edit_event = pyqtSignal(BaseEditAction)
    image_zoom_event = pyqtSignal(bool)

    __SZ_TRUE = "⊡"
    __SZ_FITS = "⊠"

    def __init__(self, playlist_model):
        super().__init__()

        self.prev_action = self.create_action(ActionType.PREV)
        self.next_action = self.create_action(ActionType.NEXT)
        self.loop_action = self.create_action(ActionType.LOOP)
        self.play_action = self.create_action(ActionType.PLAY)
        self.edit_action = self.create_action(ActionType.EDIT)
        self.save_action = self.create_action(ActionType.SAVE)
        self.size_action = self.create_action(ActionType.SIZE)
        self.exit_action = self.create_action(ActionType.CANCEL)
        self.shfl_action = self.create_action(ActionType.SHUFFLE)
        self.opts_action = self.create_action(ActionType.OPTIONS)
        self.z_in_action = self.create_action(ActionType.ZOOM_IN)
        self.z_out_action = self.create_action(ActionType.ZOOM_OUT)

        self.action_event(ActionType.SIZE, Imageplay.settings.get_setting(SettingsKeys.image_scaled, True))

        self.playlist_model = playlist_model
        self.initUI()
        self.set_playing_mode()
        self.timer = QTimer()
        self.timer.timeout.connect(self.timeout)
        self.playedSoFar = 0
        Imageplay.logger.info("Ready")

    def initUI(self):
        self.setStyleSheet("QToolButton{font-size: 16px;}")
        self.setContentsMargins(0, 0, 0, 0)

    def action_event(self, action, value_checked):
        if action == ActionType.PREV:
            self.playlist_model.previous()
        elif action == ActionType.NEXT:
            self.playlist_model.next(Imageplay.settings.get_setting(SettingsKeys.shuffle, False))

        elif action == ActionType.LOOP:
            Imageplay.settings.apply_setting(SettingsKeys.loop, value_checked)

        elif action == ActionType.SHUFFLE:
            Imageplay.settings.apply_setting(SettingsKeys.shuffle, value_checked)

        elif action == ActionType.OPTIONS:
            SettingsDialog().exec()

        elif action == ActionType.PLAY:
            if value_checked:
                self.playedSoFar = 0
                self.timer.start(Imageplay.settings.get_setting(SettingsKeys.image_delay, 2000))
            else:
                self.timer.stop()

        elif action == ActionType.EDIT:
            self.set_editing_mode()
            self.image_edit_starting_event.emit()

        elif action == ActionType.SAVE:
            self.image_edit_complete_event.emit(action)
            self.set_playing_mode()

        elif action == ActionType.CANCEL:
            self.image_edit_complete_event.emit(action)
            self.set_playing_mode()

        elif action == ActionType.SIZE:
            if value_checked:
                self.size_action.setText(ControlBar.__SZ_FITS)
            else:
                self.size_action.setText(ControlBar.__SZ_TRUE)
            Imageplay.settings.apply_setting(SettingsKeys.image_scaled, value_checked)

        elif action == ActionType.ZOOM_IN:
            self.image_zoom_event.emit(True)

        elif action == ActionType.ZOOM_OUT:
            self.image_zoom_event.emit(False)

        elif isinstance(action, BaseEditAction):
            self.image_edit_event.emit(action)

    def timeout(self):
        if self.playedSoFar >= self.playlist_model.rowCount(self):
            if Imageplay.settings.get_setting(SettingsKeys.loop, False):
                self.playedSoFar = 0
            else:
                # Simulate a pause button press
                # self.action_event(Controller.__PLAY, False)
                self.play_action.trigger()
                return

        self.playlist_model.next(
            Imageplay.settings.get_setting(SettingsKeys.shuffle, False)
        )
        self.playedSoFar += 1

    def files_from_args(self, files, start_file=None):
        urls = []
        for file in files:
            urls.append(QUrl.fromLocalFile(file))
        self.playlist_model.add_files(
            FileScanner(urls,
                        Imageplay.settings.get_setting(SettingsKeys.recurse_subdirs, False),
                        Imageplay.supported_formats).files)
        index = -1 if start_file is None else self.playlist_model.find_file(start_file)
        self.playlist_model.next(
            Imageplay.settings.get_setting(SettingsKeys.shuffle, False),
            index)

    def set_playing_mode(self):
        self.clear()
        dummy = QWidget()
        dummy.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.addAction(self.prev_action)
        self.addAction(self.play_action)
        self.addAction(self.next_action)
        self.addSeparator()
        self.addAction(self.loop_action)
        self.addAction(self.shfl_action)
        self.addSeparator()
        self.addAction(self.edit_action)

        self.addWidget(dummy)
        self.addAction(self.z_in_action)
        self.addAction(self.z_out_action)
        self.addSeparator()
        self.addAction(self.size_action)
        self.addAction(self.opts_action)

    def set_editing_mode(self):
        self.clear()
        dummy = QWidget()
        dummy.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        for action in actions.available_actions:
            if action.trigger() is None:
                action.triggered.connect(partial(self.action_event, action))
            self.addAction(action)
        self.addSeparator()
        self.addAction(self.save_action)
        self.addAction(self.exit_action)

        self.addWidget(dummy)
        self.addAction(self.opts_action)

    def create_action(self, action_type):
        action = QAction(action_type.value.text)
        action.setShortcut(action_type.value.shortcut)
        action.setCheckable(action_type.value.checkable)
        action.setChecked(action_type.value.checked)
        action.setToolTip(action_type.value.tooltip + "  (" + action_type.value.shortcut + ")")
        action.triggered.connect(partial(self.action_event, action_type))
        if action_type.value.icon is not None:
            action.setIcon(action_type.value.icon)
        return action
