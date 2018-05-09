import sys
import subprocess
import os

from PyQt5.QtWidgets import (QWidget,
                             QApplication,
                             QLabel,
                             QHBoxLayout,
                             QVBoxLayout,
                             QStyleFactory,
                             QGridLayout,
                             QLineEdit,
                             QCheckBox,
                             QTabWidget,
                             QPushButton,
                             QMessageBox)

from CustomUI import FileChooser
from RobocopySwitchDictionary import allOptions


class RoboGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):

        test_button = QPushButton("Preview")
        exec_button = QPushButton("Start!!")
        # save_button = QPushButton("Save")

        btnLayout = QHBoxLayout()
        btnLayout.addStretch()
        # btnLayout.addWidget(save_button)
        btnLayout.addWidget(test_button)
        test_button.clicked.connect(self.run_test)
        btnLayout.addWidget(exec_button)

        layout = QVBoxLayout()
        layout.addLayout(self.setup_file_chooser())
        layout.addLayout(self.setup_copy_options())
        layout.addLayout(btnLayout)

        self.setLayout(layout)
        self.setWindowTitle('Robocopy Command Generator')
        self.show()

    def setup_file_chooser(self):
        layout = QGridLayout()
        source = FileChooser("Source", "Select Source", True)
        source.setObjectName("Source Directory")
        target = FileChooser("Target", "Select Target", True)
        target.setObjectName("Target Directory")
        layout.addWidget(source, 1, 0)
        layout.addWidget(target, 2, 0)
        return layout

    def setup_copy_options(self):
        tabWidget = QTabWidget()
        layout = QHBoxLayout()
        layout.addWidget(tabWidget)
        tabs = ["Source", "Destination", "Copy", "Logging", "Advanced"]
        for tab in tabs:
            tabWidget.addTab(self.setup_ui_from_options(tab), tab)
        return layout

    @staticmethod
    def setup_ui_from_options(key):
        key_options = allOptions[key]
        check = 0
        entry = 0
        checkgrid = QGridLayout()
        checkgrid.setSpacing(5)
        entrygrid = QGridLayout()
        entrygrid.setSpacing(5)

        for option in key_options:
            if option.find(":n") > 0:
                # Text Box
                widget = QLineEdit()
                width = widget.fontMetrics().boundingRect("999").width() + 12
                widget.setMaximumWidth(width)
                container = QHBoxLayout()
                container.addWidget(widget)
                container.setSpacing(5)
                container.addWidget(QLabel(key_options[option]))
                entrygrid.addLayout(container, entry, 0)
                option = option[:option.find(":") + 1]  # Strip directives
                entry += 1
            elif option.find(":file") > 0:
                # File Browser
                widget = FileChooser(key_options[option], key_options[option], False)
                entrygrid.addWidget(widget, entry, 0)
                option = option[:option.find(":") + 1]  # Strip directives
                entry += 1
            else:
                # Check box
                widget = QCheckBox(key_options[option])
                checkgrid.addWidget(widget, check, 0)
                check += 1

            widget.setProperty("option", option)
            widget.setObjectName("option")

        panel = QWidget()
        grid = QVBoxLayout()
        grid.addLayout(checkgrid)
        grid.addLayout(entrygrid)
        grid.addStretch()
        panel.setLayout(grid)
        return panel

    def run_test(self):
        command = self.get_parameters(self)
        command += ' /L'
        os.system('start /wait powershell -NoProfile -NoExit -Command "%s"' %command)

    def get_parameters(self, parent):
        command = 'robocopy '
        source = self.get_path("Source Directory", parent)
        if not source:
            return
        command = command + " " + source
        target = self.get_path("Target Directory", parent)
        if not target:
            return
        command = command + " " + target

        children = parent.findChildren(QWidget, name="option")
        for child in children:
            # Checkbox
            if type(child) is QCheckBox:
                if child.isChecked():
                    command = command + " " + child.property("option")
            # File Chooser
            elif type(child) is FileChooser:
                if child.getSelection() != '':
                    command = command + " " + \
                              child.property("option") + child.getSelection()
            # Text box
            elif type(child) is QLineEdit:
                if child.text() != '':
                    command = command + " " + \
                              child.property("option") + child.text()
        print("%s" % command)
        return command

    @staticmethod
    def get_path(name, container):
        widget = container.findChildren(FileChooser, name=name)
        path = widget[0].getSelection()
        if not path:
            error = str("%s is not specified" % name)
        # elif QDir.exists(path.re):
        #     error = str("%s is not a valid location" % name)
        else:
            return path

        if error:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText(error)
            msg.setInformativeText("In order to continue, please correct this issue and retry.")
            msg.setWindowTitle("Cannot proceed!")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec()

        return False


if __name__ == '__main__':
    # print("%s" % str(options.allOptions))
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("GTK+"))
    ex = RoboGUI()
    sys.exit(app.exec_())
