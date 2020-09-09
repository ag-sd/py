import os
import re
import shutil
import sys
from functools import partial

from PyQt5.QtCore import Qt, QCoreApplication, QMimeDatabase
from PyQt5.QtGui import QIcon, QBrush, QColor
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout, \
    QProgressBar, QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QLabel, QProgressDialog, \
    QLineEdit

from CustomUI import FileChooserTextBox, QVLine, DropZone
from FileWrangler import logger
from FileWrangler.FileWranglerCore import ActionKeys, DisplayKeys, ConfigKeys, create_merge_tree, _UNKNOWN_KEY, \
    _DEFAULT_REGEX


class MainTable(QTableWidget):
    _error_brush = QBrush(QColor(220, 20, 60, 75))
    _mime_database = QMimeDatabase()

    def __init__(self):
        super().__init__()
        self._reset()
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.verticalHeader().setDefaultSectionSize(self.verticalHeader().fontMetrics().height() + 3)
        self.verticalHeader().hide()
        self.horizontalHeader().setHighlightSections(False)
        self.horizontalHeader().setSectionsMovable(True)
        self.horizontalHeader().setSectionsClickable(True)
        self.setSortingEnabled(True)
        self.model = None

    def is_selected(self, source_file):
        matches = self.findItems(source_file, Qt.MatchExactly)
        if len(matches):
            return matches[0].checkState() == Qt.Checked
        else:
            return False

    def remove_file(self, source_file):
        matches = self.findItems(source_file, Qt.MatchExactly)
        if len(matches):
            self.removeRow(matches[0].row())

    def set_model(self, file_items):
        self._reset()
        self.setRowCount(len(file_items))
        self.setSortingEnabled(False)
        for i in range(0, len(file_items)):
            source = file_items[i][DisplayKeys.source]
            target = file_items[i][DisplayKeys.target]
            source_item = QTableWidgetItem(source)
            target_item = QTableWidgetItem(target)
            mime = MainTable._mime_database.mimeTypesForFileName(source)
            if len(mime):
                source_item.setIcon(QIcon.fromTheme(mime[0].iconName()))
            else:
                logger.error("Unable to determine mime type for " + source)
                source_item.setIcon(QIcon.fromTheme("text-x-generic"))
            source_item.setCheckState(Qt.Checked)
            _, file_name = os.path.split(target)
            if file_name.startswith(_UNKNOWN_KEY):
                target_item.setBackground(MainTable._error_brush)
                source_item.setBackground(MainTable._error_brush)
                source_item.setCheckState(Qt.Unchecked)
            self.setItem(i, 0, source_item)
            self.setItem(i, 1, target_item)
        self.setSortingEnabled(True)
        self.model = file_items

    def _reset(self):
        self.clear()
        self.setColumnCount(2)
        self.setHorizontalHeaderItem(0, QTableWidgetItem("Source File"))
        self.setHorizontalHeaderItem(1, QTableWidgetItem("Destination File"))
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)


class FileWranglerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.targetDir = FileChooserTextBox("Destination: ", "Select destination directory", True)
        self.targetDir.file_selection_changed.connect(self.create_merge)
        self.move_button = QPushButton(ActionKeys.move.value)
        self.move_button.pressed.connect(partial(self.execute_merge, ActionKeys.move.value))
        self.copy_button = QPushButton(ActionKeys.copy.value)
        self.copy_button.pressed.connect(partial(self.execute_merge, ActionKeys.copy.value))
        self.progress_bar = QProgressBar()
        self.date_checkbox = QCheckBox("Append Date (YYYY.MM.DD) to destination file")
        self.date_checkbox.stateChanged.connect(self.create_merge)
        self.key_regex = QLineEdit(_DEFAULT_REGEX)
        self.key_regex.textChanged.connect(self.create_merge)
        self.dropZone = DropZone()
        self.dropZone.files_dropped_event.connect(self.create_merge)
        self.table = MainTable()
        self.init_ui()

    def init_ui(self):
        self.move_button.setIcon(QIcon.fromTheme("edit-paste"))
        self.copy_button.setIcon(QIcon.fromTheme("edit-copy"))

        button_layout = QHBoxLayout()
        button_layout.addWidget(QLabel(""), stretch=1)
        button_layout.addWidget(self.move_button)
        button_layout.addWidget(self.copy_button)

        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("Key Identifier"))
        key_layout.addWidget(self.key_regex)
        control_layout = QVBoxLayout()
        control_layout.addWidget(self.targetDir)
        control_layout.addWidget(self.date_checkbox)
        control_layout.addLayout(key_layout)
        control_layout.addWidget(QLabel(""))
        control_layout.addLayout(button_layout)

        top_layout = QHBoxLayout()
        top_layout.addWidget(self.dropZone)
        top_layout.addWidget(QVLine())
        top_layout.addLayout(control_layout)

        main_layout = QVBoxLayout()
        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.table)
        main_layout.setContentsMargins(2, 2, 2, 2)

        dummy_widget = QWidget()
        dummy_widget.setLayout(main_layout)
        self.setCentralWidget(dummy_widget)

        self.setWindowTitle('File Wrangler')
        self.setMinimumWidth(1724)
        self.setMinimumHeight(768)
        self.show()

    def create_merge(self, _):
        try:
            re.compile(self.key_regex.text())
        except re.error:
            logger.error("Regular expression error")
            return

        config = {
            ConfigKeys.append_date: self.date_checkbox.isChecked(),
            ConfigKeys.key_regex: self.key_regex.text()
        }
        model = create_merge_tree(self.dropZone.dropped_files, self.targetDir.getSelection(), config)
        if model:
            self.table.set_model(model)

    def execute_merge(self, action):
        file_items = self.table.model
        transfer_dialog = QProgressDialog()
        transfer_dialog.setWindowModality(Qt.WindowModal)
        transfer_dialog.setWindowTitle(action + " Files")
        transfer_dialog.setCancelButtonText("Abort")
        transfer_dialog.setValue(0)
        transfer_dialog.setMaximum(len(file_items))
        transfer_dialog.setMinimumWidth(550)
        transfer_dialog.setMaximumWidth(self.minimumWidth())
        transfer_dialog.show()
        for item in file_items:
            source = item[DisplayKeys.source]
            target = item[DisplayKeys.target]
            transfer_dialog.setValue(transfer_dialog.value() + 1)
            if self.table.is_selected(source):
                logger.debug(f"{action}: {source} -> {target}")
                transfer_dialog.setLabelText(f"{action}: \n{source} \n->\n {target}")
                # Allow repainting etc.
                QCoreApplication.processEvents()
                if action == ActionKeys.copy.value:
                    shutil.copy(source, target)
                    self.table.remove_file(source)
                elif action == ActionKeys.move.value:
                    shutil.move(source, target)
                    self.table.remove_file(source)
                else:
                    logger.error("Unknown Action! " + action)
            if transfer_dialog.wasCanceled():
                logger.info("User aborted operation")
                break


def main():
    app = QApplication(sys.argv)
    ex = FileWranglerApp()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
