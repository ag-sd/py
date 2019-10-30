from enum import Enum
from functools import partial

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction

import Imageplay
from Imageplay import SettingsKeys


class Action(object):
    def __init__(self, text, shortcut, tooltip,
                 checkable=False, checked=False, icon=None):
        self.text = text
        self.shortcut = shortcut
        self.tooltip = tooltip
        self.checkable = checkable
        self.checked = checked
        self.icon = icon

    def create_action(self, action_function):
        action = QAction(self.text)
        action.setShortcut(self.shortcut)
        action.setCheckable(self.checkable)
        action.setChecked(self.checked)
        action.setToolTip(self.tooltip + "  (" + self.shortcut + ")")
        if self.icon is not None:
            action.setIcon(self.icon)
        if action_function is not None:
            action.triggered.connect(partial(action_function, self.text))
        return action


class CropAction(Action):
    def __init__(self, text, shortcut, tooltip):
        super().__init__(text, shortcut, tooltip)

    @staticmethod
    def apply(top_left, crop_width, crop_height,
              view_width, view_height, base_image):
        # Compute x ratio, y ratio from dimension of view and dimension of image
        x_ratio = base_image.width() / view_width
        y_ratio = base_image.height() / view_height

        top = top_left.x() * y_ratio
        left = top_left.y() * x_ratio
        width = crop_width * x_ratio
        height = crop_height * y_ratio

        return base_image.copy(top, left, width, height)


class ActionType(Enum):
    PREV = Action("←", "Left", "Previous image")

    NEXT = Action("→", "Right", "Next image")

    LOOP = Action("∞", "L", "Toggle playlist looping", True, Imageplay.settings.get_setting(SettingsKeys.loop, True))

    SHUFFLE = Action("⧓", "S", "Toggle playlist shuffling", True,
                     Imageplay.settings.get_setting(SettingsKeys.shuffle, True))

    OPTIONS = Action("≡", "Ctrl+P", "Open preferences")

    PLAY = Action("P", "Space", "Start Slide-show", checkable=True, checked=False,
                  icon=QIcon("resources/play_icon.svg"))

    EDIT = Action("𝐄", "Ctrl+E", "Edit image")

    # CROP = CropAction("◳", "Ctrl+O", "Crop Image")

    SAVE = Action("OK", "Ctrl+S", "Save Image and reload", icon=QIcon("resources/check.svg"))
    CANCEL = Action("Close", "Esc", "Discard Changes and reload", icon=QIcon("resources/close.svg"))

    ZOOM_IN = Action("⊞", "Ctrl++", "Zoom in")
    ZOOM_OUT = Action("⊟", "Ctrl+-", "Zoom out")
    SIZE = Action("[]", "Ctrl+0", "Toggle scaled-to-fit or true-size of image", True,
                  Imageplay.settings.get_setting(SettingsKeys.image_scaled, True))
