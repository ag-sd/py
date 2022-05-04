import os
import re
import shutil
import sys
from functools import partial

from PyQt5.QtCore import Qt, QCoreApplication, QMimeDatabase
from PyQt5.QtGui import QIcon, QBrush, QColor
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout, \
    QProgressBar, QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QLabel, QProgressDialog, \
    QRadioButton, QSpinBox, QComboBox, QGroupBox

from CustomUI import FileChooserTextBox, QVLine, DropZone
from FileWrangler import logger
from FileWrangler.FileWranglerCore import ActionKeys, DisplayKeys, ConfigKeys, create_merge_tree, _UNKNOWN_KEY, \
    _DEFAULT_REGEX, KeyType, SortBy


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

        self.move_button = QPushButton(ActionKeys.move.value)
        self.move_button.pressed.connect(partial(self.execute_merge, ActionKeys.move.value))
        self.copy_button = QPushButton(ActionKeys.copy.value)
        self.copy_button.pressed.connect(partial(self.execute_merge, ActionKeys.copy.value))
        self.progress_bar = QProgressBar()
        self.date_checkbox = QCheckBox("Append Date (YYYY.MM.DD) to destination file")
        self.delete_source_checkbox = QCheckBox("After move, delete Source directories if empty")
        self.dir_include = QSpinBox()
        self.dir_include.setMinimum(0)
        self.dir_include.setValue(0)
        self.dir_include.setMaximum(10)
        self.sort_name = QRadioButton("Name")
        self.sort_name.setChecked(True)
        self.sort_date = QRadioButton("Date")
        self.sort_size = QRadioButton("Size")
        self.sort_none = QRadioButton("None")
        self.key_token_string = QComboBox()
        self.key_token_string.setEditable(True)
        self.key_token_string.setInsertPolicy(QComboBox.InsertAtTop)
        self.key_token_string.setCurrentText(_DEFAULT_REGEX)
        self.key_separator = QRadioButton("Separator")
        self.key_regex = QRadioButton("Regular Expression")
        self.key_regex.setChecked(True)
        self.key_replace = QRadioButton("Completely Replace")
        self.key_match_counter = QSpinBox()
        self.key_match_counter.setMinimum(1)
        self.key_match_counter.setValue(1)
        self.key_match_counter.setMaximum(10)
        self.dropZone = DropZone()

        self.key_match_counter.valueChanged.connect(self.create_merge)
        self.dir_include.valueChanged.connect(self.create_merge)
        self.dropZone.files_dropped_event.connect(self.create_merge)
        self.key_token_string.editTextChanged.connect(self.create_merge)
        self.key_regex.released.connect(partial(self.create_merge))
        self.key_replace.released.connect(partial(self.create_merge))
        self.key_separator.released.connect(partial(self.create_merge))
        self.date_checkbox.stateChanged.connect(self.create_merge)
        self.targetDir.file_selection_changed.connect(self.create_merge)
        self.sort_date.released.connect(partial(self.create_merge))
        self.sort_name.released.connect(partial(self.create_merge))
        self.sort_size.released.connect(partial(self.create_merge))
        self.sort_none.released.connect(partial(self.create_merge))
        self.table = MainTable()
        self.init_ui()

    def init_ui(self):
        def create_dropzone_groupbox():
            dropzone_sort_layout = QHBoxLayout()
            dropzone_sort_layout.addWidget(QLabel("Order By"))
            dropzone_sort_layout.addWidget(self.sort_name)
            dropzone_sort_layout.addWidget(self.sort_date)
            dropzone_sort_layout.addWidget(self.sort_size)
            dropzone_sort_layout.addWidget(self.sort_none)
            dropzone_layout = QVBoxLayout()
            dropzone_layout.addWidget(self.dropZone)
            dropzone_layout.addLayout(dropzone_sort_layout)
            dropzone_layout.setContentsMargins(0, 0, 0, 0)

            groupbox = QGroupBox()
            groupbox.setLayout(dropzone_layout)
            return groupbox

        def create_rename_controlbox():
            self.move_button.setIcon(QIcon.fromTheme("edit-paste"))
            self.copy_button.setIcon(QIcon.fromTheme("edit-copy"))

            button_layout = QHBoxLayout()
            button_layout.addWidget(QLabel(""), stretch=1)
            button_layout.addWidget(self.move_button)
            button_layout.addWidget(self.copy_button)

            key_layout = QHBoxLayout()
            key_layout.addWidget(QLabel("Match Key:   "))
            key_layout.addWidget(self.key_match_counter)
            key_layout.addWidget(QLabel("Key Identifier"))
            key_layout.addWidget(self.key_token_string, stretch=1)
            key_layout.addWidget(self.key_regex)
            key_layout.addWidget(self.key_separator)
            key_layout.addWidget(self.key_replace)

            sub_control_layout = QHBoxLayout()
            sub_control_layout.addWidget(QLabel("Dir. names:  "))
            sub_control_layout.addWidget(self.dir_include)
            sub_control_layout.addWidget(self.date_checkbox)
            sub_control_layout.addWidget(self.delete_source_checkbox)
            sub_control_layout.addWidget(QLabel(""), stretch=1)

            control_layout = QVBoxLayout()
            control_layout.addWidget(self.targetDir)
            control_layout.addLayout(key_layout)
            control_layout.addLayout(sub_control_layout)
            # control_layout.addWidget(QLabel(""))
            control_layout.addLayout(button_layout)

            groupbox = QGroupBox()
            groupbox.setLayout(control_layout)
            return groupbox

        top_layout = QHBoxLayout()
        top_layout.addWidget(create_dropzone_groupbox())
        top_layout.addWidget(QVLine())
        top_layout.addWidget(create_rename_controlbox())

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

    def create_merge(self):
        token_string = self.key_token_string.currentText()
        if token_string is None or token_string == "":
            return

        sort_key = SortBy.none
        if self.sort_size.isChecked():
            sort_key = SortBy.size
        elif self.sort_name.isChecked():
            sort_key = SortBy.name
        elif self.sort_date.isChecked():
            sort_key = SortBy.date

        config = {
            ConfigKeys.append_date: self.date_checkbox.isChecked(),
            ConfigKeys.key_token_string: self.key_token_string.currentText(),
            ConfigKeys.key_token_count: self.key_match_counter.value(),
            ConfigKeys.sort_by: sort_key,
            ConfigKeys.dir_include: self.dir_include.value()
        }

        if self.key_regex.isChecked():
            try:
                re.compile(self.key_token_string.currentText())
                config[ConfigKeys.key_type] = KeyType.regular_expression
            except re.error:
                logger.error("Regular expression error")
                return
        elif self.key_replace.isChecked():
            config[ConfigKeys.key_type] = KeyType.replacement
        else:
            config[ConfigKeys.key_type] = KeyType.separator

        try:
            model = create_merge_tree(self.dropZone.dropped_files, self.targetDir.getSelection(), config)
            if model:
                self.table.set_model(model)
        except FileNotFoundError as fne:
            logger.error(f"File not found {fne.filename}")

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
        source_dirs = set()
        for item in file_items:
            source = item[DisplayKeys.source]
            source_dirs.add(os.path.dirname(source))
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
        self.key_token_string.blockSignals(True)
        self.key_token_string.addItem(self.key_token_string.currentText())
        self.key_token_string.blockSignals(False)

        # Delete Source dirs
        if self.delete_source_checkbox.checkState() == Qt.Checked:
            for _dir in source_dirs:
                if not os.listdir(_dir):
                    logger.info(f"Directory {_dir} is empty. Attempting to delete it")
                    os.rmdir(_dir)
                    logger.info(f"Directory {_dir} is empty. Attempting to delete it - Done")
                else:
                    logger.info(f"Directory {_dir} is not empty, so will not delete it")


def main():
    app = QApplication(sys.argv)
    # app.setStyleSheet("QGroupBox {  border: 1px solid gray;}")
    ex = FileWranglerApp()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
