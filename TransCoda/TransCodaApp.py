import sys

import psutil
from PyQt5 import QtCore
from PyQt5.QtCore import (pyqtSignal, QSize)
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QToolBar, \
    QFileDialog, QProgressBar, QMessageBox

import CommonUtils
from CommonUtils import CommandExecutionFactory
from TransCoda.Encoda import EncodaCommand, EncodaStatus
from TransCoda.MainPanel import MainPanel, OutputDirectoryNotSet, EncoderNotSelected
from TransCoda.TransCodaSettings import TransCodaSettings


class MainToolBar(QToolBar):
    button_pressed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.create_actions()
        self.setIconSize(QSize(48, 48))

    def create_actions(self):
        self.addAction(CommonUtils.create_action(name="Add File", shortcut="Ctrl+O",
                                                 tooltip="Add a single file to list",
                                                 func=self.raise_event, parent=self,
                                                 icon=QIcon.fromTheme("list-add")))
        self.addAction(CommonUtils.create_action(name="Add Directory", shortcut="Ctrl+D",
                                                 tooltip="Add an entire directory list",
                                                 func=self.raise_event, parent=self,
                                                 icon=QIcon.fromTheme("folder-new")))
        self.addAction(CommonUtils.create_action(name="Clear", shortcut="Delete",
                                                 tooltip="Clear all files",
                                                 func=self.raise_event, parent=self,
                                                 icon=QIcon.fromTheme("edit-clear")))
        self.addSeparator()
        self.addAction(CommonUtils.create_action(name="Settings", shortcut="Ctrl+R",
                                                 tooltip="Open the settings editor",
                                                 func=self.raise_event, parent=self,
                                                 icon=QIcon.fromTheme("preferences-system")))
        self.addAction(CommonUtils.create_action(name="Start", shortcut="Ctrl+R",
                                                 tooltip="Start encoding the files",
                                                 func=self.raise_event, parent=self,
                                                 icon=QIcon.fromTheme("media-playback-start")))
        self.addSeparator()
        self.addAction(CommonUtils.create_action(name="Help", shortcut="F1",
                                                 tooltip="View online help",
                                                 func=self.raise_event, parent=self,
                                                 icon=QIcon.fromTheme("help-contents")))
        self.addAction(CommonUtils.create_action(name="About", shortcut="Ctrl+I",
                                                 tooltip="About this application",
                                                 func=self.raise_event, parent=self,
                                                 icon=QIcon.fromTheme("help-about")))

    def raise_event(self, event):
        self.button_pressed.emit(event)


class TransCodaApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.main_panel = MainPanel()
        self.tool_bar = MainToolBar()
        self.progressbar = QProgressBar()
        self.executor = None
        self.init_ui()

    def init_ui(self):
        self.main_panel.files_changed_event.connect(self.files_changed_event)
        self.main_panel.menu_item_event.connect(self.menu_event)
        self.tool_bar.button_pressed.connect(self.toolbar_event)
        self.addToolBar(QtCore.Qt.LeftToolBarArea, self.tool_bar)
        self.setCentralWidget(self.main_panel)
        self.statusBar().addPermanentWidget(self.progressbar)
        self.setMinimumSize(800, 600)
        self.setWindowTitle("Trans:Coda")
        self.setWindowIcon(QIcon("resource/soundconverter.svg"))
        self.show()

    def toolbar_event(self, event_name):
        if event_name == "Add File":
            file, _ = QFileDialog.getOpenFileUrl(caption="Select a File")
            if not file.isEmpty():
                self.main_panel.add_files([file])
        elif event_name == "Add Directory":
            _dir = QFileDialog.getExistingDirectoryUrl(caption="Select a directory")
            if not _dir.isEmpty():
                self.main_panel.add_files([_dir])
        elif event_name == "Settings":
            TransCodaSettings().exec()
        elif event_name == "Clear":
            self.main_panel.clear_table()
        elif event_name == "Start":
            if self.executor is not None and self.executor.is_running():
                self.executor.stop_scan()
                self.statusBar().showMessage("Stop command issued. Waiting for threads to finish")
                return
            else:
                self.validate_and_start_encoding()

    def menu_event(self, event_name, item_index):
        if event_name == "Remove":
            self.main_panel.remove_files([item_index])
        elif event_name == "Encode":
            self.validate_and_start_encoding(run_index=item_index)
        elif event_name == EncodaStatus.SUCCESS.name:
            self.main_panel.update_item_status(item_index, EncodaStatus.SUCCESS)
        elif event_name == EncodaStatus.READY.name:
            self.main_panel.update_item_status(item_index, EncodaStatus.READY)
        # elif event_name == "Open":
        #     file = self.file_model.get_item(row, FileModelKeys.input_file_name)
        #     subprocess.run(["open", f"\"{file}\""], check=False, shell=True)

    def validate_and_start_encoding(self, run_index=None):
        runnables = []
        try:
            for index, (_input, _output, _command) in enumerate(self.main_panel.generate_commands()):
                if run_index and index != run_index:
                    continue
                runnable = EncodaCommand(input_file=_input, output_file=_output, command=_command)
                runnable.signals.result.connect(self.result_received_event)
                runnable.signals.status.connect(self.status_received_event)
                runnables.append(runnable)
        except OutputDirectoryNotSet:
            QMessageBox.critical(self, "Error! Output directory not selected",
                                 "Encoding cannot start because the output directory is not selected. "
                                 "You can select the output directory from Settings")
            self.statusBar().showMessage("Error! Output directory not selected")
            return
        except EncoderNotSelected:
            QMessageBox.critical(self, "Error! Encoder not selected",
                                 "Encoding cannot start because the output encoder is not selected. "
                                 "You can select the output encoder from Settings")
            self.statusBar().showMessage("Error! Encoder not selected")
            return

        if len(runnables) <= 0:
            self.statusBar().showMessage("Nothing to encode!")
            return

        self.progressbar.setValue(0)
        self.progressbar.setMaximum(len(runnables))
        self.main_panel.encoding_started(run_index)
        self.executor = CommandExecutionFactory(runnables)
        self.executor.finish_event.connect(self.jobs_complete_event)
        self.statusBar().showMessage(f"Dispatching {self.progressbar.maximum()} jobs for encoding")
        self.executor.start()

    def result_received_event(self, result):
        self.main_panel.update_item(result)
        self.progressbar.setValue(self.progressbar.value() + 1)
        self.update_status_bar()

    def status_received_event(self, input_file, total_time, completed_time):
        self.main_panel.update_item_percent_compete(input_file, total_time, completed_time)
        self.update_status_bar()

    def jobs_complete_event(self, all_results, time_taken):
        self.progressbar.setValue(self.progressbar.maximum())
        self.executor = None
        self.statusBar().showMessage(f"Processed {len(all_results)} files in {time_taken} seconds")

    def files_changed_event(self, files_added, count_of_files):
        if files_added:
            self.statusBar().showMessage(f"{count_of_files} supported files were added to encode list")
        else:
            self.statusBar().showMessage(f"{count_of_files} files were removed from encode list")

    def update_status_bar(self):
        cpu = psutil.cpu_percent()
        if cpu > 0:
            cpu = f"\tCPU: {cpu}%"
        else:
            cpu = ""
        self.statusBar().showMessage(f"{self.progressbar.value()} files processed so far, "
                                     f"{self.progressbar.maximum() - self.progressbar.value()} files remaining. {cpu}")


def main():
    app = QApplication(sys.argv)
    ex = TransCodaApp()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
