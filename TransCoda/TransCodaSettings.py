import pickle
from enum import Enum, unique
from functools import partial

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QCheckBox, QDialogButtonBox, QLabel, QVBoxLayout, QSpinBox, QHBoxLayout

import TransCoda
from CommonUtils import AppSettings, CommandExecutionFactory
from CustomUI import FileChooserTextBox, QHLine
from TransCoda import TransCodaEditor


@unique
class SettingsKeys(Enum):
    output_dir = "output_dir"
    preserve_dir = "preserve_dir"
    encoder_path = "encoder_path"
    encoder_details = "encoder_details"
    overwrite_files = "overwrite_existing"
    preserve_times = "preserve_times"
    encode_list = "encode_list"
    max_threads = "max_threads"
    delete_metadata = "delete_metadata"
    single_thread_video = "single_thread_video"


settings = AppSettings(
    "TransCoda",
    {}
)


def set_setting(setting, value):
    TransCoda.logger.info(f"{setting} -> {value}")
    settings.apply_setting(setting, value)


def get_setting(setting, default=None):
    return settings.get_setting(setting, default)


def get_output_dir():
    return settings.get_setting(SettingsKeys.output_dir, None)


def get_max_threads():
    return settings.get_setting(SettingsKeys.max_threads, CommandExecutionFactory([]).get_max_threads())


def get_encoder():
    return settings.get_setting(SettingsKeys.encoder_details, None)


def get_encoder_name():
    return settings.get_setting(SettingsKeys.encoder_path, None)


def get_preserve_dir():
    return settings.get_setting(SettingsKeys.preserve_dir, Qt.Checked) == Qt.Checked


def get_overwrite_if_exists():
    return settings.get_setting(SettingsKeys.overwrite_files, Qt.Checked) == Qt.Checked


def get_preserve_timestamps():
    return settings.get_setting(SettingsKeys.preserve_times, Qt.Checked) == Qt.Checked


def get_delete_metadata():
    return settings.get_setting(SettingsKeys.delete_metadata, Qt.Unchecked) == Qt.Checked


def save_encode_list(items):
    items_pickle = pickle.dumps(items)
    settings.apply_setting(SettingsKeys.encode_list, items_pickle)


def get_encode_list():
    items_pickle = settings.get_setting(SettingsKeys.encode_list)
    if items_pickle:
        return pickle.loads(items_pickle)
    return []


class TransCodaSettings(QDialog):

    def __init__(self):
        super().__init__()
        self.output_dir = FileChooserTextBox("Output :", "Select Output Directory", True)
        self.preserve_dir = QCheckBox("Preserve Directory Structure")
        self.overwrite_files = QCheckBox("Overwrite files if they exist")
        self.preserve_times = QCheckBox("Preserve original file times in result")
        self.delete_metadata = QCheckBox("Delete all tag information in result")
        self.single_thread_video = QCheckBox("Process video in a single thread only")
        self.encoder_editor = TransCodaEditor.TransCodaEditor()
        self.max_threads = QSpinBox()
        self.init_ui()
        self.load_settings_and_hooks()

    def load_settings_and_hooks(self):
        self.output_dir.setSelection(settings.get_setting(SettingsKeys.output_dir, ""))
        self.output_dir.file_selection_changed.connect(partial(self.set_setting, SettingsKeys.output_dir))

        self._set_checkbox(self.preserve_dir, SettingsKeys.preserve_dir, self.set_setting)
        self._set_checkbox(self.preserve_times, SettingsKeys.preserve_times, self.set_setting)
        self._set_checkbox(self.delete_metadata, SettingsKeys.delete_metadata, self.set_setting)
        self._set_checkbox(self.overwrite_files, SettingsKeys.overwrite_files, self.set_setting)
        self._set_checkbox(self.single_thread_video, SettingsKeys.single_thread_video, self.set_setting)

        self.encoder_editor.select_encoder(settings.get_setting(SettingsKeys.encoder_path, "NA"))
        self.encoder_editor.encoder_changed.connect(self.set_encoder)

        self.max_threads.setMinimum(1)
        self.max_threads.setMaximum(CommandExecutionFactory([]).get_max_threads())
        self.max_threads.setValue(settings.get_setting(SettingsKeys.max_threads, self.max_threads.maximum()))
        self.max_threads.valueChanged.connect(partial(self.set_setting, SettingsKeys.max_threads))

    def init_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(self.output_dir)
        layout.addWidget(self.preserve_dir)
        layout.addWidget(self.preserve_times)
        layout.addWidget(self.delete_metadata)
        layout.addWidget(self.overwrite_files)

        layout.addWidget(QHLine())
        layout.addWidget(self.encoder_editor)

        layout.addWidget(QHLine())
        layout.addWidget(QLabel("Advanced"))
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel("Number of files to encode at the same time"))
        h_layout.addWidget(self.max_threads)
        layout.addLayout(h_layout)
        layout.addWidget(self.single_thread_video)

        layout.addWidget(QHLine())
        buttons = QDialogButtonBox(QDialogButtonBox.Ok, Qt.Horizontal, self)
        buttons.clicked.connect(self.close)
        layout.addWidget(buttons)
        self.setLayout(layout)
        self.setWindowTitle("Settings")

    @staticmethod
    def set_encoder(path, encoder):
        set_setting(SettingsKeys.encoder_path, path)
        set_setting(SettingsKeys.encoder_details, encoder)

    @staticmethod
    def set_setting(setting, value):
        TransCoda.logger.info(f"{setting} -> {value}")
        settings.apply_setting(setting, value)

    @staticmethod
    def _set_checkbox(checkbox, setting_key, connect_method):
        checkbox.setChecked(settings.get_setting(setting_key) == Qt.Checked)
        checkbox.stateChanged.connect(partial(connect_method, setting_key))
