import sys
from functools import partial

from PyQt5 import QtCore
from PyQt5.QtCore import (pyqtSignal, QSize,
                          QUrl)
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QToolBar, \
    QAction, QFileDialog, QProgressBar

from CommonUtils import FileScanner, CommandExecutionFactory
from TransCoda.Encoda import EncodaCommand
from TransCoda.MainPanel import MainPanel
from TransCoda.TransCodaSettings import TransCodaSettings


class MainToolBar(QToolBar):
    button_pressed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.create_actions()
        self.setIconSize(QSize(48, 48))

    def create_actions(self):
        self.addAction(self.create_action(name="Add File", shortcut="Ctrl+O",
                                          tooltip="Add a single file to list",
                                          icon=QIcon.fromTheme("list-add")))
        self.addAction(self.create_action(name="Add Directory", shortcut="Ctrl+D",
                                          tooltip="Add an entire directory list",
                                          icon=QIcon.fromTheme("folder-new")))
        self.addAction(self.create_action(name="Clear", shortcut="Delete",
                                          tooltip="Clear all files",
                                          icon=QIcon.fromTheme("edit-clear")))
        self.addSeparator()
        self.addAction(self.create_action(name="Settings", shortcut="Ctrl+R",
                                          tooltip="Open the settings editor",
                                          icon=QIcon.fromTheme("preferences-system")))
        self.addAction(self.create_action(name="Start", shortcut="Ctrl+R",
                                          tooltip="Start encoding the files",
                                          icon=QIcon.fromTheme("media-playback-start")))
        self.addSeparator()
        self.addAction(self.create_action(name="Help", shortcut="F1",
                                          tooltip="View online help",
                                          icon=QIcon.fromTheme("help-contents")))
        self.addAction(self.create_action(name="About", shortcut="Ctrl+I",
                                          tooltip="About this application",
                                          icon=QIcon.fromTheme("help-about")))

    def create_action(self, name, shortcut=None, tooltip=None, icon=None):
        action = QAction(name, self)
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tooltip is not None:
            if shortcut is not None:
                tooltip = f"{tooltip} ({shortcut})"
            action.setToolTip(tooltip)
        action.triggered.connect(partial(self.raise_event, name))
        if icon is not None:
            action.setIcon(icon)
        return action

    def raise_event(self, event):
        self.button_pressed.emit(event)


class TransCodaApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.main_panel = MainPanel()
        self.tool_bar = MainToolBar()
        # self.status_bar = QStatusBar()
        self.progressbar = QProgressBar()
        self.executor = None
        self.init_ui()

    def init_ui(self):
        self.tool_bar.button_pressed.connect(self.toolbar_event)
        self.addToolBar(QtCore.Qt.LeftToolBarArea, self.tool_bar)
        # self.setStatusBar(self.status_bar)
        self.setCentralWidget(self.main_panel)
        self.statusBar().addPermanentWidget(self.progressbar)
        self.setMinimumSize(800, 600)
        self.setWindowTitle("Trans:Coda")
        self.show()

    def toolbar_event(self, event_name):
        if event_name == "Add File":
            file, _ = QFileDialog.getOpenFileUrl(caption="Select a File")
            if not file.isEmpty():
                self.main_panel.add_files([file])
        elif event_name == "Add Directory":
            _dir = QFileDialog.getExistingDirectoryUrl(caption="Select a directory")
            if not _dir.isEmpty():
                scanner = FileScanner([_dir], recurse=True, is_qfiles=True)
                files_to_add = []
                for file in scanner.files:
                    files_to_add.append(QUrl(f"file://{file}"))
                self.main_panel.add_files(files_to_add)
        elif event_name == "Settings":
            TransCodaSettings().exec()
        elif event_name == "Clear":
            self.main_panel.clear_table()
        elif event_name == "Start":
            if self.executor is not None and self.executor.is_running():
                self.executor.stop_scan()
                return
            else:
                runnables = []
                for _input, _output, _command in self.main_panel.generate_commands():
                    runnables.append(EncodaCommand(input_file=_input, output_file=_output, command=_command))

                self.progressbar.setValue(0)
                self.progressbar.setMaximum(len(runnables))
                self.main_panel.encoding_started()
                self.executor = CommandExecutionFactory(runnables)
                self.executor.result_event.connect(self.result_received)
                self.executor.finish_event.connect(self.jobs_complete)
                self.executor.start()

    def result_received(self, result):
        self.main_panel.update_item(result)
        self.progressbar.setValue(self.progressbar.value() + 1)

    def jobs_complete(self, all_results, time_taken):
        self.progressbar.setValue(self.progressbar.maximum())
        self.executor = None
        self.statusBar().showMessage(f"Processed {len(all_results)} files in {time_taken} seconds")


def main():
    app = QApplication(sys.argv)
    ex = TransCodaApp()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
