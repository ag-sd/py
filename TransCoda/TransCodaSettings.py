from enum import Enum, unique

from PyQt5.QtWidgets import QDialog, QGridLayout, QCheckBox, QComboBox, QDialogButtonBox, QLabel
from PyQt5.QtCore import Qt, pyqtSignal

from CommonUtils import AppSettings
from CustomUI import FileChooserTextBox, QHLine
from TransCoda import Encoda


@unique
class SettingsKeys(Enum):
    output_dir = "output_dir"
    preserve_dir = "preserve_dir"
    encoder = "encoder"


settings = AppSettings(
    "TransCoda",
    {}
)


class TransCodaSettings(QDialog):

    def __init__(self):
        super(TransCodaSettings, self).__init__()
        self.output_dir = FileChooserTextBox("Output :", "Select Output Directory", True)
        self.preserve_dir = QCheckBox("Preserve Directory Structure")
        self.encoder = QComboBox()
        self.encoder.addItems(Encoda.available_encoders.keys())
        self.init_ui()
        self.load_settings_and_hooks()

    def load_settings_and_hooks(self):
        self.output_dir.setSelection(settings.get_setting(SettingsKeys.output_dir, ""))
        self.output_dir.file_selection_changed.connect(TransCodaSettings.output_dir_changed)
        self.preserve_dir.setChecked(settings.get_setting(SettingsKeys.preserve_dir) == Qt.Checked)
        self.preserve_dir.stateChanged.connect(TransCodaSettings.preserve_dir_changed)
        encoder = settings.get_setting(SettingsKeys.encoder, "NA")
        match = self.encoder.findText(encoder, Qt.MatchExactly)
        if match >= 0:
            self.encoder.setCurrentIndex(match)
        self.encoder.currentTextChanged.connect(self.encoder_changed)

    def init_ui(self):
        layout = QGridLayout()
        layout.addWidget(self.output_dir, 0, 0)
        layout.addWidget(self.preserve_dir, 1, 0)
        layout.addWidget(QHLine(), 2, 0)
        layout.addWidget(QLabel("Encoder"), 3, 0)
        layout.addWidget(self.encoder, 4, 0)

        layout.addWidget(QHLine(), 5, 0)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
                                   Qt.Horizontal, self)
        layout.addWidget(buttons, 6, 0)
        self.setLayout(layout)
        self.setWindowTitle("Settings")

    settings_container = settings

    @staticmethod
    def output_dir_change(output_dir):
        settings.apply_setting(SettingsKeys.output_dir, output_dir)

    @staticmethod
    def preserve_dir_changed(preserve_dir):
        settings.apply_setting(SettingsKeys.preserve_dir, preserve_dir)

    @staticmethod
    def encoder_changed(encoder):
        settings.apply_setting(SettingsKeys.encoder, encoder)

    @staticmethod
    def output_dir_changed(output_dir):
        settings.apply_setting(SettingsKeys.output_dir, output_dir)

    @staticmethod
    def get_output_dir():
        return settings.get_setting(SettingsKeys.output_dir, None)

    @staticmethod
    def get_encoder():
        encoder = TransCodaSettings.settings_container.get_setting(SettingsKeys.encoder, None)
        if encoder is not None and Encoda.available_encoders.__contains__(encoder):
            return Encoda.available_encoders[encoder]
        return None

    @staticmethod
    def get_preserve_dir():
        return TransCodaSettings.settings_container.get_setting(SettingsKeys.preserve_dir, False)


