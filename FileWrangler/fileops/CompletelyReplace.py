from PyQt5.QtWidgets import QLabel, QHBoxLayout, QBoxLayout

from FileWrangler import logger, FileWranglerCore, std_separator
from FileWrangler.FileWranglerCore import RenameUIOperation

NAME = "Completely Replace"
DESCRIPTION = "Completely replace the filename with the new value provided."
KEY_TOKEN = "Token"
KEY_FILE_SEPARATOR = "File_Separator"


def get_key(_, context) -> str:
    return context[KEY_TOKEN]


def get_context(replacement_text: str) -> dict:
    return {
        KEY_TOKEN: replacement_text,
        KEY_FILE_SEPARATOR: std_separator
    }


class CompletelyReplaceUIOperation(RenameUIOperation):
    def __init__(self):
        super().__init__(name=NAME, description=DESCRIPTION)
        self.key_token_string = self._get_editable_combo()
        self.key_token_string.editTextChanged.connect(self._emit_merge_event)

    def is_ready(self) -> bool:
        if self._none_or_empty(self.key_token_string.currentText()):
            logger.error("Key Identifier cannot be empty!")
            return False
        return True

    def get_context(self) -> dict:
        return get_context(self.key_token_string.currentText())

    def save_state(self):
        self._save_combo_current_text(self.key_token_string)

    def _get_source_key(self, file, config) -> str:
        return get_key(file, config[FileWranglerCore.ConfigKeys.context])

    def _get_layout(self) -> QBoxLayout:
        layout = QHBoxLayout()
        layout.addWidget(QLabel("Replace filename with : "))
        layout.addWidget(self.key_token_string, stretch=1)
        return layout


