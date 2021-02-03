import os
from enum import Enum

from PyQt5.QtCore import pyqtSignal, QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QToolBar

import CommonUtils
from TransCoda.core.Encoda import EncoderStatus


class Action(Enum):
    ADD_FILE = "Add File"
    ADD_DIR = "Add Directory"
    ADD_YTD = "ADd YouTube"
    DEL_FILE = "Remove"
    DEL_ALL = "Clear All"
    ENCODE = "Encode"
    SETTINGS = "Settings"
    HELP = "Help"
    ABOUT = "About"
    CHANGE_STATUS_SUCCESS = EncoderStatus.SUCCESS.name
    CHANGE_STATUS_READY = EncoderStatus.READY.name


class MainToolBar(QToolBar):
    button_pressed = pyqtSignal(Action)
    _ACTION_ENCODE_DISABLED_NO_ENCODER_MESSAGE = "Choose an encoder"
    _ACTION_ENCODE_DISABLED_NO_FILES_MESSAGE = "Select files to encode"
    _ACTION_ENCODE_DISABLED_NO_OUTPUT_DIR_MESSAGE = "Choose output directory"
    _ACTION_ENCODE_READY_MESSAGE = "Start encoding the files"
    _ACTION_ENCODE_RUNNING_MESSAGE = "Wait for files in progress to complete and stop"

    def __init__(self):
        super().__init__()
        self.setIconSize(QSize(48, 48))
        self.action_add_file = CommonUtils.create_action(name=Action.ADD_FILE.name, shortcut="Ctrl+O",
                                                         tooltip="Add a single file ",
                                                         func=self.raise_event, parent=self,
                                                         icon=QIcon.fromTheme("list-add"))
        self.action_add_dir = CommonUtils.create_action(name=Action.ADD_DIR.name, shortcut="Ctrl+D",
                                                        tooltip="Add an entire directory",
                                                        func=self.raise_event, parent=self,
                                                        icon=QIcon.fromTheme("folder-new"))
        self.action_add_yt = CommonUtils.create_action(name=Action.ADD_YTD.name, shortcut="Ctrl+Y",
                                                       tooltip="Add a file with YouTube Links",
                                                       func=self.raise_event, parent=self,
                                                       icon=QIcon(os.path.join(os.path.dirname(__file__),
                                                                               "../resource/youtube.svg")))
        self.action_clear_all = CommonUtils.create_action(name=Action.DEL_ALL.name, shortcut="Delete",
                                                          tooltip="Clear all files",
                                                          func=self.raise_event, parent=self,
                                                          icon=QIcon.fromTheme("edit-clear"))
        self.action_settings = CommonUtils.create_action(name=Action.SETTINGS.name, shortcut="Ctrl+R",
                                                         tooltip="Open the settings editor",
                                                         func=self.raise_event, parent=self,
                                                         icon=QIcon.fromTheme("preferences-system"))
        self.action_encode = CommonUtils.create_action(name=Action.ENCODE.name, shortcut="Ctrl+R",
                                                       tooltip="Start encoding the files",
                                                       func=self.raise_event, parent=self,
                                                       icon=QIcon.fromTheme("media-playback-start"))
        self.action_help = CommonUtils.create_action(name=Action.HELP.name, shortcut="F1",
                                                     tooltip="View online help",
                                                     func=self.raise_event, parent=self,
                                                     icon=QIcon.fromTheme("help-contents"))
        self.action_about = CommonUtils.create_action(name=Action.ABOUT.name, shortcut="Ctrl+I",
                                                      tooltip="About this application",
                                                      func=self.raise_event, parent=self,
                                                      icon=QIcon.fromTheme("help-about"))
        self.addAction(self.action_add_file)
        self.addAction(self.action_add_dir)
        self.addAction(self.action_add_yt)
        self.addAction(self.action_clear_all)
        self.addSeparator()
        self.addAction(self.action_settings)
        self.addAction(self.action_encode)
        self.addSeparator()
        self.addAction(self.action_help)
        self.addAction(self.action_about)
        self.set_encode_state(0, None, None)

    def set_encode_state(self, file_count, output_dir, encoder_name):
        enabled = encoder_name is not None and output_dir is not None and output_dir is not "" and file_count != 0
        self.action_encode.setEnabled(enabled)
        if enabled:
            self.action_encode.setToolTip(self._ACTION_ENCODE_READY_MESSAGE)
        else:
            message = []
            if file_count == 0:
                message.append(self._ACTION_ENCODE_DISABLED_NO_FILES_MESSAGE)
            if output_dir is None or output_dir == "":
                message.append(self._ACTION_ENCODE_DISABLED_NO_OUTPUT_DIR_MESSAGE)
            if encoder_name is None:
                message.append(self._ACTION_ENCODE_DISABLED_NO_ENCODER_MESSAGE)
            self.action_encode.setToolTip(", ".join(message))

    def raise_event(self, event):
        self.button_pressed.emit(Action[event])

    def encoding_finished(self, file_count, output_dir, encoder_name):
        self.action_add_file.setEnabled(True)
        self.action_add_dir.setEnabled(True)
        self.action_add_yt.setEnabled(True)
        self.action_clear_all.setEnabled(True)
        self.action_settings.setEnabled(True)
        self.action_help.setEnabled(True)
        self.action_about.setEnabled(True)
        self.action_encode.setIcon(QIcon.fromTheme("media-playback-start"))
        self.set_encode_state(file_count, output_dir, encoder_name)

    def encoding_started(self):
        self.action_add_file.setEnabled(False)
        self.action_add_dir.setEnabled(False)
        self.action_add_yt.setEnabled(False)
        self.action_clear_all.setEnabled(False)
        self.action_settings.setEnabled(False)
        self.action_help.setEnabled(False)
        self.action_about.setEnabled(False)
        self.action_encode.setIcon(QIcon.fromTheme("media-playback-stop"))
        self.action_encode.setToolTip(self._ACTION_ENCODE_RUNNING_MESSAGE)
