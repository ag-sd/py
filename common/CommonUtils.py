import datetime
import hashlib
import logging
import mimetypes
import os
import subprocess
from functools import partial
from os import path

from PyQt5.QtCore import QObject, pyqtSignal, QSettings, QThread, QThreadPool, QRunnable, QTimer, QCoreApplication
from PyQt5.QtWidgets import QCheckBox, QRadioButton, QGroupBox, QWidget, QSplitter, QAction

from common.CustomUI import FileChooserTextBox


def batch(iterable, batch_size=10):
    iterable = list(iterable)
    total_size = len(iterable)
    for index in range(0, total_size, batch_size):
        yield iterable[index:min(index + batch_size, total_size)]


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
    size = float(size)
    for unit in ['B', 'KiB', 'MiB', 'GiB', 'TiB']:
        if size < 1024.0:
            break
        size /= 1024.0
    return f"{size:.{decimal_places}f}{unit}"


def from_human_readable_filesize(text):
    lookup = {
        "B": 1,
        "KiB": 1024.0,
        'MiB': 1024.0 * 1024.0,
        'GiB': 1024.0 * 1024.0 * 1024.0,
        'TiB': 1024.0 * 1024.0 * 1024.0 * 1024.0
    }
    if type(text) != str:
        return text
    key = text[-3:]
    if key in lookup:
        return float(text[:-3]) * lookup[key]
    elif key[-1] in lookup:
        return float(text[:-1])
    else:
        return None


def open_file_item(file_item):
    from sys import platform
    if platform == "linux" or platform == "linux2":
        subprocess.Popen(["xdg-open", file_item])
    elif platform == "darwin":
        subprocess.call(['open', file_item])
    elif platform == "win32":
        subprocess.Popen(["explorer", "/select,", file_item])


def human_readable_time(seconds):
    seconds = int(float(seconds))
    _hrs = 0
    _min = 0
    _sec = 0
    _min, _sec = divmod(seconds, 60)
    _hrs, _min = divmod(_min, 60)
    return f"{_hrs:02}:{_min:02}:{_sec:02}"


def create_toolbar_action(tooltip, icon, func, text=""):
    action = QAction("")
    action.setToolTip(tooltip)
    action.setIcon(icon)
    action.setText(text)
    action.triggered.connect(func)
    return action


def create_action(parent, name, func=None, shortcut=None, tooltip=None, icon=None, checked=None):
    action = QAction(name, parent)
    if shortcut is not None:
        action.setShortcut(shortcut)
    if tooltip is not None:
        if shortcut is not None:
            tooltip = f"{tooltip} ({shortcut})"
        action.setToolTip(tooltip)
    if func:
        action.triggered.connect(partial(func, name))
    if icon is not None:
        action.setIcon(icon)
    if checked is not None:
        action.setCheckable(True)
        action.setChecked(checked)
    return action


class PausableTimer(QTimer):
    def __init__(self):
        super().__init__()
        self._is_paused = False

    def pause(self):
        self.stop()
        self._is_paused = True

    def resume(self):
        self.start()
        self._is_paused = False

    def isPaused(self):
        return self._is_paused


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
    def __init__(self, file_urls, recurse=False, supported_extensions=None, is_qfiles=True, partial_mimetypes_list=None):
        super().__init__()
        self.supported_extensions = self._get_extensions(supported_extensions, partial_mimetypes_list)
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
        return self._scan_files(file_urls, recurse, None)

    def _scan_q_files(self, file_urls, recurse):
        """
            Routine for finding all files in a directory
            :param file_urls: the **PyQT5 QFile** paths to find files in
            :param recurse: Recurse into subdirectories
            :return: List of files found in the path sorted in descending order of file size
        """
        def qfile_to_file(qfile):
            if qfile.isLocalFile():
                return qfile.toLocalFile()
            else:
                return None
        return self._scan_files(file_urls, recurse, qfile_to_file)

    def _scan_files(self, file_urls, recurse, normalizing_function=None):
        """
            Routine for finding all files in a directory
            :param file_urls: the paths to find files in
            :param recurse: Recurse into subdirectories
            :param normalizing_function used to convert the file_url from any non standard format to a string
            :return: List of files found in the path sorted in descending order of file size
        """
        rejected_files = []
        dirs = []
        files = []
        for file in file_urls:
            if normalizing_function is None:
                normalized_file = file
            else:
                normalized_file = normalizing_function(file)
            if normalized_file is None:
                rejected_files.append(normalized_file)  # Reject it if cannot be normalized
            elif path.isdir(normalized_file):
                dirs.append(normalized_file)            # Save it if dir
            elif self.is_supported(normalized_file):
                files.append(normalized_file)           # Process it if a supported file
            else:
                rejected_files.append(normalized_file)  # Reject it if not a dir or supported file
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

    @staticmethod
    def _get_extensions(supported_extensions, partial_mimetypes_list):
        extensions = set()
        if partial_mimetypes_list is not None:
            db = mimetypes.MimeTypes()
            for partial_mime_type in partial_mimetypes_list:
                partial_mime_type = partial_mime_type.upper()
                for _map in db.types_map_inv:
                    for key, value in _map.items():
                        if partial_mime_type in key.upper():
                            for ext in value:
                                extensions.add(ext.upper())
        if supported_extensions is not None:
            for x in supported_extensions:
                extensions.add(x.upper())
        if len(extensions) == 0:
            return None
        return extensions


