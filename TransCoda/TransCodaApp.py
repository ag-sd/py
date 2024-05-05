import os
import sys
from datetime import datetime

import psutil
from PyQt5 import QtCore
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QProgressBar, QLabel, QPushButton, QMessageBox

import TransCoda
from TransCoda.core import TransCodaHistory
from TransCoda.core.Encoda import EncoderCommand, EncoderStatus
from TransCoda.core.MetaDataOperations import FileMetaDataExtractor
from TransCoda.ui import TransCodaSettings
from TransCoda.ui.Actions import MainToolBar, Action
from TransCoda.ui.MainPanel import MainPanel
from TransCoda.ui.TerminalView import TerminalView
from TransCoda.ui.TransCodaSettings import SettingsKeys
from common import CommonUtils
from common.CustomUI import QVLine


class TransCodaApp(QMainWindow):

    def __init__(self):
        super().__init__()
        self.main_panel = MainPanel()
        self.tool_bar = MainToolBar()
        self.progressbar = QProgressBar()
        self.message = QLabel("Ready")
        self.encoder = QLabel("Encoder")
        self.terminal_btn = QPushButton()
        self.terminal_view = TerminalView()
        self.executor = None
        self.timer = QTimer()
        self.init_ui()

    def init_ui(self):
        encoder_name = TransCodaSettings.get_encoder_name()
        self.main_panel.set_items(TransCodaSettings.get_encode_list())
        self.main_panel.files_changed_event.connect(self.files_changed_event)
        self.main_panel.menu_item_event.connect(self.action_event)
        self.tool_bar.set_encode_state(file_count=self.main_panel.row_count(),
                                       encoder_name=encoder_name,
                                       output_dir=TransCodaSettings.get_output_dir())
        self.tool_bar.button_pressed.connect(self.action_event)
        self.addToolBar(QtCore.Qt.LeftToolBarArea, self.tool_bar)
        self.setCentralWidget(self.main_panel)
        self.statusBar().addPermanentWidget(QVLine())
        if encoder_name:
            self.encoder.setText(TransCodaSettings.get_encoder_name())
        else:
            self.encoder.setText("No encoder selected.")
        self.terminal_btn.setIcon(TransCoda.theme.ico_terminal)
        self.terminal_btn.setFlat(True)
        self.terminal_btn.setToolTip("Show Encoder Logs")
        self.terminal_btn.clicked.connect(self.show_encode_logs)
        self.statusBar().addPermanentWidget(self.encoder, 0)
        self.statusBar().addPermanentWidget(QVLine())
        self.statusBar().addPermanentWidget(self.progressbar, 0)
        self.statusBar().addPermanentWidget(self.terminal_btn, 0)

        self.setMinimumSize(800, 600)
        self.setWindowTitle(TransCoda.__APP_NAME__)
        self.setWindowIcon(TransCoda.theme.ico_app_icon)
        self.timer.timeout.connect(self.timer_timeout_event)
        self.timer.setInterval(6000)
        self.timer.setSingleShot(True)
        TransCodaSettings.settings.settings_change_event.connect(self.settings_changed)
        TransCodaSettings.settings.load_ui(self, TransCoda.logger)
        self.show()
        # Executed after the show, where all dimensions are calculated
        self.progressbar.setFixedWidth(self.progressbar.width())
        self.progressbar.setVisible(False)

    def action_event(self, event, item_indices=None):
        if event == Action.ADD_FILE:
            file, _ = QFileDialog.getOpenFileUrl(caption="Select a File")
            if not file.isEmpty():
                self.files_changed_event(True, [file])
        elif event == Action.ADD_DIR:
            _dir = QFileDialog.getExistingDirectoryUrl(caption="Select a directory")
            if not _dir.isEmpty():
                self.files_changed_event(True, [_dir])
        elif event == Action.SETTINGS:
            TransCodaSettings.TransCodaSettings().exec()
        elif event == Action.DEL_ALL:
            self.main_panel.clear_table()
        elif event == Action.DEL_FILE:
            self.main_panel.remove_files(item_indices)
        elif event == Action.ENCODE:
            if self.executor is not None and self.executor.is_running():
                self.executor.stop_scan()
                self.statusBar().showMessage("Stop command issued. Waiting for threads to finish")
                return
            self.validate_and_start_encoding(run_indices=item_indices)
        elif event == Action.CHANGE_STATUS_SUCCESS:
            self.main_panel.update_item_status(item_indices, EncoderStatus.SUCCESS)
        elif event == Action.CHANGE_STATUS_READY:
            self.main_panel.update_item_status(item_indices, EncoderStatus.READY)
        elif event == Action.OPEN_FILE:
            self.open_paths_in_system_default(item_indices, "file")
        elif event == Action.OPEN_SOURCE:
            self.open_paths_in_system_default(item_indices, "file", func=os.path.dirname)
        elif event == Action.OPEN_DEST:
            self.open_paths_in_system_default(item_indices, "output_file", func=os.path.dirname)

        elif event == Action.ABOUT:
            with open(os.path.join(os.path.dirname(__file__), "resource/about.html"), 'r') as file:
                about_html = file.read()
            QMessageBox.about(self, TransCoda.__APP_NAME__, about_html.format(APP_NAME=TransCoda.__APP_NAME__,
                                                                              VERSION=TransCoda.__VERSION__,
                                                                              YEAR=datetime.now().year))

    def files_changed_event(self, is_added, files):
        if is_added:
            self.statusBar().showMessage("Scanning files please wait...")
            scanner = CommonUtils.FileScanner(files, recurse=True, is_qfiles=True)
            self.statusBar().showMessage(f"Loading files into {TransCoda.__APP_NAME__}")
            # Add files first
            total_added = self.main_panel.add_files(scanner.files)
            # Fetch and enrich with metadata
            batches = []
            for batch in CommonUtils.batch(list(scanner.files), batch_size=20):
                retriever = FileMetaDataExtractor(batch, batch_size=len(batch))
                retriever.signals.result.connect(self.result_received_event)
                batches.append(retriever)
            # UX
            self.begin_tasks(batches, f"Fetching meta-data for {total_added} files", total_added)
        self.tool_bar.set_encode_state(file_count=self.main_panel.row_count(),
                                       encoder_name=TransCodaSettings.get_encoder_name(),
                                       output_dir=TransCodaSettings.get_output_dir())

    def validate_and_start_encoding(self, run_indices=None):
        def create_runnable(_item):
            runnable = EncoderCommand(_item)
            runnable.signals.result.connect(self.result_received_event)
            runnable.signals.status.connect(self.status_received_event)
            runnable.signals.log_message.connect(self.terminal_view.log_message)
            return runnable

        runnables = []
        is_video = False
        if run_indices is not None:
            self.main_panel.update_item_status(run_indices, EncoderStatus.WAITING)
            for index in run_indices:
                item = self.main_panel.get_items(index)
                is_video = is_video or item.is_video()
                runnables.append(create_runnable(item))
        else:
            for index in range(0, self.main_panel.row_count()):
                item = self.main_panel.get_items(index)
                self.main_panel.update_item_status([index], EncoderStatus.WAITING)
                is_video = is_video or item.is_video()
                runnables.append(create_runnable(item))

        if len(runnables) <= 0:
            self.statusBar().showMessage("Nothing to encode!")
            return

        if TransCodaSettings.sort_by_size():
            runnables.sort(key=lambda x: x.file.file_size)
        self.tool_bar.encoding_started()
        if is_video and TransCodaSettings.is_single_thread_video():
            self.begin_tasks(runnables, f"Dispatching {len(runnables)} jobs for serial encoding", len(runnables),
                             threads=1)
        else:
            self.begin_tasks(runnables, f"Dispatching {len(runnables)} jobs for encoding", len(runnables),
                             threads=TransCodaSettings.get_max_threads())

    def begin_tasks(self, tasks, status_message, total_size, threads=TransCodaSettings.get_max_threads()):
        TransCoda.logger.info(status_message)
        self.progressbar.setVisible(True)
        self.progressbar.setValue(0)
        self.progressbar.setMaximum(total_size)
        self.executor = CommonUtils.CommandExecutionFactory(tasks,
                                                            logger=TransCoda.logger,
                                                            max_threads=threads)
        self.executor.finish_event.connect(self.jobs_complete_event)
        self.statusBar().showMessage(status_message)
        self.executor.start()

    def reset_timer(self):
        if self.executor is not None:
            if self.timer.isActive() and not self.executor.is_running():
                self.timer.stop()
        self.timer.start()

    def result_received_event(self, result):
        for result_item in result:
            if result_item.status in [EncoderStatus.SUCCESS, EncoderStatus.ERROR]:
                TransCodaHistory.set_history(
                    input_file=result_item.display_name(),
                    output_file=result_item.output_file,
                    start_time=result_item.encode_start_time,
                    end_time=result_item.encode_end_time,
                    input_size=result_item.file_size,
                    output_size=result_item.encode_output_size,
                    status=result_item.status,
                    encoder=result_item.encode_command,
                    message=result_item.encode_messages
                )
        self.main_panel.update_items(result)
        self.progressbar.setValue(self.progressbar.value() + len(result))
        self.update_status_bar()

    def status_received_event(self, status):
        self.main_panel.update_items([status])
        self.update_status_bar()

    def jobs_complete_event(self, all_results, time_taken):
        self.progressbar.setValue(self.progressbar.maximum())
        self.executor = None
        self.statusBar().showMessage(f"Processed {len(all_results)} files in {time_taken} seconds", msecs=400)
        self.set_window_title()
        self.tool_bar.encoding_finished(file_count=self.main_panel.row_count(),
                                        encoder_name=TransCodaSettings.get_encoder_name(),
                                        output_dir=TransCodaSettings.get_output_dir())
        self.reset_timer()

    def timer_timeout_event(self):
        self.progressbar.setValue(0)
        self.progressbar.setVisible(False)
        self.statusBar().clearMessage()

    def settings_changed(self, setting, _):
        valid_keys = {SettingsKeys.encoder_path}
        if setting in valid_keys:
            self.encoder.setText(TransCodaSettings.get_encoder_name())
        self.tool_bar.set_encode_state(file_count=self.main_panel.row_count(),
                                       encoder_name=TransCodaSettings.get_encoder_name(),
                                       output_dir=TransCodaSettings.get_output_dir())

    def update_status_bar(self):
        cpu = psutil.cpu_percent()
        if cpu > 0:
            cpu = f"\tCPU: {cpu}%"
        else:
            cpu = ""
        self.statusBar().showMessage(f"{self.progressbar.value()} files processed so far, "
                                     f"{self.progressbar.maximum() - self.progressbar.value()} files remaining. {cpu}")
        self.set_window_title(cpu=cpu, progress=self.progressbar.text())
        TransCoda.logger.info(self.statusBar().currentMessage())

    def set_window_title(self, cpu=None, progress=None):
        title = TransCoda.__APP_NAME__
        title += " " + cpu if cpu else ""
        title += " " + progress if progress else ""
        self.setWindowTitle(title)

    def show_encode_logs(self):
        self.terminal_view.show()

    def closeEvent(self, close_event) -> None:
        TransCoda.logger.info("Saving encode list...")
        TransCodaSettings.save_encode_list(self.main_panel.get_items())
        TransCoda.logger.info("Saving UI...")
        TransCodaSettings.settings.save_ui(self, TransCoda.logger)

    def open_paths_in_system_default(self, item_indices, attr, func=None):
        locations = set()
        for index in item_indices:
            item = self.main_panel.get_items(index)
            if hasattr(item, attr):
                if func:
                    locations.add(func(getattr(item, attr)))
                else:
                    locations.add(getattr(item, attr))

        if len(locations) > 3:
            choice = QMessageBox.question(self, "Are you Sure?",
                                          f"You are attempting to open several directories. "
                                          f"Are you sure you want to proceed?")
            if choice == QMessageBox.No:
                return
        for loc in locations:
            CommonUtils.open_file_item(loc)


def main():
    app = QApplication(sys.argv)
    _ = TransCodaApp()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
