import logging
from os import path, walk, listdir

from PyQt5.QtWidgets import QWidget, QCheckBox, QRadioButton, QGroupBox

from CustomUI import FileChooser
from FileItem import FileItem
from Plugin import Plugin
from FileItemModel import FileItemModel


def _find_files(dir_path, model, supported_extensions, rejected_files, recurse=True):
    """
    Routine for finding all files in a directory
    :param dir_path: the path to find files in
    :param model: the model to insert data into
    :param recurse: Recurse into subdirectories
    :return: List of files found in the path sorted in descending order of file size
    """
    #   Check if path exists
    if not path.exists(dir_path):
        __logger.info(dir_path + " does not exist!")
        return model, rejected_files

    #   Check if it is a directory
    if not path.isdir(dir_path):
        __logger.info(dir_path + " is not a directory!")
        return model, rejected_files

    for root, dirs, files in walk(dir_path):
        for file_name in files:
            _add_supported_file_to_model(file_name, root, supported_extensions, model, rejected_files)
        if not recurse:
            break

    # return sorted(model, key=lambda x: x.file_size, reverse=False)
    return model, rejected_files


def _add_supported_file_to_model(file_name, _path, supported_extensions, model, rejected_files):
    #suffix, extension = path.splitext(file_name)
    #if supported_extensions.count(extension) > 0:
    entry = FileItem(file_name, _path, path.getsize(path.join(_path, file_name)))
    model.appendRow(entry)
    #else:
    #    rejected_files.append(file_name)


def create_model(file_urls, recurse, supported_extensions = []):
    item_model = FileItemModel()
    rejected_files = []
    for file in file_urls:
        if file.isLocalFile():
            local_file = file.toLocalFile()
            if path.isdir(local_file):
                _find_files(local_file, item_model, supported_extensions, rejected_files, recurse=recurse)
            else:
                # -------->print(local_file)
                _dir, file = path.split(file.path()[1:])
                _add_supported_file_to_model(file, _dir, supported_extensions, item_model, rejected_files)
    return item_model, rejected_files


def get_available_encoders(plugins_dir):
    plugins = []
    #   For each dir in plugin dir
    for plugin_dir in listdir(plugins_dir):
        plugin_dir = path.join(plugins_dir, plugin_dir)
        if path.isdir(plugin_dir):
            #   Check if it has a file...plugin.yaml
            plugin_config = path.join(plugin_dir, "plugin.yaml")
            if path.exists(plugin_config):
                print("Plugin Found!")
                #   Each plugin.yaml represents a plugin
                try:
                    plugins.append(Plugin(plugin_config))
                except ValueError as ve:
                    print(ve)

    return plugins


def load_settings(ui, settings):
    """
    https://stackoverflow.com/questions/23279125/python-pyqt4-functions-to-save-and-restore-ui-widget-values
    :param ui:
    :return:
    """
    # Main window settings
    current_files = settings.value("current_file_list")
    ui.current_files = current_files
    for obj in ui.findChildren(QWidget):
        name = obj.objectName()
        if name.startswith("stateful_"):
            value = settings.value(name)
            __logger.info("Loaded %s: %s" % (name, value))
            if value is None:
                continue
            if type(obj) is QCheckBox:
                obj.setChecked(value)
            elif type(obj) is QRadioButton or type(obj) is QGroupBox:
                obj.setChecked(bool(value))
            elif type(obj) is FileChooser:
                obj.setSelection(value)


def save_settings(ui, settings):
    """
    https://stackoverflow.com/questions/23279125/python-pyqt4-functions-to-save-and-restore-ui-widget-values
    :param ui:
    :return:
    """
    # Main window settings
    settings.setValue("current_file_list", ui.current_files)
    for obj in ui.findChildren(QWidget):
        name = obj.objectName()
        if name.startswith("stateful_"):
            if type(obj) is QCheckBox:
                value = obj.checkState()
            elif type(obj) is QRadioButton or type(obj) is QGroupBox:
                value = obj.isChecked()
            elif type(obj) is FileChooser:
                value = obj.getSelection()
            settings.setValue(name, value)
            __logger.info("Saved %s: %s" % (name, value))


def get_logger(appName):
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    log = logging.getLogger(appName)
    log.addHandler(ch)
    log.setLevel(logging.DEBUG)
    return log


__logger = get_logger('Autocode.Utils')

