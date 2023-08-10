from datetime import datetime
import sys

from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableView, QProgressBar, QMessageBox

import CommonUtils
import MediaLib
from MediaLib.runtime.library import LibraryManagement
from MediaLib.runtime.library.LibraryManagement import Task, TaskStatus
from MediaLib.ui.LibraryActions import MediaLibToolbar, Action


class TaskManager(QObject):
    task_finish_event = pyqtSignal('PyQt_PyObject', int)

    class Job(CommonUtils.Command):
        def __init__(self, task_id, function, *args):
            super().__init__()
            self.function = function
            self.args = args
            self.task_id = task_id

        def work_size(self):
            return 1

        def do_work(self):
            self.function(*self.args)
            self.signals.result.emit(self.task_id)

    def __init__(self):
        super(TaskManager, self).__init__()
        self._executor = CommonUtils.CommandExecutionFactory(runnable_commands=[], logger=MediaLib.logger)
        self._task_manager = {}
        self._completed = []
        self._job_counter = 0

    def run_task(self, function, *args):
        self._job_counter += 1
        task = Task(task_id=f"{datetime.now().strftime('%Y-%m-%d')}:{self._job_counter}:{function.__name__}",
                    status=TaskStatus.Created)
        command = TaskManager.Job(task.task_id, function, *args, task)
        command.signals.result.connect(self.complete)
        self._task_manager[task.task_id] = (task, command)
        self._executor.add_task(command)

    def complete(self, task_id):
        task, cmd = self._task_manager.pop(task_id)
        MediaLib.logger.info(f"Task completed - {task_id} in {cmd.time_taken_seconds}")
        LibraryManagement.save_task(task)
        self._completed.append(task)
        self.task_finish_event.emit(task, cmd.time_taken_seconds)


class MediaLibApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.tool_bar = MediaLibToolbar()
        self.tool_bar.library_action.connect(self.library_event)
        self.progressbar = QProgressBar()
        self.task_manager = TaskManager()
        self.library = None
        self._init_ui()

    def _init_ui(self):
        MediaLib.logger.debug("Initializing UI")
        self.addToolBar(QtCore.Qt.TopToolBarArea, self.tool_bar)
        self.addToolBar(QtCore.Qt.LeftToolBarArea, MediaLibToolbar())

        self.statusBar().addPermanentWidget(self.progressbar, 0)

        self.setCentralWidget(QTableView())
        self.setMinimumSize(800, 600)
        self.setWindowTitle(MediaLib.__APP_NAME__)
        self.show()
        MediaLib.logger.debug("Initializing UI - Completed")

    def library_event(self, action, action_data):
        match action:
            case Action.Add:
                self.library = action_data
                self.task_manager.run_task(LibraryManagement.create_library, self.library)
            case Action.Refresh:
                self.library = action_data
                self.task_manager.run_task(LibraryManagement.refresh_library, self.library)
            case Action.Delete:
                choice = QMessageBox.question(self, "Are you Sure?",
                                              f"Once deleted, the library is not recoverable. "
                                              f"This operation cannot be undone."
                                              f"Are you sure you want to proceed?")
                if choice == QMessageBox.No:
                    return
                self.task_manager.run_task(LibraryManagement.delete_library, action_data)
            case Action.Select:
                self.library = action_data
                self.statusBar().showMessage(f"Now showing {action_data.name}")
            case Action.Search:
                MediaLib.logger.debug(f"Searching for {action_data}")
            case _:
                MediaLib.logger.error(f"Unrecognized library event {action} for {action_data}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MediaLibApp()
    sys.exit(app.exec_())
