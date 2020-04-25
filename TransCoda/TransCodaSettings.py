from enum import Enum, unique
from functools import partial

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QCheckBox, QComboBox, QDialogButtonBox, QLabel, QVBoxLayout

import TransCoda
from CommonUtils import AppSettings
from CustomUI import FileChooserTextBox, QHLine
from TransCoda.Encoda import Encoders


@unique
class SettingsKeys(Enum):
    output_dir = "output_dir"
    preserve_dir = "preserve_dir"
    encoder = "encoder"
    overwrite_files = "overwrite_existing"
    preserve_times = "preserve_times"


settings = AppSettings(
    "TransCoda",
    {}
)


class TransCodaSettings(QDialog):

    def __init__(self):
        super(TransCodaSettings, self).__init__()
        self.output_dir = FileChooserTextBox("Output :", "Select Output Directory", True)
        self.preserve_dir = QCheckBox("Preserve Directory Structure")
        self.overwrite_files = QCheckBox("Overwrite files if they exist")
        self.preserve_times = QCheckBox("Preserve original file times in result")
        self.encoder = QComboBox()
        for e in Encoders:
            self.encoder.addItem(str(e), e)
        self.init_ui()
        self.load_settings_and_hooks()

    def load_settings_and_hooks(self):
        self.output_dir.setSelection(settings.get_setting(SettingsKeys.output_dir, ""))
        self.output_dir.file_selection_changed.connect(partial(self.set_setting, SettingsKeys.output_dir))

        self.preserve_dir.setChecked(settings.get_setting(SettingsKeys.preserve_dir) == Qt.Checked)
        self.preserve_dir.stateChanged.connect(partial(self.set_setting, SettingsKeys.preserve_dir))

        self.preserve_times.setChecked(settings.get_setting(SettingsKeys.preserve_times) == Qt.Checked)
        self.preserve_times.stateChanged.connect(partial(self.set_setting, SettingsKeys.preserve_times))

        self.overwrite_files.setChecked(settings.get_setting(SettingsKeys.overwrite_files) == Qt.Checked)
        self.overwrite_files.stateChanged.connect(partial(self.set_setting, SettingsKeys.overwrite_files))

        encoder = settings.get_setting(SettingsKeys.encoder, "NA")
        match = self.encoder.findText(encoder, Qt.MatchExactly)
        if match >= 0:
            self.encoder.setCurrentIndex(match)
        self.encoder.currentTextChanged.connect(partial(self.set_setting, SettingsKeys.encoder))

    def init_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(self.output_dir)
        layout.addWidget(self.preserve_dir)
        layout.addWidget(self.preserve_times)
        layout.addWidget(self.overwrite_files)

        layout.addWidget(QHLine())
        layout.addWidget(QLabel("Encoder"))
        layout.addWidget(self.encoder)

        layout.addWidget(QHLine())
        buttons = QDialogButtonBox(QDialogButtonBox.Ok, Qt.Horizontal, self)
        buttons.clicked.connect(self.close)
        layout.addWidget(buttons)
        self.setLayout(layout)
        self.setWindowTitle("Settings")

    settings_container = settings

    def set_setting(self, setting, value):
        TransCoda.logger.info(f"{setting} -> {value}")
        settings.apply_setting(setting, value)

    @staticmethod
    def get_setting(setting, default=None):
        return TransCodaSettings.settings_container.get_setting(setting, default)

    @staticmethod
    def get_output_dir():
        return settings.get_setting(SettingsKeys.output_dir, None)

    @staticmethod
    def get_encoder():
        encoder = TransCodaSettings.settings_container.get_setting(SettingsKeys.encoder, None)
        if encoder is not None and encoder in Encoders.__lookup__:
            return Encoders.__lookup__[encoder]
        return None

    @staticmethod
    def get_encoder_name():
        return TransCodaSettings.settings_container.get_setting(SettingsKeys.encoder, None)

    @staticmethod
    def get_preserve_dir():
        return TransCodaSettings.settings_container.get_setting(SettingsKeys.preserve_dir, Qt.Checked) == Qt.Checked

    @staticmethod
    def get_overwrite_if_exists():
        return TransCodaSettings.settings_container.get_setting(SettingsKeys.overwrite_files, Qt.Checked) == Qt.Checked

    @staticmethod
    def get_preserve_timestamps():
        return TransCodaSettings.settings_container.get_setting(SettingsKeys.preserve_times, Qt.Checked) == Qt.Checked




