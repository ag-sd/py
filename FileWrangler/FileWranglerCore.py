import os
import re
from datetime import datetime
from enum import Enum

from CommonUtils import FileScanner

_UNKNOWN_KEY = "Unknown"
_DEFAULT_SPLITTER = " - "
_DEFAULT_REGEX = ".+?(?= - )"


class DisplayKeys(Enum):
    source = "source"
    target = "target"


class ConfigKeys(Enum):
    append_date = 0
    key_token_string = 1
    key_type = 2
    key_token_count = 4


class KeyType(Enum):
    regular_expression = 1
    separator = 2
    replacement = 3


class ActionKeys(Enum):
    copy = "Copy"
    move = "Move"


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
    for file in source_scanner.files:
        # Update reference dict for file
        key = _create_key(file, config)
        _update_dict(file, reference_keys, key)
        key = _create_key(file, config)
        _, ext = os.path.splitext(file)
        file_model.append({
            DisplayKeys.source: file,
            DisplayKeys.target: os.path.join(target_directory, f"{key} - {len(reference_keys[key])}{ext}")
        })
    return file_model


def _create_destination_keymap(files, config):
    _dict = {}
    for file in files:
        key = _create_key(file, config)
        _, file_name = os.path.split(file)
        if file_name.startswith(key):
            _update_dict(file, _dict, key)
    return _dict


def _update_dict(file, _dict, key):
    if _dict.__contains__(key):
        _dict[key].append(file)
    else:
        _dict[key] = [file]


def _create_key(file, config):
    _, file_name = os.path.split(file)

    if config[ConfigKeys.key_type] == KeyType.regular_expression:
        tokens = re.findall(config[ConfigKeys.key_token_string], file_name)
        splitter = _DEFAULT_SPLITTER
    elif config[ConfigKeys.key_type] == KeyType.separator:
        tokens = file_name.split(config[ConfigKeys.key_token_string])
        splitter = config[ConfigKeys.key_token_string]
    else:
        tokens = [config[ConfigKeys.key_token_string]]
        splitter = None

    if config[ConfigKeys.key_type] == KeyType.replacement:
        key_base = tokens[0]
    elif len(tokens) >= config[ConfigKeys.key_token_count]:
        key_base = splitter.join(tokens[:config[ConfigKeys.key_token_count]])
    else:
        return _UNKNOWN_KEY

    if ConfigKeys.append_date in config:
        if config[ConfigKeys.append_date]:
            return f"{key_base}{_DEFAULT_SPLITTER}{datetime.now().strftime('%Y-%m-%d')}"
        else:
            return key_base
    else:
        return _UNKNOWN_KEY