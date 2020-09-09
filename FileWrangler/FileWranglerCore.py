import os
import re
from datetime import datetime
from enum import Enum

from CommonUtils import FileScanner

_SPLITTER = " - "
_UNKNOWN_KEY = "Unknown"
_DEFAULT_REGEX = ".+?(?= - )"


class DisplayKeys(Enum):
    source = "source"
    target = "target"


class ConfigKeys(Enum):
    append_date = 0
    key_regex = 1


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
    # Find all unique keys in destination dir
    # for each source file:
    #   generate key
    #   if key exists in destination, update destination file count to destination value + 1
    #   add to list of files to return
    #

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
    tokens = re.search(config[ConfigKeys.key_regex], file_name)
    if tokens:
        token = tokens[0]
        if ConfigKeys.append_date in config and config[ConfigKeys.append_date]:
            token = f"{token}{_SPLITTER}{datetime.now().strftime('%Y-%m-%d')}"
        return token
    else:
        return _UNKNOWN_KEY


    # tokens = file_name.split(_SPLITTER)
    #
    # if len(tokens) > 1:
    #     token = tokens[0]
    #     if ConfigKeys.append_date in config and config[ConfigKeys.append_date]:
    #         token = f"{token}{_SPLITTER}{datetime.now().strftime('%Y-%m-%d')}"
    #     return token
    # else:
    #     return _UNKNOWN_KEY
