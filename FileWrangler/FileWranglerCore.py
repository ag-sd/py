import os
import re
from datetime import datetime
from enum import Enum

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QBoxLayout, QComboBox, QWidget

from FileWrangler import logger, std_separator
from common.CommonUtils import FileScanner

UNKNOWN_KEY = "Unknown"
CTX_FILE_SEPARATOR = "File_Separator"
DEFAULT_SPLITTER = std_separator
EMPTY_STR = ""
_DEFAULT_REGEX = ".+?(?= - )"


class DisplayKeys(Enum):
    source = "source"
    target = "target"


class ConfigKeys(Enum):
    append_date = 0
    key_type = 2
    sort_by = 5
    context = 7
    is_version_2 = 8
    operation = 9
    fill_gaps = 10


class SortBy(Enum):
    name = 1
    date = 2
    size = 3
    none = 4


class ActionKeys(Enum):
    copy = "Copy"
    move = "Move"
    help = "Help"


def create_merge_tree(files, target_directory, config):
    """
    Create keys for the files.
    Then find files matching those keys in the target_directory
    For each matching key, determine point of insertion of new file

    :param config: Key generation config
    :param files:
    :param target_directory:
    :return:
    """

    if files is None:
        return
    if target_directory is None:
        return

    file_model = []

    # Step 1: Find all files in Destination
    target_scanner = FileScanner([target_directory], recurse=False, is_qfiles=False)

    # Step 2: Find all unique keys in destination dir
    reference_keys = _create_destination_keymap(target_scanner.files, config)

    # Step 3: Find all source files from input (including expanded directories)
    source_scanner = FileScanner(files, recurse=True, is_qfiles=True)

    # For each source file:
    for file in _sort_files(source_scanner.files, config):
        key = _create_key(file, config)
        _, ext = os.path.splitext(file)
        file_model.append(_get_target_file(source_file=file, target_directory=target_directory,
                                           reference_keys=reference_keys, file_key=key, file_ext=ext, config=config))
    return file_model


def _get_target_file(source_file: str, target_directory: str, reference_keys: dict,
                     file_key: str, file_ext: str, config: dict) -> dict:
    if config[ConfigKeys.fill_gaps]:
        target_file = _get_next_gap_in_sequence(target_directory=target_directory,
                                                file_key=file_key, file_ext=file_ext,
                                                target_files=
                                                reference_keys[file_key] if file_key in reference_keys else [])
        if target_file is None:
            target_file = _get_next_file_in_sequence(target_directory=target_directory,
                                                     file_key=file_key, file_ext=file_ext,
                                                     target_files=
                                                     reference_keys[file_key] if file_key in reference_keys else [])
    else:
        target_file = _get_next_file_in_sequence(target_directory=target_directory,
                                                 file_key=file_key, file_ext=file_ext,
                                                 target_files=
                                                 reference_keys[file_key] if file_key in reference_keys else [])
    # Update reference dict for target_file so that it is accounted for in subsequent iterations
    _update_dict(target_file, reference_keys, file_key)
    return {
        DisplayKeys.source: source_file,
        DisplayKeys.target: target_file
    }


def _get_next_gap_in_sequence(target_directory: str, target_files: list, file_key: str, file_ext: str):
    for i in range(1, len(target_files)):
        target_file = os.path.join(target_directory, f"{file_key} - {i}{file_ext}")
        if target_file not in target_files:
            return target_file
    return None


def _get_next_file_in_sequence(target_directory: str, target_files: list, file_key: str, file_ext: str):
    curr_max = 0
    for file in target_files:
        _, file_name = os.path.split(file)
        file_name_tokens = file_name.split(DEFAULT_SPLITTER)
        string_index_value = ''.join(filter(lambda x: x.isdigit(), file_name_tokens[-1]))
        file_index = 1 if string_index_value == EMPTY_STR else int(string_index_value)
        if file_index > curr_max:
            curr_max = file_index
    return os.path.join(target_directory, f"{file_key} - {curr_max + 1}{file_ext}")


def _sort_files(files, config):
    def atoi(text):
        return int(text) if text.isdigit() else text

    def natural_keys(_tuple):
        """
        alist.sort(key=natural_keys) sorts in human order
        https://nedbatchelder.com/blog/200712/human_sorting.html
        """
        return [atoi(c) for c in re.split(r'(\d+)', _tuple[0])]

    # create a tuple of file and creation time
    tuples = []
    for file in files:
        os_info = os.stat(file)
        tuples.append((file, os_info.st_ctime, os_info.st_size))

    if config[ConfigKeys.sort_by] == SortBy.name:
        tuples.sort(key=natural_keys)
    elif config[ConfigKeys.sort_by] == SortBy.date:
        tuples.sort(key=lambda t: t[1])
    elif config[ConfigKeys.sort_by] == SortBy.size:
        tuples.sort(key=lambda t: t[2])

    for _tuple in tuples:
        yield _tuple[0]


