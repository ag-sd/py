import logging
import os

from PyQt5.QtCore import QObject, pyqtSignal, QSettings
from PyQt5.QtWidgets import QCheckBox, QRadioButton, QGroupBox, QWidget, QSplitter

from common.CustomUI import FileChooserTextBox


def get_logger(app_name):
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - '
                                  '%(module)s:[%(funcName)s]:%(lineno)s - %(message)s')
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    log = logging.getLogger(app_name)
    log.addHandler(ch)
    log.setLevel(logging.DEBUG)
    return log


class AppSettings(QObject):

    stateful_prefix = "_stateful"
    """
    A class that can read and write application settings. The class can also fire events
    when a setting changes.
    App specific settings are stored as a dictionary that is saved as a byte stream
    This class is also capable of saving stateful UI's.
    UI settings may be partially human readable
    In order to save a UI, prefix each of its child widgets names with stateful_
    NOTE: The UI needs to have a object name if you are dealing with multiple saved UI's
    Currently supported stateful widgets are QCheckBox, QRadioButton, QGroupBox, FileChooser
    """
    settings_change_event = pyqtSignal(object, object)

    def __init__(self, app_name, default_settings):
        super().__init__()
        self._app_settings = QSettings("github.com/ag-sd", app_name)
        self._config = self._app_settings.value("app_settings")
        if self._config is None:
            self._config = default_settings

    def apply_setting(self, key, value):
        """
        Save an internal setting and fire an event
        :param key: the setting key
        :param value: the value to set
        :return:
        """
        self._config[key] = value
        self._app_settings.setValue("app_settings", self._config)
        self.settings_change_event.emit(key, value)

    def save_ui(self, ui, logger=None, ignore_children=False):
        """
        https://stackoverflow.com/questions/23279125/python-pyqt4-functions-to-save-and-restore-ui-widget-values
        :param ignore_children: If set, the children of the UI will not be saved
        :param ui       : The QWidget to save
        :param logger   : Optional, if provided will log each save attempt of a stateful widget
        :return:
        """
        path = ui.objectName()
        self._app_settings.setValue(f"{path}/geometry", ui.saveGeometry())
        if ignore_children:
            return

        for obj in ui.findChildren(QWidget):
            name = obj.objectName()
            if name.startswith(AppSettings.stateful_prefix):
                value = None
                key = f"{path}/{name}"
                if isinstance(obj, QCheckBox):
                    value = obj.checkState()
                elif isinstance(obj, QRadioButton) or isinstance(obj, QGroupBox):
                    value = obj.isChecked()
                elif isinstance(obj, FileChooserTextBox):
                    value = obj.getSelection()
                elif isinstance(obj, QSplitter):
                    value = obj.saveState()

                if value is not None:
                    self._app_settings.setValue(key, value)
                    if logger is not None:
                        logger.info(f"Saved {key}: {value}")
                else:
                    if logger is not None:
                        logger.debug(f"{key} could not be saved")

    def load_ui(self, ui, logger=None, ignore_children=False):
        """
        https://stackoverflow.com/questions/23279125/python-pyqt4-functions-to-save-and-restore-ui-widget-values
        :param ignore_children: If set, the children of the UI will not be loaded
        :param ui       : The QWidget to save
        :param logger   : Optional, if provided will log each load attempt of a stateful widget
        :return:
        """
        path = ui.objectName()
        geometry = self._app_settings.value(f"{path}/geometry")
        if geometry is None:
            if logger is not None:
                logger.warn(f"{path} not found in settings")
            return False
        else:
            ui.restoreGeometry(self._app_settings.value(f"{path}/geometry"))
        if ignore_children:
            return True

        for obj in ui.findChildren(QWidget):
            name = obj.objectName()
            if name.startswith(AppSettings.stateful_prefix):
                key = f"{path}/{name}"
                value = self._app_settings.value(key)
                if logger is not None:
                    logger.info(f"Loaded {key}: {value}")
                if value is None:
                    continue
                if isinstance(obj, QCheckBox):
                    obj.setChecked(value)
                elif isinstance(obj, QRadioButton) or isinstance(obj, QGroupBox):
                    obj.setChecked(bool(value))
                elif isinstance(obj, FileChooserTextBox):
                    obj.setSelection(value)
                elif isinstance(obj, QSplitter):
                    obj.restoreState(value)
        return True

    def get_setting(self, key, default=None):
        if self._config.__contains__(key):
            return self._config[key]
        return default


class FileScanner:
    """
    A class to scan a collection of Qfile file URL's which may represent files or directories
    and create a list of files in this collection
    """
    def __init__(self, file_urls, recurse=False, supported_extensions=None):
        super().__init__()
        self.supported_extensions = supported_extensions
        self.recurse = recurse
        self.files = self._scan_files(file_urls, recurse)

    def _scan_files(self, file_urls, recurse):
        dirs = []
        files = []
        for file in file_urls:
            if file.isLocalFile():
                local_file = file.toLocalFile()
                if os.path.isdir(local_file):
                        dirs.append(local_file)
                elif self.is_supported(local_file):
                    files.append(local_file)

        while len(dirs) > 0:
            _dir = dirs.pop()
            for dirName, _, fileList in os.walk(_dir, topdown=True):
                for file in fileList:
                    if self.is_supported(file):
                        files.append(os.path.join(dirName, file))
                if not recurse:
                    break

        return files

    def is_supported(self, file):
        if self.supported_extensions is not None:
            _, ext = os.path.splitext(file)
            return self.supported_extensions.__contains__(ext.upper())
        return True

