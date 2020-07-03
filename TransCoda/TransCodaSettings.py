import json
import pickle
from enum import Enum, unique
from functools import partial

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QCheckBox, QComboBox, QDialogButtonBox, QLabel, QVBoxLayout, QSpinBox, QHBoxLayout

import TransCoda
from CommonUtils import AppSettings, CommandExecutionFactory
from CustomUI import FileChooserTextBox, QHLine
from TransCoda import TransCodaEditor
from TransCoda.Encoda import Encoders
from TransCoda.TransCodaEditor import EncoderModel


@unique
class SettingsKeys(Enum):
    output_dir = "output_dir"
    preserve_dir = "preserve_dir"
    encoder = "encoder"
    overwrite_files = "overwrite_existing"
    preserve_times = "preserve_times"
    encode_list = "encode_list"
    max_theads = "max_threads"
    delete_metadata = "delete_medatata"


settings = AppSettings(
    "TransCoda",
    {}
)


class TransCodaSettings(QDialog):

    def __init__(self):
        super().__init__()
        self.output_dir = FileChooserTextBox("Output :", "Select Output Directory", True)
        self.preserve_dir = QCheckBox("Preserve Directory Structure")
        self.overwrite_files = QCheckBox("Overwrite files if they exist")
        self.preserve_times = QCheckBox("Preserve original file times in result")
        self.delete_metadata = QCheckBox("Delete all tag information in result")
        with open(TransCodaEditor.get_config_file()) as json_file:
            encoder_model = EncoderModel(json.load(json_file), disable_selections=True)
            self.encoder = TransCodaEditor.EncoderSelector(encoder_model)
        self.max_threads = QSpinBox()
        # for e in Encoders:
        #     self.encoder.addItem(str(e), e)
        self.init_ui()
        self.load_settings_and_hooks()

    def load_settings_and_hooks(self):
        self.output_dir.setSelection(settings.get_setting(SettingsKeys.output_dir, ""))
        self.output_dir.file_selection_changed.connect(partial(self.set_setting, SettingsKeys.output_dir))

        self.preserve_dir.setChecked(settings.get_setting(SettingsKeys.preserve_dir) == Qt.Checked)
        self.preserve_dir.stateChanged.connect(partial(self.set_setting, SettingsKeys.preserve_dir))

        self.preserve_times.setChecked(settings.get_setting(SettingsKeys.preserve_times) == Qt.Checked)
        self.preserve_times.stateChanged.connect(partial(self.set_setting, SettingsKeys.preserve_times))

        self.delete_metadata.setChecked(settings.get_setting(SettingsKeys.delete_metadata) == Qt.Checked)
        self.delete_metadata.stateChanged.connect(partial(self.set_setting, SettingsKeys.delete_metadata))

        self.overwrite_files.setChecked(settings.get_setting(SettingsKeys.overwrite_files) == Qt.Checked)
        self.overwrite_files.stateChanged.connect(partial(self.set_setting, SettingsKeys.overwrite_files))

        encoder = settings.get_setting(SettingsKeys.encoder, "NA")
        match = self.encoder.findText(encoder, Qt.MatchExactly)
        if match >= 0:
            self.encoder.setCurrentIndex(match)
        self.encoder.currentTextChanged.connect(partial(self.set_setting, SettingsKeys.encoder))

        self.max_threads.setMinimum(1)
        self.max_threads.setMaximum(CommandExecutionFactory([]).get_max_threads())
        self.max_threads.setValue(settings.get_setting(SettingsKeys.max_theads, self.max_threads.maximum()))
        self.max_threads.valueChanged.connect(partial(self.set_setting, SettingsKeys.max_theads))

    def init_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(self.output_dir)
        layout.addWidget(self.preserve_dir)
        layout.addWidget(self.preserve_times)
        layout.addWidget(self.delete_metadata)
        layout.addWidget(self.overwrite_files)

        layout.addWidget(QHLine())
        layout.addWidget(QLabel("Encoder"))
        layout.addWidget(self.encoder)

        layout.addWidget(QHLine())
        layout.addWidget(QLabel("Advanced"))
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel("Number of files to encode at the same time"))
        h_layout.addWidget(self.max_threads)
        layout.addLayout(h_layout)

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
    def get_max_threads():
        return settings.get_setting(SettingsKeys.max_theads, CommandExecutionFactory([]).get_max_threads())

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

    @staticmethod
    def get_delete_metadata():
        return TransCodaSettings.settings_container.get_setting(SettingsKeys.delete_metadata, Qt.Unchecked) == Qt.Checked

    @staticmethod
    def save_encode_list(items):
        items_pickle = pickle.dumps(items)
        TransCodaSettings.settings_container.apply_setting(SettingsKeys.encode_list, items_pickle)

    @staticmethod
    def get_encode_list():
        items_pickle = TransCodaSettings.settings_container.get_setting(SettingsKeys.encode_list)
        if items_pickle:
            return pickle.loads(items_pickle)
        return []
