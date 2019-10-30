from enum import Enum, unique

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QHBoxLayout, QSpinBox, QLabel, QVBoxLayout, QCheckBox


@unique
class SettingsKeys(Enum):
    image_delay = "image_delay"
    gif_delay = "gif_delay"
    gif_by_frame = "gif_by_frame"
    recurse_subdirs = "recurse_subdirs"
    shuffle = "shuffle"
    loop = "loop"
    image_scaled = "image_scaled"
    dupe_image_view_zoom = "dupe_image_view_zoom"


class SettingsDialog(QDialog):

    def __init__(self):
        super().__init__()
        self.imageSpinner = QSpinBox()
        self.imageSpinner.setMinimum(1)
        self.imageSpinner.setValue(Imageplay.settings.get_setting(SettingsKeys.image_delay, 3000) / 1000)
        self.imageSpinner.valueChanged.connect(self.image_delay_change)

        self.gifSpinner = QSpinBox()
        self.gifSpinner.setMinimum(1)
        self.gifSpinner.setValue(Imageplay.settings.get_setting(SettingsKeys.gif_delay, 1000) / 1000)
        self.gifSpinner.valueChanged.connect(self.animation_delay_change)

        self.recurse = QCheckBox("Add all child folders when a directory is added")
        self.recurse.setChecked(Imageplay.settings.get_setting(SettingsKeys.recurse_subdirs, False))
        self.recurse.stateChanged.connect(self.recurse_change)

        self.gifByFrame = QCheckBox("View gif files one frame at a time")
        self.gifByFrame.setChecked(Imageplay.settings.get_setting(SettingsKeys.gif_by_frame, False))
        self.gifByFrame.stateChanged.connect(self.gif_by_frame_change)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.addLayout(self.create_spinner_layout("Load next image in (seconds)", self.imageSpinner))
        layout.addLayout(self.create_spinner_layout("Load next animation in (seconds)", self.gifSpinner))
        layout.addWidget(self.recurse)
        layout.addWidget(self.gifByFrame)

        self.setLayout(layout)
        self.setWindowTitle("Configure Imageplay")
        self.setWindowModality(Qt.ApplicationModal)

    @staticmethod
    def create_spinner_layout(label, spinbox):
        layout = QHBoxLayout()
        layout.addWidget(QLabel(label))
        layout.addStretch(1)
        layout.addWidget(spinbox)
        return layout

    @staticmethod
    def image_delay_change(delay):
        Imageplay.settings.apply_setting(SettingsKeys.image_delay, delay * 1000)

    @staticmethod
    def animation_delay_change(delay):
        Imageplay.settings.apply_setting(SettingsKeys.gif_delay, delay * 1000)

    def recurse_change(self):
        Imageplay.settings.apply_setting(SettingsKeys.recurse_subdirs, self.recurse.isChecked())

    def gif_by_frame_change(self):
        Imageplay.settings.apply_setting(SettingsKeys.gif_by_frame, self.gifByFrame.isChecked())
