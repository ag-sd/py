import os

from PyQt5.QtWidgets import QSpinBox, QHBoxLayout, QLabel, QBoxLayout

from FileWrangler import logger, FileWranglerCore
from FileWrangler.FileWranglerCore import ConfigKeys, RenameUIOperation

NAME = "Separator"
DESCRIPTION = "Tokenizes the filename by separator and extracts all or part of the file name"
KEY_FILE_SEPARATOR = "File_Separator"
KEY_NEW_SEPARATOR = "New Separator"
KEY_REPEAT = "Repeat"


def get_key(file, context) -> str:
    file_splitter = context[KEY_FILE_SEPARATOR]
    # Discard path and only work on filename
    _, file_name = os.path.split(file)
    file_name, _ = os.path.splitext(file_name)
    tokens = file_name.split(file_splitter)

    if len(tokens) >= context[KEY_REPEAT]:
        return context[KEY_NEW_SEPARATOR].join(tokens[:context[KEY_REPEAT]])
    else:
        return FileWranglerCore.UNKNOWN_KEY


def get_context(file_sep: str, new_sep: str, repeat: int) -> dict:
    return {
        KEY_FILE_SEPARATOR: file_sep,
        KEY_NEW_SEPARATOR: new_sep,
        KEY_REPEAT: repeat
    }


class SeparatorUIOperation(RenameUIOperation):
    # {del}/{0} in {1}/{del}

    def __init__(self):
        super().__init__(name=NAME, description=DESCRIPTION)
        self.file_separator = self._get_editable_combo(FileWranglerCore.DEFAULT_SPLITTER)
        self.new_separator = self._get_editable_combo(FileWranglerCore.DEFAULT_SPLITTER)

        self.key_match_counter = QSpinBox()
        self.key_match_counter.setMinimum(1)
        self.key_match_counter.setValue(1)
        self.key_match_counter.setMaximum(10)

        self.file_separator.editTextChanged.connect(self._emit_merge_event)
        self.new_separator.editTextChanged.connect(self._emit_merge_event)
        self.key_match_counter.valueChanged.connect(self._emit_merge_event)

    def is_ready(self) -> bool:
        if self._none_or_empty(self.file_separator.currentText()):
            logger.error("Key Separator cannot be empty!")
            return False
        return True

    def get_context(self) -> dict:
        return get_context(file_sep=self.file_separator.currentText(),
                           new_sep=self.new_separator.currentText(),
                           repeat=self.key_match_counter.value())

    def save_state(self):
        self._save_combo_current_text(self.file_separator)
        self._save_combo_current_text(self.new_separator)

    def _get_key(self, file, config) -> str:
        context = config[ConfigKeys.context]
        return get_key(file, context)

    def _get_layout(self) -> QBoxLayout:
        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("File Separator"))
        key_layout.addWidget(self.file_separator, stretch=1)
        key_layout.addWidget(QLabel("New Separator"))
        key_layout.addWidget(self.new_separator, stretch=1)
        key_layout.addWidget(QLabel("Match Count"))
        key_layout.addWidget(self.key_match_counter)
        return key_layout