class ProcessRunnerException(Exception):
    def __init__(self, cmd, exit_code, stdout, stderr):
        self.cmd = cmd
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.message = f"`{self.cmd}` exited with status {exit_code}" \
                       f"\n\nSTDOUT:\n{(stdout or b'').decode()}" \
                       f"\n\nSTDERR:\n{(stderr or b'').decode()}"


class CommandSignals(QObject):
    result = pyqtSignal('PyQt_PyObject')
    __complete__ = pyqtSignal('PyQt_PyObject')
    status = pyqtSignal('PyQt_PyObject')
    log_message = pyqtSignal('PyQt_PyObject')


class Command(QRunnable):
    def __init__(self):
        super().__init__()
        self.signals = CommandSignals()
        self.time_taken_seconds = None

    def run(self):
        start_time = datetime.datetime.now()
        self.do_work()
        end_time = datetime.datetime.now()
        self.time_taken_seconds = (end_time - start_time).total_seconds()
        self.signals.__complete__.emit(self.time_taken_seconds)

    def do_work(self):
        pass

    def work_size(self):
        pass


class CommandExecutionFactory(QThread):
    finish_event = pyqtSignal('PyQt_PyObject', int)
    result_event = pyqtSignal('PyQt_PyObject')

    def __init__(self, runnable_commands, logger=None, max_threads=None):
        super().__init__()
        self.pending_jobs = runnable_commands
        self.total_jobs = len(self.pending_jobs)
        self.completed = []
        self.thread_pool = QThreadPool()
        self.stop = False
        self.logger = logger
        if max_threads:
            self.max_threads = min(max_threads, self.thread_pool.maxThreadCount())
        else:
            self.max_threads = self.thread_pool.maxThreadCount()

        self.log(f"Multi-threading with maximum of {self.max_threads} threads")

    def add_task(self, task):
        self.pending_jobs.append(task)
        self.total_jobs += 1
        self.run()

    def get_max_threads(self):
        return self.max_threads

    def get_active_thread_count(self):
        return self.thread_pool.activeThreadCount()

    def stop_scan(self):
        self.stop = True

    def run(self):
        self.do_work()

    def thread_complete(self, result):
        self.completed.append(result)
        self.do_work()

    def is_running(self):
        return self.thread_pool.activeThreadCount() > 0

    def do_work(self):
        if len(self.pending_jobs) > 0:
            if self.stop:
                self.log(f"Stop has been received. Waiting for threads to finish before exiting... {self.check_thread()}")
                self.thread_pool.waitForDone()
                self.log(f"Waiting for {self.total_jobs - len(self.pending_jobs) - len(self.completed)} "
                         f"threads to finish {self.check_thread()}")
                if (self.total_jobs - len(self.pending_jobs) - len(self.completed)) == 0:
                    self.finish_event.emit(self.completed, sum(self.completed))
                self.check_thread()
                return
            active_threads = self.thread_pool.activeThreadCount()
            available_threads = self.max_threads - active_threads
            for i in range(0, min(available_threads, len(self.pending_jobs))):
                self.log(f"Dispatching thread on empty slot... {self.check_thread()}")
                runnable = self.pending_jobs.pop()
                runnable.signals.__complete__.connect(self.thread_complete)
                runnable.setAutoDelete(True)
                # Execute
                self.thread_pool.start(runnable)
        else:
            self.log(f"Waiting for threads to finish {self.check_thread()}")
            if len(self.completed) == self.total_jobs:
                total_time = sum(self.completed)
                self.log(f"Done. Total work completed in...{total_time} {self.check_thread()}")
                self.finish_event.emit(self.completed, total_time)

    def check_thread(self):
        # https://stackoverflow.com/questions/58511891/qthreadcreate-running-on-ui-thread
        if QCoreApplication.instance().thread() == self.currentThread():
            return "UI Thread in use!!!"
        else:
            return "Worker thread in use"

    def log(self, message):
        if self.logger:
            self.logger.info(message)
        else:
            print(f"No Logger Set!!: {message}")

