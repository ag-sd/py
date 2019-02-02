from PyQt5.QtCore import (Qt, pyqtSignal, )
from PyQt5.QtWidgets import (QVBoxLayout,
                             QHBoxLayout,
                             QTableView,
                             QCheckBox,
                             QDockWidget,
                             QComboBox,
                             QGroupBox,
                             QAbstractItemView,
                             QPushButton,
                             QLabel,
                             QRadioButton,
                             QSpinBox)

from CustomUI import FileChooser


class MainPanel(QTableView):
    file_drop_event = pyqtSignal('PyQt_PyObject')

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        # stylesheet = "QHeaderView::section{" \
        #              "border-top:0px solid #D8D8D8;" \
        #              "border-left:0px solid #D8D8D8;" \
        #              "border-right:1px solid #D8D8D8;" \
        #              "border-bottom: 1px solid #D8D8D8;" \
        #              "padding:4px;" \
        #              "}"
        # self.horizontalHeader().setStyleSheet(stylesheet)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.verticalHeader().hide()
        self.horizontalHeader().setHighlightSections(False)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls:
            event.setDropAction(Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls:
            self.file_drop_event.emit(event.mimeData().urls())
        else:
            event.ignore()


class InputOptions(QDockWidget):
    def __init__(self):
        super().__init__()
        lbl = QLabel("           ")
        lbl.setFixedSize(48, 48)
        self.chkRecurse = QCheckBox("Recurse Subdirectories")
        self.chkRecurse.setObjectName("stateful_chkRecurse")
        layout = QVBoxLayout()
        layout.addWidget(self.chkRecurse)
        layout.addStretch(1)
        container = QGroupBox()
        container.setLayout(layout)
        self.setFeatures(QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetClosable)
        self.setWidget(container)
        self.setWindowTitle("Input Options")

    def shouldRecurseSubdirs(self):
        return self.chkRecurse.isChecked()


class OutputOptions(QDockWidget):
    def __init__(self):
        super().__init__()
        self.fileChooser = FileChooser("Output Dir: ", "Select output directory", True)
        self.fileChooser.setObjectName("stateful_fileChooser")
        self.dirStructure = QCheckBox("Preserve Directory Structure")
        self.dirStructure.setObjectName("stateful_dirStructure")
        layout = QVBoxLayout()
        layout.addWidget(self.fileChooser)
        layout.addWidget(self.dirStructure)
        layout.addStretch(1)
        container = QGroupBox()
        container.setLayout(layout)
        self.setFeatures(QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetClosable)
        self.setWidget(container)
        self.setWindowTitle("Output Options")

    def getOutputDirectory(self):
        return self.fileChooser.getSelection()

    def preserveDirStructure(self):
        return self.dirStructure.isChecked()


class EncoderOptions(QDockWidget):
    def __init__(self, plugins):
        super().__init__()
        self.plugin_dictionary = {}
        plugin_names = ["Foo"]
        for plugin in plugins:
            self.plugin_dictionary[plugin.name] = plugin
            plugin_names.append(plugin.name)
        self.encoderCombo = QComboBox()
        self.encoderCombo.addItems(plugin_names)
        self.encoderCombo.currentIndexChanged[str].connect(self.item_change_lambda)
        self.version = QLabel("Version: ")
        self.author = QLabel("Author: ")
        self.description = QLabel("Plugin Description: ")
        self.input_extensions = QLabel("Supported Extensions: ")

        self.configure = QPushButton("Configure...")
        self.initUI()

    def initUI(self):
        cmb_layout = QHBoxLayout()
        cue = QLabel("Select Encoder: ")
        width = cue.fontMetrics().boundingRect(cue.text()).width() + 12
        cue.setMaximumWidth(width)
        cmb_layout.addWidget(cue)
        cmb_layout.addWidget(self.encoderCombo)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch(1)
        btn_layout.addWidget(self.configure)

        plugin_layout = QVBoxLayout()
        plugin_layout.addWidget(self.version)
        plugin_layout.addWidget(self.author)
        plugin_layout.addWidget(self.description)
        plugin_layout.addWidget(self.input_extensions)
        plugin_layout.addLayout(btn_layout)

        plugin_group = QGroupBox("Encoder Details")
        plugin_group.setLayout(plugin_layout)

        layout = QVBoxLayout()
        layout.addLayout(cmb_layout)
        #layout.addLayout(btn_layout)
        layout.addWidget(plugin_group)
        layout.addStretch(1)

        container = QGroupBox()
        container.setLayout(layout)
        self.setFeatures(QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetClosable)
        self.setWidget(container)
        self.setWindowTitle("Encoder Options")

    def item_change_lambda(self, plugin_name):
        plugin = self.plugin_dictionary[plugin_name]
        self.version.setText("Version: " + plugin.version)
        self.author.setText("Author: " + plugin.author)
        self.description.setText("Description: " + plugin.description)
        self.input_extensions.setText("Supported Extensions: " + plugin.input_extensions)


class ProgressWidget(QDockWidget):
    start_processing = pyqtSignal()
    stop_processing = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.optionEncodeAll = QRadioButton("Once all files are processed")
        self.optionEncodeAll.setObjectName("stateful_optionEncodeAll")
        self.optionEncodeTime = QRadioButton("After a fixed number of hours")
        self.optionEncodeTime.setObjectName("stateful_optionEncodeTime")
        self.optionEncodeTimeValue = QSpinBox()
        self.optionEncodeTimeValue.setObjectName("stateful_optionEncodeTimeValue")
        self.btnStart = QPushButton("START!")
        self.btnStart.clicked.connect(self.start_processing)
        self.btnStop = QPushButton("STOP!")
        self.btnStop.clicked.connect(self.stop_processing)
        self.initUI()

    def initUI(self):
        run_layout = QVBoxLayout()
        run_layout.addWidget(self.optionEncodeAll)

        hrs_layout = QHBoxLayout()
        hrs_layout.addWidget(self.optionEncodeTime)
        hrs_layout.addWidget(self.optionEncodeTimeValue)
        run_layout.addLayout(hrs_layout)
        run_layout.addStretch(1)

        run_group = QGroupBox("Shutdown computer")
        run_group.setCheckable(True)
        run_group.setChecked(False)
        run_group.setObjectName("stateful_run_group")
        run_group.setLayout(run_layout)

        cmd_layout = QVBoxLayout()
        cmd_layout.addWidget(self.btnStart)
        cmd_layout.addWidget(self.btnStop)
        cmd_layout.addStretch(1)

        layout = QHBoxLayout()
        layout.addWidget(run_group)
        layout.addStretch(1)
        layout.addLayout(cmd_layout)

        container = QGroupBox()
        container.setLayout(layout)
        self.setFeatures(QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetClosable)
        self.setWidget(container)
        self.setWindowTitle("Runtime Options")



# class ScriptConfigurePanel(QWidget):
#     def __init__(self):
#         super().__init__()
#         self.initUI()
#
#     def initUI(self):
#         #self.setLayout(layout)
#         self.setWindowTitle('Edit Autocode Script')
#         self.show()
#
#
# if __name__ == '__main__':
#     from PyQt5.QtWidgets import (QApplication)
#     import sys
#     app = QApplication(sys.argv)
#     ex = ScriptConfigurePanel()
#     ex.show()
#     sys.exit(app.exec_())