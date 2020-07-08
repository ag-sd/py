import os
import sys
from builtins import staticmethod

import psutil
from PyQt5 import QtCore
from PyQt5.QtCore import (pyqtSignal, QSize, QUrl)
from PyQt5.QtGui import QIcon, QTextCursor, QFontDatabase
from PyQt5.QtWidgets import QApplication, QMainWindow, QToolBar, \
    QFileDialog, QProgressBar, QMessageBox, QLabel, QPushButton, QDialog, QTextEdit, QComboBox, \
    QVBoxLayout

import CommonUtils
import TransCoda
from CustomUI import QVLine
from TransCoda import MediaMetaData, TransCodaSettings
from TransCoda.Encoda import EncodaStatus, EncodaCommand
from TransCoda.MainPanel import MainPanel, OutputDirectoryNotSet, EncoderNotSelected, ItemKeys
from TransCoda.MediaMetaData import MetaDataFields
from TransCoda.ProcessRunners import HandbrakeProcessRunner
from TransCoda.TransCodaSettings import SettingsKeys


class MetadataRetriever(CommonUtils.Command):
    def __init__(self, input_files, batch_size=15):
        self.files = input_files
        self.batch_size = batch_size
        super().__init__()

    def do_work(self):
        batch = []
        for file in self.files:
            metadata = MediaMetaData.get_metadata(file)
            if not metadata:
                continue
            item = {
                ItemKeys.input_file_name: file,
                ItemKeys.input_bitrate: metadata[MetaDataFields.bit_rate],
                ItemKeys.input_duration: metadata[MetaDataFields.duration],
                ItemKeys.input_encoder: metadata[MetaDataFields.codec_long_name],
                ItemKeys.input_file_size: metadata[MetaDataFields.size],
                ItemKeys.sample_rate: metadata[MetaDataFields.sample_rate],
                ItemKeys.channels: metadata[MetaDataFields.channels],
                ItemKeys.status: EncodaStatus.READY
            }
            self.add_element(item, ItemKeys.artist, metadata, MetaDataFields.artist)
            self.add_element(item, ItemKeys.album_artist, metadata, MetaDataFields.album_artist)
            self.add_element(item, ItemKeys.title, metadata, MetaDataFields.title)
            self.add_element(item, ItemKeys.album, metadata, MetaDataFields.album)
            self.add_element(item, ItemKeys.track, metadata, MetaDataFields.track)
            self.add_element(item, ItemKeys.genre, metadata, MetaDataFields.genre)
            batch.append(item)
            if len(batch) >= self.batch_size:
                self.signals.result.emit(batch)
                batch = []
        if len(batch):
            self.signals.result.emit(batch)

    @staticmethod
    def add_element(_dict, item_key, metadata, meta_key):
        if meta_key in metadata:
            _dict[item_key] = metadata[meta_key]


class MainToolBar(QToolBar):
    button_pressed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setIconSize(QSize(48, 48))
        self.encode_ = CommonUtils.create_action(name="Start", shortcut="Ctrl+R",
                                                 tooltip="Start encoding the files",
                                                 func=self.raise_event, parent=self,
                                                 icon=QIcon.fromTheme("media-playback-start"))
        self.encode_.triggered.connect(self.encode_click)
        self.create_actions()

    def create_actions(self):
        self.addAction(CommonUtils.create_action(name="Add File", shortcut="Ctrl+O",
                                                 tooltip="Add a single file to list",
                                                 func=self.raise_event, parent=self,
                                                 icon=QIcon.fromTheme("list-add")))
        self.addAction(CommonUtils.create_action(name="Add Directory", shortcut="Ctrl+D",
                                                 tooltip="Add an entire directory list",
                                                 func=self.raise_event, parent=self,
                                                 icon=QIcon.fromTheme("folder-new")))
        self.addAction(CommonUtils.create_action(name="Clear", shortcut="Shift+Delete",
                                                 tooltip="Clear all files",
                                                 func=self.raise_event, parent=self,
                                                 icon=QIcon.fromTheme("edit-clear")))
        self.addSeparator()
        self.addAction(CommonUtils.create_action(name="Settings", shortcut="Ctrl+R",
                                                 tooltip="Open the settings editor",
                                                 func=self.raise_event, parent=self,
                                                 icon=QIcon.fromTheme("preferences-system")))
        self.addAction(self.encode_)
        self.addSeparator()
        self.addAction(CommonUtils.create_action(name="Help", shortcut="F1",
                                                 tooltip="View online help",
                                                 func=self.raise_event, parent=self,
                                                 icon=QIcon.fromTheme("help-contents")))
        self.addAction(CommonUtils.create_action(name="About", shortcut="Ctrl+I",
                                                 tooltip="About this application",
                                                 func=self.raise_event, parent=self,
                                                 icon=QIcon.fromTheme("help-about")))

    def encode_click(self, event):
        if self.encode_.text() == "Start":
            self.encode_.setIcon(QIcon.fromTheme("media-playback-stop"))
            self.encode_.setText("Stop")
            self.encode_.setToolTip("Wait for all files in progress to complete and Stop")
        else:
            self.encode_.setIcon(QIcon.fromTheme("media-playback-start"))
            self.encode_.setText("Start")
            self.encode_.setToolTip("Start encoding the files")

    def raise_event(self, event):
        self.button_pressed.emit(event)


