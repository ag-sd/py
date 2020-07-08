import datetime
import hashlib
import logging
import os
import subprocess
from os import path

from PyQt5.QtCore import QObject, pyqtSignal, QSettings, QThread, QThreadPool
from PyQt5.QtWidgets import QCheckBox, QRadioButton, QGroupBox, QWidget, QSplitter, QAction

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


def calculate_sha256_hash(file):
    block_size = 1048576  # (1MB) The size of each read from the file
    file_hash = hashlib.sha256()
    with open(file, 'rb') as f:
        file_bytes = f.read(block_size)
        while len(file_bytes) > 0:
            file_hash.update(file_bytes)
            file_bytes = f.read(block_size)
    return file_hash.hexdigest()


def human_readable_filesize(size, decimal_places=2):
    for unit in ['B', 'KiB', 'MiB', 'GiB', 'TiB']:
        if size < 1024.0:
            break
        size /= 1024.0
    return f"{size:.{decimal_places}f}{unit}"


def create_toolbar_action(tooltip, icon, func, text=""):
    action = QAction("")
    action.setToolTip(tooltip)
    action.setIcon(icon)
    action.setText(text)
    action.triggered.connect(func)
    return action


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
    def __init__(self, file_urls, recurse=False, supported_extensions=None, is_qfiles=True):
        super().__init__()
        if supported_extensions is not None:
            self.supported_extensions = [x.upper() for x in supported_extensions]
        else:
            self.supported_extensions = None
        self.recurse = recurse
        if is_qfiles:
            self.files, self.rejected_files = self._scan_q_files(file_urls, recurse)
        else:
            self.files, self.rejected_files = self._scan_p_files(file_urls, recurse)

    def _scan_p_files(self, file_urls, recurse):
        """
            Routine for finding all files in a directory
            :param file_urls: the **PYTHON STRING** paths to find files in
            :param recurse: Recurse into subdirectories
            :return: List of files found in the path sorted in descending order of file size
        """
        rejected_files = []
        dirs = []
        files = []
        for file in file_urls:
            if path.isdir(file):
                dirs.append(file)               # Save it if dir
            elif self.is_supported(file):
                files.append(file)              # Process it if a supported file
            else:
                rejected_files.append(file)     # Reject it if not a dir or supported file
        return self._walk(dirs, files, [], recurse)

    def _scan_q_files(self, file_urls, recurse):
        """
            Routine for finding all files in a directory
            :param file_urls: the **PyQT5 QFile** paths to find files in
            :param recurse: Recurse into subdirectories
            :return: List of files found in the path sorted in descending order of file size
        """
        dirs = []
        files = []
        for file in file_urls:
            if file.isLocalFile():
                local_file = file.toLocalFile()
                if os.path.isdir(local_file):
                    dirs.append(local_file)
                elif self.is_supported(local_file):
                    files.append(local_file)
        return self._walk(dirs, files, [], recurse)

    def _walk(self, dirs, files, rejects, recurse):
        while len(dirs) > 0:
            _dir = dirs.pop()
            for dirName, _, fileList in os.walk(_dir, topdown=True):
                for file in fileList:
                    if self.is_supported(file):
                        files.append(os.path.join(dirName, file))
                    else:
                        rejects.append(os.path.join(dirName, file))
                if not recurse:
                    break
        return set(files), set(rejects)

    def is_supported(self, file):
        if self.supported_extensions is not None:
            _, ext = os.path.splitext(file)
            return self.supported_extensions.__contains__(ext.upper())
        return True


class ProcessRunnerException(Exception):
    def __init__(self, cmd, exit_code, stdout, stderr):
        self.cmd = cmd
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.message = "`{0}` exited with status {1}\n\nSTDOUT:\n{2}\n\nSTDERR:\n{3}".format(
            self.cmd,
            exit_code,
            (stdout or b'').decode(),
            (stderr or b'').decode()
        )


class ProcessRunner(object):
    def __init__(self, command):
        self.command = command

    def run(self, stdout=None, stderr=None):
        process = subprocess.Popen(
            self.command,
            stdin=subprocess.PIPE,
            stdout=stdout,
            stderr=stderr,
            shell=True
        )
        out = process.communicate()

        if process.returncode != 0:
            raise ProcessRunnerException(self.command, process.returncode, out[0], out[1])

        return out


class CommandExecutionFactory(QThread):
    finish_event = pyqtSignal('PyQt_PyObject', int)
    result_event = pyqtSignal('PyQt_PyObject')

    def __init__(self, runnable_commands):
        super().__init__()
        self.runnables = runnable_commands
        self.runnable_count = len(self.runnables)
        self.completed = []
        self.thread_pool = QThreadPool()
        self.stop = False
        self.start_time = None

    def stop_scan(self):
        self.stop = True

    def run(self):
        self.start_time = datetime.datetime.now()
        self._start_work()

    def result_received(self, result):
        self.result_event.emit(result)
        self.completed.append(result)
        self._start_work()

    def is_running(self):
        return self.thread_pool.activeThreadCount() > 0

    def _start_work(self):
        if len(self.runnables) > 0:
            if self.stop:
                print("Stop has been received. Exiting now!")
                self.thread_pool.waitForDone()
                if len(self.completed) == self.runnable_count + len(self.runnables):
                    end_time = datetime.datetime.now()
                    self.finish_event.emit(self.completed, (end_time - self.start_time).total_seconds())
                return
            active_threads = self.thread_pool.activeThreadCount()
            available_threads = self.thread_pool.maxThreadCount() - active_threads
            for i in range(0, min(available_threads, len(self.runnables))):
                print("Dispatching to thread number " + str(i))
                runnable = self.runnables.pop()
                runnable.signals.result.connect(self.result_received)
                runnable.setAutoDelete(True)
                # Execute
                self.thread_pool.start(runnable)
        else:
            self.thread_pool.waitForDone()
            if len(self.completed) == self.runnable_count:
                end_time = datetime.datetime.now()
                self.finish_event.emit(self.completed, (end_time - self.start_time).total_seconds())
