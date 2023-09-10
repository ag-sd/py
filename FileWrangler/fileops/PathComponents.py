import os

from PyQt5.QtWidgets import QSpinBox, QBoxLayout, QHBoxLayout, QLabel, QCheckBox

from FileWrangler import FileWranglerCore, logger
from FileWrangler.FileWranglerCore import RenameUIOperation, ConfigKeys


NAME = "Use Path Components"
DESCRIPTION = "Use path components to compose a new file name"
KEY_FILE_SEPARATOR = "File_Separator"
KEY_PATH_COMPONENT = "Path_Component"
KEY_ORDER_REVERSED = "Order_Reversed"


def get_key(file, context):
    file_splitter = context[KEY_FILE_SEPARATOR]
    path, _ = os.path.split(file)
    norm_path = os.path.normpath(path)
    path_keys = norm_path.split(os.sep)
    if context[KEY_PATH_COMPONENT] >= len(path_keys):
        return FileWranglerCore.UNKNOWN_KEY
    path_keys = path_keys[-context[KEY_PATH_COMPONENT]:]
    if context[KEY_ORDER_REVERSED]:
        path_keys.reverse()
    return f"{file_splitter.join(path_keys)}"


def get_context(separator: str, component_count: int, reverse: bool) -> dict:
    return {
        KEY_FILE_SEPARATOR: separator,
        KEY_PATH_COMPONENT: component_count,
        KEY_ORDER_REVERSED: reverse
    }


class PathComponentsUIOperation(RenameUIOperation):

    def __init__(self):
        super().__init__(name=NAME, description=DESCRIPTION)
        self.dir_include = QSpinBox()
        self.dir_include.setMinimum(1)
        self.dir_include.setValue(1)
        self.dir_include.setMaximum(10)
        self.file_separator = self._get_editable_combo(FileWranglerCore.DEFAULT_SPLITTER)
        self.reverse_order_checkbox = QCheckBox("Reverse Order")
        self.file_separator.editTextChanged.connect(self._emit_merge_event)
        self.dir_include.valueChanged.connect(self._emit_merge_event)
        self.reverse_order_checkbox.stateChanged.connect(self._emit_merge_event)

    def is_ready(self) -> bool:
        if self._none_or_empty(self.file_separator.currentText()):
            logger.error("Key Separator cannot be empty!")
            return False
        return True

    def get_context(self) -> dict:
        return get_context(
            separator=self.file_separator.currentText(),
            component_count=self.dir_include.value(),
            reverse=self.reverse_order_checkbox.isChecked()
        )

    def save_state(self):
        self._save_combo_current_text(self.file_separator)

    def _get_source_key(self, file, config) -> str:
        return get_key(file, config[ConfigKeys.context])

    def _get_layout(self) -> QBoxLayout:
        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("Dir Count"))
        key_layout.addWidget(self.dir_include)
        key_layout.addWidget(QLabel("File Separator"))
        key_layout.addWidget(self.file_separator, stretch=1)
        key_layout.addWidget(self.reverse_order_checkbox)
        return key_layout
