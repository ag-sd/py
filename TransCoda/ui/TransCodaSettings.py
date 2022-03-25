import pickle
from enum import Enum, unique
from functools import partial

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QCheckBox, QDialogButtonBox, QLabel, QVBoxLayout, QSpinBox, QHBoxLayout, QLineEdit

import TransCoda
from CommonUtils import AppSettings, CommandExecutionFactory
from CustomUI import FileChooserTextBox, QHLine
from TransCoda.ui import TransCodaEditor


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
    sort_by_size = "sort_by_size"
    skip_previously_processed = "skip_previously_processed"
    columns = "columns"
    sort_order = "sort_order"
    copy_extensions = "copy_extensions"
    use_system_theme = "use_system_theme"


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
    return settings.get_setting(SettingsKeys.preserve_dir, Qt.Unchecked) == Qt.Checked


def get_overwrite_if_exists():
    return settings.get_setting(SettingsKeys.overwrite_files, Qt.Unchecked) == Qt.Checked


def get_preserve_timestamps():
    return settings.get_setting(SettingsKeys.preserve_times, Qt.Unchecked) == Qt.Checked


def get_delete_metadata():
    return settings.get_setting(SettingsKeys.delete_metadata, Qt.Unchecked) == Qt.Checked


def is_history_enforced():
    return settings.get_setting(SettingsKeys.skip_previously_processed, Qt.Unchecked) == Qt.Checked


def sort_by_size():
    return settings.get_setting(SettingsKeys.sort_by_size, Qt.Unchecked) == Qt.Checked


def use_system_theme():
    return settings.get_setting(SettingsKeys.use_system_theme, Qt.Unchecked) == Qt.Checked


def get_copy_extensions():
    return settings.get_setting(SettingsKeys.copy_extensions, "")


def is_single_thread_video():
    return settings.get_setting(SettingsKeys.single_thread_video, Qt.Unchecked) == Qt.Checked


def save_encode_list(items):
    items_pickle = pickle.dumps(items)
    settings.apply_setting(SettingsKeys.encode_list, items_pickle)


def get_encode_list():
    items_pickle = settings.get_setting(SettingsKeys.encode_list)
    if items_pickle:
        return pickle.loads(items_pickle)
    return []


def save_columns(columns):
    items_pickle = pickle.dumps(columns)
    settings.apply_setting(SettingsKeys.columns, items_pickle)


def get_columns():
    items_pickle = settings.get_setting(SettingsKeys.columns)
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
        self.use_system_theme = QCheckBox("Use System theme for icons (requires restart)")
        self.history = QCheckBox("Skip files if they have been processed before")
        self.sort_by_size = QCheckBox("Encode the largest files first")
        self.encoder_editor = TransCodaEditor.TransCodaEditor(caption="Available Encoders")
        self.max_threads = QSpinBox()
        self.unsupported_extensions_to_copy = QLineEdit()
        self.init_ui()
        self.load_settings_and_hooks()

    def load_settings_and_hooks(self):
        self.output_dir.setSelection(settings.get_setting(SettingsKeys.output_dir, ""))
        self.output_dir.file_selection_changed.connect(partial(self.set_setting, SettingsKeys.output_dir))

        self._set_checkbox(self.preserve_dir, SettingsKeys.preserve_dir, self.set_setting)
        self._set_checkbox(self.preserve_times, SettingsKeys.preserve_times, self.set_setting)
        self._set_checkbox(self.delete_metadata, SettingsKeys.delete_metadata, self.set_setting)
        self._set_checkbox(self.overwrite_files, SettingsKeys.overwrite_files, self.set_setting)
        self._set_checkbox(self.history, SettingsKeys.skip_previously_processed, self.set_setting)
        self._set_checkbox(self.sort_by_size, SettingsKeys.sort_by_size, self.set_setting)
        self._set_checkbox(self.single_thread_video, SettingsKeys.single_thread_video, self.set_setting)
        self._set_checkbox(self.use_system_theme, SettingsKeys.use_system_theme, self.set_setting)

        self.encoder_editor.select_encoder(settings.get_setting(SettingsKeys.encoder_path, "NA"))
        self.encoder_editor.encoder_changed.connect(self.set_encoder)

        self.max_threads.setMinimum(1)
        self.max_threads.setMaximum(CommandExecutionFactory([]).get_max_threads())
        self.max_threads.setValue(settings.get_setting(SettingsKeys.max_threads, self.max_threads.maximum()))
        self.max_threads.valueChanged.connect(partial(self.set_setting, SettingsKeys.max_threads))

        self.unsupported_extensions_to_copy.setText(get_copy_extensions())
        self.unsupported_extensions_to_copy.editingFinished.connect(partial(self.set_setting,
                                                                            SettingsKeys.copy_extensions))

    def init_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(self.output_dir)
        layout.addWidget(self.preserve_dir)
        layout.addWidget(self.preserve_times)
        layout.addWidget(self.delete_metadata)
        layout.addWidget(self.overwrite_files)
        layout.addWidget(self.history)
        layout.addWidget(self.sort_by_size)

        layout.addWidget(QHLine())
        layout.addWidget(self.encoder_editor)

        layout.addWidget(QHLine())
        layout.addWidget(QLabel("<u>Advanced</u>"))
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel("Number of files to encode at the same time"))
        h_layout.addWidget(self.max_threads)
        layout.addLayout(h_layout)
        layout.addWidget(self.single_thread_video)

        layout.addWidget(QHLine())
        layout.addWidget(QLabel("<u>Unsupported files</u>"))
        layout.addWidget(QLabel("Copy files with the following extensions to output\n(Separate with ;)"))
        layout.addWidget(self.unsupported_extensions_to_copy)

        layout.addWidget(QHLine())
        layout.addWidget(QLabel("<u>Appearance</u>"))
        layout.addWidget(self.use_system_theme)

        layout.addWidget(QHLine())
        buttons = QDialogButtonBox(QDialogButtonBox.Ok, Qt.Horizontal, self)
        buttons.clicked.connect(self.close)
        layout.addWidget(buttons)
        self.setLayout(layout)
        self.setWindowTitle("Settings")
        self.setWindowIcon(TransCoda.theme.ico_app_icon)

    @staticmethod
    def set_encoder(path, encoder):
        set_setting(SettingsKeys.encoder_path, path)
        set_setting(SettingsKeys.encoder_details, encoder)

    def set_setting(self, setting, value=None):
        if setting == SettingsKeys.copy_extensions:
            value = self.unsupported_extensions_to_copy.text()
        TransCoda.logger.info(f"{setting} -> {value}")
        settings.apply_setting(setting, value)

    @staticmethod
    def _set_checkbox(checkbox, setting_key, connect_method):
        checkbox.setChecked(settings.get_setting(setting_key) == Qt.Checked)
        checkbox.stateChanged.connect(partial(connect_method, setting_key))
