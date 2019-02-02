import sys

from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtWidgets import (QApplication,
                             QMainWindow)

import AutocodeUtils
from Panels import (MainPanel, InputOptions, OutputOptions, EncoderOptions, ProgressWidget)
from Runtime import TaskRunner


class Autocode(QMainWindow):
    def __init__(self, plugin_dir):
        super().__init__()
        self.plugins = AutocodeUtils.get_available_encoders(plugin_dir)

        self.mainPanel = MainPanel()
        self.mainPanel.file_drop_event.connect(self.files_added)

        self.inputOptions = InputOptions()
        self.outputOptions = OutputOptions()
        self.encoderOptions = EncoderOptions(self.plugins)

        self.progress = ProgressWidget()
        self.progress.start_processing.connect(self.start_encode)
        self.progress.stop_processing.connect(self.stop_encode)

        self.settings = QSettings("github.com/ag-sd", "Autocode")
        self.current_files = []
        self.logger = AutocodeUtils.get_logger("Autocode")

        self.taskRunner = TaskRunner()
        self.taskRunner.encode_started.connect(self.start_encode)
        self.taskRunner.encode_completed.connect(self.encode_completed)
        self.initUI()

    def initUI(self):
        self.logger.info("Initializing UI")
        self.setCentralWidget(self.mainPanel)
        self.addDockWidget(Qt.TopDockWidgetArea, self.inputOptions)
        self.addDockWidget(Qt.TopDockWidgetArea, self.outputOptions)
        self.addDockWidget(Qt.TopDockWidgetArea, self.encoderOptions)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.progress)

        AutocodeUtils.load_settings(self, self.settings)
        self.statusBar().showMessage('Ready')
        self.setWindowTitle('Autocode')
        self.show()
        if self.current_files is not None:
            self.files_added(self.current_files)
        self.logger.info("Initializing UI - Completed")

    def closeEvent(self, *args, **kwargs):
        AutocodeUtils.save_settings(self, self.settings)

    def encode_started(self, file):
        self.logger.info("START----------------->" + file)

    def encode_completed(self, file):
        self.logger.info("FINISH----------------->" + file)

    def start_encode(self):
        self.logger.info("I should start!")
        # Get list of files from Table
        file_model = self.mainPanel.model()

        # Send to TaskEncoder
        self.taskRunner.start(file_model, "FOOOO/", "BAR", 10)

    def stop_encode(self):
        self.logger.info("I should stop!")

    def files_added(self, file_urls):
        model, rejected = AutocodeUtils.create_model(file_urls,
                                                     self.inputOptions.shouldRecurseSubdirs())
        # if len(rejected) > 0:
        #     msg = QMessageBox()
        #     msg.setIcon(QMessageBox.Information)
        #     msg.setText("The following files were not added as no supported encoder was found for them.")
        #     msg.setInformativeText("You can configure the encoders and supported files that Autocode "
        #                            "uses from the Encoder Options panel")
        #     msg.setWindowTitle("Autocode Notification")
        #     msg.setDetailedText('\n'.join(rejected))
        #     msg.setStandardButtons(QMessageBox.Ok)
        #     msg.exec()

        self.mainPanel.setModel(model)
        self.mainPanel.resizeColumnsToContents()
        self.mainPanel.resizeRowsToContents()
        self.current_files = file_urls


if __name__ == '__main__':
    # print("%s" % str(options.allOptions))
    app = QApplication(sys.argv)
    # app.setStyle(QStyleFactory.create("GTK+"))
    ex = Autocode("/media/sheldon/Stuff/py/Autocode/plugins")
    sys.exit(app.exec_())
