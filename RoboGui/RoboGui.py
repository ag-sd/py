import sys

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
                             QPushButton)

from CustomUI import FileChooser
from RobocopySwitchDictionary import allOptions


class RoboGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.source = ''
        self.target = ''

    def initUI(self):

        test_button = QPushButton("Preview")
        exec_button = QPushButton("Start!!")
        save_button = QPushButton("Save")

        btnLayout = QHBoxLayout()
        btnLayout.addStretch()
        btnLayout.addWidget(save_button)
        btnLayout.addWidget(test_button)
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
        layout.addWidget(FileChooser("Source", "Select Source", True), 1, 0)
        layout.addWidget(FileChooser("Target", "Select Target", True), 2, 0)
        return layout

    def setup_copy_options(self):
        tabWidget = QTabWidget()
        layout = QHBoxLayout()
        layout.addWidget(tabWidget)
        tabs = ["Source Options", "Destination Options", "Copy Options", "Logging options"]
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
                entry += 1
            elif option.find(":file") > 0:
                # File Browser
                widget = FileChooser(key_options[option], key_options[option], False, True)
                entrygrid.addWidget(widget, entry, 0)
                entry += 1
            else:
                # Check box
                widget = QCheckBox(key_options[option])
                checkgrid.addWidget(widget, check, 0)
                check += 1

            widget.setProperty("option", option)
            widget.setProperty("robocopy_flag", True)

        panel = QWidget()
        grid = QVBoxLayout()
        grid.addLayout(checkgrid)
        grid.addLayout(entrygrid)
        grid.addStretch()
        panel.setLayout(grid)
        return panel


if __name__ == '__main__':
    #print("%s" % str(options.allOptions))
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("GTK+"))
    ex = RoboGUI()
    sys.exit(app.exec_())

# ly = panel.layout()
# for i in range(ly.count()):
#     item = ly.itemAt(i)
#     item = item.widget()
#     print("linedit: %s  - %s\n" % (item.property("option"), item.text()))