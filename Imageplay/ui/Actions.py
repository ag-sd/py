from enum import Enum

from PyQt5.QtCore import pyqtSignal, QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QToolBar, QWidget, QSizePolicy

from common import CommonUtils
from Imageplay.ui import Settings


class Action(Enum):
    __lookup__ = {}

    PREV = "←", "Left", "Previous image", "go-previous"
    NEXT = "→", "Right", "Next image", "go-next"
    LOOP = "∞", "L", "Toggle playlist looping", "media-playlist-repeat"
    SHUFFLE = "⧓", "S", "Toggle playlist shuffling", "media-playlist-shuffle"
    OPTIONS = "≡", "Ctrl+P", "Open preferences", "preferences-system"
    PLAY = "P", "Space", "Start Slide-show", "media-playback-start", "media-playback-pause"
    ZOOM_IN = "⊞", "Ctrl++", "Zoom in", "zoom-in"
    ZOOM_OUT = "⊟", "Ctrl+-", "Zoom out", "zoom-out"
    SIZE = "><", "Ctrl+0", "Toggle scaled-to-fit or true-size of image", "zoom-original", "zoom-fit-best"
    INFO = "i", "Ctrl+A", "Show Image Details", "dialog-information"
    SEND = "s", "Ctrl+O", "Send to external program", "document-send"

    def __init__(self, text, shortcut, tooltip, icon_name=None, icon_name_alt=None):
        self.text = text
        self.shortcut = shortcut
        self.tooltip = tooltip
        self.icon = QIcon.fromTheme(icon_name) if icon_name is not None else None
        self.icon_alt = QIcon.fromTheme(icon_name_alt) if icon_name_alt is not None else None
        self.__class__.__lookup__[text] = self

    def __str__(self):
        return self.text


class ToolBar(QToolBar):
    button_pressed = pyqtSignal(Action)

    def __init__(self):
        super().__init__()
        self._actions = {
            Action.PREV: self._create_action(Action.PREV),
            Action.NEXT: self._create_action(Action.NEXT),
            Action.LOOP: self._create_action(Action.LOOP, checked=Settings.get_loop()),
            Action.SHUFFLE: self._create_action(Action.SHUFFLE, checked=Settings.get_shuffle()),
            Action.OPTIONS: self._create_action(Action.OPTIONS),
            Action.PLAY: self._create_action(Action.PLAY, checked=False),
            Action.ZOOM_IN: self._create_action(Action.ZOOM_IN),
            Action.ZOOM_OUT: self._create_action(Action.ZOOM_OUT),
            Action.SIZE: self._create_action(Action.SIZE, checked=Settings.get_image_scaled()),
            Action.INFO: self._create_action(Action.INFO, checked=False),
            Action.SEND: self._create_action(Action.SEND)
        }
        # Initialize the button and icon states
        for action in self._actions:
            self.toggle_action(action)
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("QToolButton{font-size: 16px;}")
        self.setContentsMargins(0, 0, 0, 0)

        dummy = QWidget()
        dummy.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.addAction(self._actions[Action.PREV])
        self.addAction(self._actions[Action.PLAY])
        self.addAction(self._actions[Action.NEXT])
        self.addSeparator()
        self.addAction(self._actions[Action.LOOP])
        self.addAction(self._actions[Action.SHUFFLE])

        self.addWidget(dummy)
        self.addAction(self._actions[Action.INFO])
        self.addAction(self._actions[Action.SEND])
        self.addSeparator()
        self.addAction(self._actions[Action.ZOOM_IN])
        self.addAction(self._actions[Action.ZOOM_OUT])
        self.addAction(self._actions[Action.SIZE])
        self.addSeparator()
        self.addAction(self._actions[Action.OPTIONS])

    def toggle_action(self, action):
        toolbar_action = self._actions[action]
        if toolbar_action is not None:
            if toolbar_action.isCheckable():
                if toolbar_action.isChecked() and action.icon_alt is not None:
                    toolbar_action.setIcon(action.icon_alt)
                elif not toolbar_action.isChecked():
                    toolbar_action.setIcon(action.icon)

    def _raise_event(self, event):
        self.button_pressed.emit(Action.__lookup__[event])

    def _create_action(self, action, checked=None):
        return CommonUtils.create_action(name=action.text, shortcut=action.shortcut, tooltip=action.tooltip,
                                         func=self._raise_event, parent=self, icon=action.icon, checked=checked)
