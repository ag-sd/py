import sys
from enum import Enum, unique
from functools import partial

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QDialog, QSpinBox, QCheckBox, QVBoxLayout, QLabel, QApplication, QDialogButtonBox, \
    QHBoxLayout, QLineEdit

import Imageplay
from CommonUtils import AppSettings
from CustomUI import QHLine


@unique
class SettingsKeys(Enum):
    image_delay = "image_delay"
    animation_speed = "animation_speed"
    animation_by_frame = "gif_by_frame"
    animation_loop = "animation_loop"
    recurse_subdirs = "recurse_subdirs"
    shuffle = "shuffle"
    loop = "loop"
    image_scaled = "image_scaled"
    external_app = "external_app"


_settings = AppSettings(
    "ImagePlay",
    {}
)


def _set_setting(setting, value):
    Imageplay.logger.info(f"{setting} -> {value}")
    _settings.apply_setting(setting, value)


def _get_setting(setting, default=None):
    return _settings.get_setting(setting, default)


def get_recurse():
    return _settings.get_setting(SettingsKeys.recurse_subdirs, False)


def get_animation_by_frame():
    return _settings.get_setting(SettingsKeys.recurse_subdirs, False)


def get_image_delay():
    return _settings.get_setting(SettingsKeys.image_delay, 10)


def get_loop():
    return _settings.get_setting(SettingsKeys.loop, True)


def set_loop(value):
    _set_setting(SettingsKeys.loop, value)


def get_shuffle():
    return _settings.get_setting(SettingsKeys.shuffle, False)


def set_shuffle(value):
    _set_setting(SettingsKeys.shuffle, value)


def get_animation_loop():
    return _settings.get_setting(SettingsKeys.animation_loop, 5)


def get_animation_speed():
    return _settings.get_setting(SettingsKeys.animation_speed, 50)


def get_image_scaled():
    return _settings.get_setting(SettingsKeys.image_scaled, False)


def set_image_scaled(value):
    _set_setting(SettingsKeys.image_scaled, value)


def get_external_app():
    return _settings.get_setting(SettingsKeys.external_app, None)


class ImagePlaySettings(QDialog):

    setting_changed_event = pyqtSignal(SettingsKeys, 'PyQt_PyObject')

    def __init__(self):
        super().__init__()
        self.image_spinner = QSpinBox()
        self.image_spinner.setMinimum(1)

        self.animation_spinner = QSpinBox()
        self.animation_spinner.setMinimum(1)
        self.animation_spinner.setMaximum(100)

        self.animation_loop = QSpinBox()
        self.animation_loop.setMinimum(-1)

        self.recurse = QCheckBox("Scan all child directories for images")
        self.animation_by_frame = QCheckBox("View animation files one frame at a time")

        self.external_app = QLineEdit()
        self.external_app.setPlaceholderText("External Application to open image in")
        external_app = _get_setting(SettingsKeys.external_app)
        if external_app:
            self.external_app.setText(external_app)

        self.init_ui()
        self.load_settings_and_hooks()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(self.recurse)
        layout.addLayout(self.create_spinner_layout(QLabel("Load next image in (seconds)"), self.image_spinner))
        layout.addWidget(QHLine())
        layout.addWidget(self.animation_by_frame)
        layout.addLayout(self.create_spinner_layout(QLabel("Animation speed (%)"), self.animation_spinner))
        layout.addLayout(self.create_spinner_layout(QLabel("Times to loop (-1 is infinite)"), self.animation_loop))
        layout.addWidget(QHLine())
        layout.addWidget(self.external_app)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok, Qt.Horizontal, self)
        buttons.clicked.connect(self.close)
        layout.addWidget(buttons)

        self.setLayout(layout)
        self.setWindowTitle("Configure Imageplay")
        self.setWindowModality(Qt.ApplicationModal)

    def load_settings_and_hooks(self):
        self.recurse.setChecked(get_recurse())
        self.recurse.stateChanged.connect(partial(self.hook, SettingsKeys.recurse_subdirs))

        self.animation_by_frame.setChecked(get_animation_by_frame())
        self.animation_by_frame.stateChanged.connect(partial(self.hook, SettingsKeys.animation_by_frame))

        self.animation_spinner.setMinimum(1)
        self.animation_spinner.setValue(get_animation_speed())
        self.animation_spinner.valueChanged.connect(partial(self.hook, SettingsKeys.animation_speed))
        self.animation_spinner.setEnabled(self.animation_by_frame.isChecked())

        self.image_spinner.setMinimum(1)
        self.image_spinner.setValue(get_image_delay())
        self.image_spinner.valueChanged.connect(partial(self.hook, SettingsKeys.image_delay))
        self.external_app.textEdited.connect(partial(self.hook, SettingsKeys.external_app))

    @staticmethod
    def create_spinner_layout(label, spinbox):
        layout = QHBoxLayout()
        layout.addWidget(label)
        layout.addStretch(1)
        layout.addWidget(spinbox)
        return layout

    def hook(self, setting, value=None):
        if setting == SettingsKeys.animation_by_frame:
            self.animation_spinner.setEnabled(self.animation_by_frame.isChecked())
        _set_setting(setting, value)
        self.setting_changed_event.emit(setting, value)
    

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ImagePlaySettings()
    ex.show()
    sys.exit(app.exec_())