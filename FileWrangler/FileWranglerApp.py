import os
import shutil
import sys
from functools import partial

from PyQt5.QtCore import Qt, QCoreApplication
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout, \
    QCheckBox, QLabel, QProgressDialog, \
    QRadioButton, QGroupBox, QStackedLayout, QMessageBox

import FileWrangler
from FileWrangler import logger, FileWranglerCore
from FileWrangler.FileWranglerCore import ActionKeys, DisplayKeys, ConfigKeys, create_merge_tree, SortBy
from FileWrangler.UIComponents import MainTable, FileOperationSelector
from common.CustomUI import FileChooserTextBox, DropZone


class FileWranglerApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.targetDir = FileChooserTextBox("Destination: ", "Select destination directory", True,
                                            text_box_editable=True)

        # File Copy Operations
        self.move_button = QPushButton(ActionKeys.move.value)
        self.move_button.setIcon(FileWrangler.theme.fromTheme("edit-move"))
        self.copy_button = QPushButton(ActionKeys.copy.value)
        self.copy_button.setIcon(FileWrangler.theme.fromTheme("edit-copy"))
        self.help_button = QPushButton(ActionKeys.help.value)
        self.help_button.setIcon(FileWrangler.theme.fromTheme("help-contents"))

        # File Name Operations
        self.date_checkbox = QCheckBox("Append Date (YYYY.MM.DD) to destination file")
        self.delete_source_checkbox = QCheckBox("After move, delete Source directories if empty")
        self.file_operations_widget = QGroupBox()
        self.file_operations_widget.setContentsMargins(0, 0, 0, 0)
        self.file_operation_selector = FileOperationSelector(FileWranglerCore.get_file_operations())
        self.file_operation_selector.setEditable(False)
        self.dry_run_checkbox = QCheckBox("Dry Run")
        self.dry_run_checkbox.setChecked(True)
        self.fill_gaps_checkbox = QCheckBox("Fill Gaps")

        # File Display Operations
        self.sort_name = QRadioButton("Name")
        self.sort_name.setChecked(True)
        self.sort_date = QRadioButton("Date")
        self.sort_size = QRadioButton("Size")
        self.sort_none = QRadioButton("None")
        self.dropZone = DropZone()

        self.table = MainTable()

        self.init_events()
        self.init_ui()

    def init_events(self):
        self.dropZone.files_dropped_event.connect(self.create_merge)
        self.move_button.pressed.connect(partial(self.execute_action, ActionKeys.move))
        self.copy_button.pressed.connect(partial(self.execute_action, ActionKeys.copy))
        self.help_button.pressed.connect(partial(self.execute_action, ActionKeys.help))
        self.targetDir.file_selection_changed.connect(self.create_merge)
        self.date_checkbox.stateChanged.connect(self.create_merge)
        self.delete_source_checkbox.stateChanged.connect(self.create_merge)
        self.fill_gaps_checkbox.stateChanged.connect(self.create_merge)
        self.file_operation_selector.currentIndexChanged.connect(self._create_file_operation_widget)
        self.sort_date.released.connect(partial(self.create_merge))
        self.sort_name.released.connect(partial(self.create_merge))
        self.sort_size.released.connect(partial(self.create_merge))
        self.sort_none.released.connect(partial(self.create_merge))

    def init_ui(self):
        self._create_file_operation_layouts()
        self._create_file_operation_widget()

        main_layout = QVBoxLayout()
        main_layout.addLayout(self._create_top_layout())
        main_layout.addWidget(self.table, stretch=1)
        main_layout.setContentsMargins(2, 2, 2, 2)

        dummy_widget = QWidget()
        dummy_widget.setLayout(main_layout)
        self.setCentralWidget(dummy_widget)

        self.help_button.setMaximumHeight(self.file_operation_selector.height())

        self.setWindowIcon(FileWrangler.theme.fromTheme("app_icon", use_system_fallback=False))
        self.setWindowTitle('File Wrangler')
        self.setMinimumWidth(1724)
        self.setMinimumHeight(768)
        self.show()

    def _create_top_layout(self):
        def _create_dropzone_groupbox():
            dropzone_sort_layout = QHBoxLayout()
            dropzone_sort_layout.addWidget(QLabel("Order By"))
            dropzone_sort_layout.addWidget(self.sort_name)
            dropzone_sort_layout.addWidget(self.sort_date)
            dropzone_sort_layout.addWidget(self.sort_size)
            dropzone_sort_layout.addWidget(self.sort_none)
            dropzone_layout = QVBoxLayout()
            dropzone_layout.addWidget(self.dropZone)
            dropzone_layout.setContentsMargins(0, 0, 0, 0)
            dropzone_layout.addLayout(dropzone_sort_layout)
            return dropzone_layout

        def _create_control_groupbox():

            op_layout = QHBoxLayout()
            op_layout.addWidget(self.file_operation_selector, stretch=2)
            op_layout.addWidget(self.help_button)

            operation_layout = QVBoxLayout()
            operation_layout.addWidget(self.targetDir)
            operation_layout.addLayout(op_layout)
            operation_layout.addWidget(self.file_operations_widget)
            operation_layout.setContentsMargins(0, 0, 0, 0)

            additional_file_operations = QHBoxLayout()
            additional_file_operations.addWidget(self.date_checkbox)
            additional_file_operations.addWidget(self.delete_source_checkbox)
            additional_file_operations.addWidget(QWidget(), stretch=1)
            additional_file_operations.addWidget(self.fill_gaps_checkbox)

            control_layout = QVBoxLayout()
            control_layout.setContentsMargins(0, 0, 0, 0)
            control_layout.setSpacing(0)
            control_layout.addLayout(operation_layout)
            control_layout.addLayout(additional_file_operations)
            return control_layout

        def _create_button_layout():
            layout = QVBoxLayout()
            layout.addWidget(QWidget(), stretch=1)
            layout.addWidget(self.dry_run_checkbox)
            layout.addWidget(self.move_button)
            layout.addWidget(self.copy_button)
            return layout

        def _wrap(layout):
            groupbox = QGroupBox()
            groupbox.setLayout(layout)
            return groupbox

        top_layout = QHBoxLayout()
        top_layout.addWidget(_wrap(_create_dropzone_groupbox()))
        top_layout.addWidget(_wrap(_create_control_groupbox()))
        top_layout.addWidget(_wrap(_create_button_layout()))
        top_layout.setContentsMargins(0, 0, 0, 0)
        return top_layout

    def _create_file_operation_layouts(self):
        stacked_layout = QStackedLayout()
        for op_index in range(self.file_operation_selector.count()):
            op = self.file_operation_selector.operation_at(op_index)
            stacked_layout.addWidget(op.get_widget())
        self.file_operations_widget.setLayout(stacked_layout)

    def _create_file_operation_widget(self):
        op = self.file_operation_selector.selected_operation()
        op.merge_event.connect(self.create_merge)
        self.file_operations_widget.layout().setCurrentIndex(self.file_operation_selector.currentIndex())
        self.create_merge()

    def create_merge(self):
        if self.file_operation_selector.selected_operation() is None:
            logger.warning("Current Operation hasn't been selected yet")
            return
        elif not self.file_operation_selector.selected_operation().is_ready():
            logger.warning("Current Operation is not ready")
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
            ConfigKeys.sort_by: sort_key,
            ConfigKeys.key_type: self.file_operation_selector.selected_operation().name,
            ConfigKeys.context: self.file_operation_selector.selected_operation().get_context(),
            ConfigKeys.is_version_2: True,
            ConfigKeys.operation: self.file_operation_selector.selected_operation(),
            ConfigKeys.fill_gaps: self.fill_gaps_checkbox.isChecked()

        }

        try:
            model = create_merge_tree(self.dropZone.dropped_files, self.targetDir.getSelection(), config)
            if model:
                self.table.set_model(model)
        except FileNotFoundError as fne:
            logger.error(f"File not found {fne.filename}")

    def execute_action(self, action):
        match action:
            case ActionKeys.help:
                QMessageBox.about(self, FileWrangler.__APP_NAME__,
                                  self.file_operation_selector.selected_operation().get_help())
            case _:
                # Disable any input operations
                file_items = self.table.model
                total_items = len(file_items)
                completed_items = 1
                transfer_dialog = self._create_transfer_dialog(action.name, total_items)
                source_dirs = set()
                for item in file_items:
                    source = item[DisplayKeys.source]
                    source_dirs.add(os.path.dirname(source))
                    target = item[DisplayKeys.target]
                    transfer_dialog.setValue(transfer_dialog.value() + 1)
                    if self.table.is_selected(source):
                        target_path, _ = os.path.split(target)
                        if not os.path.exists(target_path):
                            logger.error(f"CANNOT {action.name.upper()}: {source} -> {target} "
                                         f"as target path '{target_path}' does not exist! Skipping this file...")
                            continue
                        # Prevent Overwrites
                        if os.path.exists(target):
                            logger.error(f"CANNOT {action.name.upper()}: {source} -> {target} "
                                         f"as target file '{target}' exists! Skipping this file...")
                            continue
                        logger.debug(f"{action.name} ({completed_items} / {total_items}) : {source} -> {target}")
                        transfer_dialog.setLabelText(f"{action.name}\n({completed_items} / {total_items})"
                                                     f"\n{source} \n->\n {target}")
                        # Allow repainting etc.
                        QCoreApplication.processEvents()
                        # SH OPERATION
                        if not self.dry_run_checkbox.isChecked():
                            try:
                                if action == ActionKeys.copy:
                                    shutil.copy2(source, target)
                                    self.table.remove_file(source)
                                elif action == ActionKeys.move:
                                    shutil.move(source, target)
                                    self.table.remove_file(source)
                                else:
                                    logger.error("Unknown Action! " + str(action))
                                    break
                            except IOError as e:
                                logger.error(f"{action} error: {e}")
                    if transfer_dialog.wasCanceled():
                        logger.info("User aborted operation")
                        break
                    completed_items += 1

                self.file_operation_selector.selected_operation().save_state()
                if self.delete_source_checkbox.checkState() == Qt.Checked:
                    for _dir in source_dirs:
                        if not os.listdir(_dir):
                            logger.info(f"Directory {_dir} is empty. Attempting to delete it")
                            # SH OPERATION
                            if not self.dry_run_checkbox.isChecked():
                                os.rmdir(_dir)
                            logger.info(f"Directory {_dir} is empty. Attempting to delete it - Done")
                        else:
                            logger.info(f"Directory {_dir} is not empty, so will not delete it")

    def _create_transfer_dialog(self, action, file_count):
        transfer_dialog = QProgressDialog()
        transfer_dialog.setWindowModality(Qt.WindowModal)
        transfer_dialog.setWindowTitle(action + " Files")
        transfer_dialog.setCancelButtonText("Abort")
        transfer_dialog.setValue(0)
        transfer_dialog.setMaximum(file_count)
        transfer_dialog.setMinimumWidth(550)
        transfer_dialog.setMaximumWidth(self.minimumWidth())
        transfer_dialog.show()
        return transfer_dialog


def main():
    app = QApplication(sys.argv)
    ex = FileWranglerApp()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