class TerminalView(QDialog):
    def __init__(self):
        super().__init__()
        self.file_selector = QComboBox()
        self.text_box = QTextEdit()
        self.logs = {}
        self.init_ui()

    def init_ui(self):
        self.text_box.setFont(QFontDatabase.systemFont(QFontDatabase.FixedFont))
        self.text_box.setStyleSheet("QTextEdit{background: back; color: grey; font-size: 11.5px;}")
        self.file_selector.currentTextChanged.connect(self.file_selector_changed)
        layout = QVBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        layout.addWidget(self.file_selector)
        layout.addWidget(self.text_box)
        self.setLayout(layout)
        self.setModal(False)
        self.setMinimumSize(800, 450)

    def log_message(self, message):
        _file = message['file']
        _message = self.create_message(message['time'], message['message'])
        if _file in self.logs:
            self.logs[_file].append(_message)
        else:
            self.logs[_file] = [_message]
            self.file_selector.addItem(_file)

        if self.file_selector.currentText() == _file:
            self.text_box.moveCursor(QTextCursor.End)
            self.text_box.insertPlainText(_message)
            self.text_box.moveCursor(QTextCursor.End)

    def file_selector_changed(self):
        self.text_box.clear()
        self.text_box.insertPlainText("".join(self.logs[self.file_selector.currentText()]))

    @staticmethod
    def create_message(time, message):
        return f"{time}:{message}"


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
        self.init_ui()

    def init_ui(self):
        self.main_panel.set_items(TransCodaSettings.get_encode_list())
        self.main_panel.files_changed_event.connect(self.files_changed_event)
        self.main_panel.menu_item_event.connect(self.menu_event)
        self.tool_bar.button_pressed.connect(self.toolbar_event)
        self.addToolBar(QtCore.Qt.LeftToolBarArea, self.tool_bar)
        self.setCentralWidget(self.main_panel)
        self.statusBar().addPermanentWidget(QVLine())
        encoder_name = TransCodaSettings.get_encoder_name()
        if encoder_name:
            self.encoder.setText(TransCodaSettings.get_encoder_name())
        else:
            self.encoder.setText("No encoder selected.")
        self.terminal_btn.setIcon(QIcon.fromTheme("utilities-terminal"))
        self.terminal_btn.setFlat(True)
        self.terminal_btn.setToolTip("Show Encoder Logs")
        self.terminal_btn.clicked.connect(self.show_encode_logs)
        self.statusBar().addPermanentWidget(self.encoder, 0)
        self.statusBar().addPermanentWidget(QVLine())
        self.statusBar().addPermanentWidget(self.progressbar, 0)
        self.statusBar().addPermanentWidget(self.terminal_btn, 0)

        self.setMinimumSize(800, 600)
        self.setWindowTitle(TransCoda.__APP_NAME__)
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), "resource/soundconverter.svg")))
        TransCodaSettings.settings.settings_change_event.connect(self.settings_changed)
        self.show()
        # Executed after the show, where all dimensions are calculated
        self.progressbar.setFixedWidth(self.progressbar.width())

    def do_test(self):
        command = "HandBrakeCLI -i /mnt/Stuff/testing/video/file_example_MP4_480_1_5MG.mp4 -o /mnt/Stuff/testing/video/file_example_MP4_480_1_5MG_ENC.mp4 -e x264"
        runnables = [HandbrakeProcessRunner("/mnt/Stuff/testing/video/file_example_MP4_480_1_5MG.mp4", command)]
        self.progressbar.setValue(0)
        self.progressbar.setMaximum(len(runnables))
        self.executor = CommonUtils.CommandExecutionFactory(runnables,
                                                            logger=TransCoda.logger,
                                                            max_threads=TransCodaSettings.get_max_threads())
        self.executor.finish_event.connect(self.jobs_complete_event)
        self.statusBar().showMessage(f"Dispatching {self.progressbar.maximum()} jobs for encoding")
        self.executor.start()

    def toolbar_event(self, event_name):
        if event_name == "Add File":
            file, _ = QFileDialog.getOpenFileUrl(caption="Select a File")
            if not file.isEmpty():
                self.files_changed_event(True, [file])
        elif event_name == "Add Directory":
            _dir = QFileDialog.getExistingDirectoryUrl(caption="Select a directory")
            if not _dir.isEmpty():
                self.files_changed_event(True, [_dir])
        elif event_name == "Settings":
            TransCodaSettings.TransCodaSettings().exec()
        elif event_name == "Clear":
            self.main_panel.clear_table()
            TransCodaSettings.save_encode_list(self.main_panel.get_items())
        elif event_name == "Start":
            if self.executor is not None and self.executor.is_running():
                self.executor.stop_scan()
                self.statusBar().showMessage("Stop command issued. Waiting for threads to finish")
                return
            self.validate_and_start_encoding()

    def menu_event(self, event_name, item_indices):
        if event_name == "Remove":
            self.main_panel.remove_files(item_indices)
            TransCodaSettings.save_encode_list(self.main_panel.get_items())
        elif event_name == "Encode":
            self.validate_and_start_encoding(run_indices=item_indices)
        elif event_name == EncodaStatus.SUCCESS.name:
            self.main_panel.update_item_status(item_indices, EncodaStatus.SUCCESS)
            TransCodaSettings.save_encode_list(self.main_panel.get_items())
        elif event_name == EncodaStatus.READY.name:
            self.main_panel.update_item_status(item_indices, EncodaStatus.READY)
            TransCodaSettings.save_encode_list(self.main_panel.get_items())
        elif event_name == "Clear All":
            self.main_panel.clear_table()
            TransCodaSettings.save_encode_list(self.main_panel.get_items())
        # elif event_name == "Open":
        #     file = self.file_model.get_item(row, FileModelKeys.input_file_name)
        #     subprocess.run(["open", f"\"{file}\""], check=False, shell=True)

    def validate_and_start_encoding(self, run_indices=None):
        runnables = []
        try:
            for index, file_item in enumerate(self.main_panel.get_items(item_type=ItemKeys.input_file_name)):
                if run_indices and not run_indices.__contains__(index):
                    continue
                runnable = EncodaCommand(file_item)
                runnable.signals.result.connect(self.result_received_event)
                runnable.signals.status.connect(self.status_received_event)
                runnable.signals.log_message.connect(self.terminal_view.log_message)
                runnables.append(runnable)
        except OutputDirectoryNotSet:
            QMessageBox.critical(self, "Error! Output directory not selected",
                                 "Encoding cannot start because the output directory is not selected. "
                                 "You can select the output directory from Settings")
            self.statusBar().showMessage("Error! Output directory not selected", msecs=400)
            return
        except EncoderNotSelected:
            QMessageBox.critical(self, "Error! Encoder not selected",
                                 "Encoding cannot start because the output encoder is not selected. "
                                 "You can select the output encoder from Settings", msecs=400)
            self.statusBar().showMessage("Error! Encoder not selected")
            return

        if len(runnables) <= 0:
            self.statusBar().showMessage("Nothing to encode!")
            return

        self.progressbar.setValue(0)
        self.progressbar.setMaximum(len(runnables))
        self.main_panel.encoding_started(run_indices)
        self.executor = CommonUtils.CommandExecutionFactory(runnables,
                                                            logger=TransCoda.logger,
                                                            max_threads=TransCodaSettings.get_max_threads())
        self.executor.finish_event.connect(self.jobs_complete_event)
        self.statusBar().showMessage(f"Dispatching {self.progressbar.maximum()} jobs for encoding")
        self.executor.start()

    def result_received_event(self, result):
        self.main_panel.update_items(result)
        items = self.main_panel.get_items()
        TransCodaSettings.save_encode_list(items)
        self.progressbar.setValue(self.progressbar.value() + len(result))
        self.update_status_bar()

    def status_received_event(self, status):
        self.main_panel.update_items([status])
        items = self.main_panel.get_items()
        TransCodaSettings.save_encode_list(items)
        self.update_status_bar()

    def jobs_complete_event(self, all_results, time_taken):
        self.progressbar.setValue(self.progressbar.maximum())
        self.executor = None
        self.statusBar().showMessage(f"Processed {len(all_results)} files in {time_taken} seconds", msecs=400)
        self.set_window_title()

    def files_changed_event(self, is_added, files):
        if is_added:
            scanner = CommonUtils.FileScanner(files, recurse=True, is_qfiles=True)
            qurls = []
            for file in scanner.files:
                qurls.append(QUrl(f"file://{file}"))
            # Add files first
            total_added = self.main_panel.add_qurls(qurls)
            items = self.main_panel.get_items()
            TransCodaSettings.save_encode_list(items)
            # Fetch and enrich with metadata
            retriever = MetadataRetriever(scanner.files)
            retriever.signals.result.connect(self.result_received_event)
            # UX
            self.progressbar.setValue(0)
            self.progressbar.setMaximum(total_added)
            self.executor = CommonUtils.CommandExecutionFactory([retriever],
                                                                logger=TransCoda.logger,
                                                                max_threads=TransCodaSettings.get_max_threads())
            self.executor.finish_event.connect(self.jobs_complete_event)
            self.executor.start()

    def settings_changed(self, setting, value):
        valid_keys = {SettingsKeys.encoder_path}
        if setting in valid_keys:
            self.encoder.setText(TransCodaSettings.get_encoder_name())

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


def main():
    app = QApplication(sys.argv)
    _ = TransCodaApp()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