def _create_destination_keymap(files, config):
    _dict = {}
    for file in files:
        if file == EMPTY_STR:
            continue
        key = _create_key(file, config, is_destination=True)
        _, file_name = os.path.split(file)
        if file_name.startswith(key):
            _update_dict(file, _dict, key)
    return _dict


def _update_dict(file, _dict, key):
    if _dict.__contains__(key):
        _dict[key].append(file)
    else:
        _dict[key] = [file]


def _create_key(file, config, is_destination=False):
    if ConfigKeys.is_version_2 in config:
        return _create_key_v2(file, config, is_destination)
    else:
        raise NotImplementedError("V1 is discontinued")


def _create_key_v2(file, config, is_destination=False):
    operation = config[ConfigKeys.operation]
    try:
        key_base = operation.get_key(file, config, is_destination=is_destination)
    except Exception:
        logger.exception("Something awful happened!")
        key_base = UNKNOWN_KEY

    if ConfigKeys.append_date in config:
        if config[ConfigKeys.append_date]:
            return f"{key_base}{DEFAULT_SPLITTER}{datetime.now().strftime('%Y-%m-%d')}"
        else:
            return f"{key_base}"
    else:
        return UNKNOWN_KEY


class RenameUIOperation(QObject):
    """
    All core file rename operations need to extend this class
    """
    merge_event = pyqtSignal(int)

    def __init__(self, name, description):
        super().__init__()
        self.name = name
        self.description = description

    def get_widget(self) -> QWidget:
        widget = QWidget()
        layout = self._get_layout()
        layout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(layout)
        return widget

    def is_ready(self) -> bool:
        """
        Returns true if the Operation has all the data needed to begin file rename operations
        """
        pass

    def get_key(self, file, config, is_destination=False) -> str:
        """
        Returns the key of the file with the given config.context
        Args:
            file: The full file path
            config: The config to use
            is_destination: True if the key is being extracted for a file in the destination, in which case the
            key may need to be extracted differently

        Returns: A key based on the config.context and file

        """
        self.validate_correct_operation(op_name=self.name, key_type=config[ConfigKeys.key_type])
        if is_destination:
            return self._get_destination_key(file, config)
        return self._get_source_key(file, config)

    def get_help(self):
        """
        Returns: Help associated with this rename operations
        """
        return f"<H2>{self.name}</H2><p>{self.description}</p>"

    def get_context(self) -> dict:
        """
        Returns: A dict with all the data needed for the Operation to change a file name
        """
        pass

    def show_help(self) -> str:
        """
        Returns: A formatted string with help details
        """
        pass

    def save_state(self):
        """
        Convenience function to enable file operations to save their state for next time.
        Note, states are not saved across sessions
        Returns: Nothing

        """
        pass

    def _get_layout(self) -> QBoxLayout:
        pass

    def _get_source_key(self, file_name, config) -> str:
        """
        Returns the key of the file with the given config.context
        Args:
            file_name: The filename
            config: The config to use
        Returns: A key based on the config.context and file

        """
        pass

    def _get_destination_key(self, file, config):
        """
        Extracts the destination key with the given config.context
        Args:
            file: The filename
            config: The config to use
        Returns: A key based on the config.context and file
        """
        context = config[ConfigKeys.context]
        file_splitter = context[CTX_FILE_SEPARATOR]
        _, file_name = os.path.split(file)
        idx = file_name.rfind(file_splitter)
        if idx >= 0:
            return file_name[:idx]
        else:
            logger.warning(f"Unable to find index in file name {file_name}. Returning {file_name} as key")
            return None

    def _emit_merge_event(self):
        self.merge_event.emit(0)

    @staticmethod
    def _none_or_empty(text):
        return text is None or text == EMPTY_STR

    @staticmethod
    def validate_correct_operation(op_name, key_type):
        if key_type != op_name:
            raise TypeError(f"{op_name} cannot create key for {key_type}")

    @staticmethod
    def _get_editable_combo(current_text=EMPTY_STR) -> QComboBox:
        combobox = QComboBox()
        combobox.setEditable(True)
        combobox.setInsertPolicy(QComboBox.InsertAtTop)
        combobox.setCurrentText(current_text)
        return combobox

    @staticmethod
    def _save_combo_current_text(combobox: QComboBox):
        combobox.blockSignals(True)
        combobox.addItem(combobox.currentText())
        combobox.blockSignals(False)


def get_file_operations() -> dict:
    """
    Returns a list of file operations avaialble to the user. This list is wrapped inside a method to allow
    a QApplication to be created before the file operations are called for
    Returns: a list of file operations

    """

    from FileWrangler.fileops.CompletelyReplace import CompletelyReplaceUIOperation
    from FileWrangler.fileops.Separator import SeparatorUIOperation
    from FileWrangler.fileops.PatternFinding import PatternExtractingUIOperation
    from FileWrangler.fileops.PathComponents import PathComponentsUIOperation
    operations = [
        CompletelyReplaceUIOperation(),
        SeparatorUIOperation(),
        PatternExtractingUIOperation(),
        PathComponentsUIOperation()
    ]
    return {x.name: x for x in operations}
