import sys
import time

from PyQt5.QtCore import QSize, Qt, QRunnable, QThreadPool, QTimer
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QComboBox,
                             QDockWidget,
                             QVBoxLayout, QToolBar, QSizePolicy, QMessageBox, QLineEdit, QGroupBox, QDialog,
                             QDialogButtonBox, QWidget, QLabel, QHBoxLayout, QTreeView, QApplication, QListWidget,
                             QListWidgetItem, QProgressBar)

import CommonUtils
from CustomUI import FileChooserListBox, CollapsibleWidget
from MediaLib.runtime.library import LibraryManagement


class LibraryGroupingManager(CollapsibleWidget):
    def __init__(self):
        super().__init__("Library Tree Group Manager")
        self.source = QListWidget()
        self.target = QListWidget()
        self.action_toolbar = QToolBar()
        self.add_action = CommonUtils.create_toolbar_action(
            "Add selected key to grouping", QIcon.fromTheme("media-skip-forward"), self.add)
        self.sub_action = CommonUtils.create_toolbar_action(
            "Remove selected key to grouping", QIcon.fromTheme("media-skip-backward"), self.sub)
        self.reset_action = CommonUtils.create_toolbar_action(
            "Reset to library type default", QIcon.fromTheme("document-revert"), self.reset)
        self.apply_action = CommonUtils.create_toolbar_action(
            "Apply this view", QIcon.fromTheme("document-save"), self.save)
        self.icon = QIcon.fromTheme("folder")
        self._init_ui()

    def _init_ui(self):
        self.action_toolbar.setOrientation(Qt.Vertical)
        dummy = QWidget()
        dummy.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.action_toolbar.addWidget(dummy)
        self.action_toolbar.addActions([self.add_action, self.sub_action, self.reset_action, self.apply_action])
        self.action_toolbar.setContentsMargins(0, 0, 0, 0)
        q_size = QSize(16, 16)
        self.action_toolbar.setIconSize(q_size)
        self.source.setIconSize(q_size)
        self.source.setMaximumHeight(120)
        self.target.setIconSize(q_size)
        self.target.setMaximumHeight(120)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.source)
        layout.addWidget(self.action_toolbar)
        layout.addWidget(self.target)
        self.set_content_layout(layout)

    def update_grouping(self, grouping):
        self.source.clear()
        for key in grouping:
            item = QListWidgetItem(self.icon, key)
            self.source.addItem(item)

    def add(self):
        self.swap_items(self.source, self.target)

    def sub(self):
        self.swap_items(self.target, self.source)

    def save(self):
        pass

    def reset(self):
        pass

    @staticmethod
    def swap_items(source, target):
        list_items = source.selectedItems()
        if not list_items:
            return
        for item in list_items:
            source.takeItem(source.row(item))
            target.addItem(item)


class LibraryTaskManager(QWidget):
    class Runner(QRunnable):
        def __init__(self, function, args):
            super().__init__()
            self.function = function
            self.args = args

        def run(self):
            self.function(*self.args)

    def __init__(self):
        super().__init__()
        self.thread_pool = QThreadPool()
        self.task_combo = QComboBox()
        self.task_combo.currentIndexChanged.connect(self.get_item_status)
        self.progress = QProgressBar()
        self.progress.setMaximum(100)
        self.timer = QTimer()
        q_size = QSize(16, 16)
        self.icon_in_progress = QIcon.fromTheme("media-playback-start")
        self.icon_completed = QIcon.fromTheme("media-playback-stop")
        self.task_combo.setIconSize(q_size)
        self.timer.timeout.connect(self.timeout)
        self.task_lookup = {}
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel("Task Executor"))
        layout.addWidget(self.task_combo)
        layout.addWidget(self.progress)
        self.setLayout(layout)

    def execute(self, function, args):
        runner = self.Runner(function, args)
        runner.setAutoDelete(True)
        self.thread_pool.start(runner)

    def execute_with_progress(self, function, args, task_ref):
        self.execute(function, args)
        self.task_lookup[task_ref[0]] = task_ref[1]
        self.task_combo.addItem(self.icon_in_progress, task_ref[0])
        self.task_combo.setCurrentIndex(self.task_combo.findText(task_ref[0]))

    def get_item_status(self):
        self.timer.start(500)

    def timeout(self):
        task_name = self.task_combo.currentText()
        task_ref = self.task_lookup[task_name]
        print(f"status for {task_ref}")
        status = LibraryManagement.get_task_status(task_ref)
        self.progress.setValue(status['percent_complete'])
        if status['status'] == "COMPLETE":
            self.task_combo.setItemIcon(self.task_combo.findText(task_ref), self.icon_completed)
            self.timer.stop()


class LibraryEditorPanel(QDialog):
    def __init__(self, library=None):
        super().__init__()
        self.library_name_text = QLineEdit()
        self.library_type_selector = QComboBox()
        self.library_type_selector.addItems(LibraryManagement.get_available_library_types())
        self.dir_chooser = FileChooserListBox(cue="FFFFF", dirs_only=True)
        self.library = library
        self._init_ui()
        self._init_library()

    def _init_library(self):
        if self.library is not None:
            self.library_name_text.setText(self.library['name'])
            self.library_name_text.setEnabled(False)
            index = self.library_type_selector.findText(self.library['type'])
            if index != -1:
                self.library_type_selector.setCurrentIndex(index)
            self.library_type_selector.setEnabled(False)
            self.dir_chooser.add_items(self.library['dirs'])
            self.setWindowTitle("Configure Library")

    def get_library(self):
        created = 'Creation in progress...'
        if self.library is not None:
            created = self.library['created']
        return {
            "name": self.library_name_text.text(),
            "type": self.library_type_selector.currentText(),
            "dirs": self.dir_chooser.get_items(),
            "created": created,
        }

    def validate_library(self):
        errors = ""
        if not self.library_name_text.text():
            errors = "Please enter a name for your library\n"
        if not self.library_type_selector.currentText():
            errors = errors + "Please select the library type\n"
        if len(self.dir_chooser.get_items()) == 0:
            errors = errors + "Please choose the directories in your library"
        if errors:
            QMessageBox.critical(self, "Cannot save this library",
                                 f"This library cannot be saved because of the following issues: "
                                 f"\n\n{errors}\n\n"
                                 f"Please correct these issues to proceed")
        else:
            self.accept()

    def _init_ui(self):
        lib_name = QHBoxLayout()
        lib_name.addWidget(QLabel("Library Name:"))
        lib_name.addWidget(self.library_name_text)

        lib_type = QHBoxLayout()
        lib_type.addWidget(QLabel("Library Type:"))
        lib_type.addWidget(self.library_type_selector)

        l1 = QHBoxLayout()
        l1.addWidget(self.dir_chooser)
        l1.setContentsMargins(0, 0, 0, 0)
        gb1 = QGroupBox("Directories to add to Library")
        gb1.setLayout(l1)

        layout = QVBoxLayout()
        layout.addLayout(lib_name)
        layout.addLayout(lib_type)
        layout.addWidget(gb1)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
                                   Qt.Horizontal, self)
        layout.addWidget(buttons)
        buttons.accepted.connect(self.validate_library)
        buttons.rejected.connect(self.reject)

        self.setLayout(layout)
        self.setWindowTitle("Add New Library")


class LibraryManagerPanel(QDockWidget):
    def __init__(self, task_executor):
        super().__init__()
        self.lib_selector = QComboBox()
        self.libraries = self._setup_libraries(self.lib_selector)
        self.lib_selector.currentIndexChanged.connect(self._lib_changed)
        self.info_ico_lbl = QLabel("ico")
        self.info_lbl = QLabel("Library Information")
        self.info_lbl.setStyleSheet('font-size: 8pt;')
        self.task_executor = task_executor
        self.group_manager = LibraryGroupingManager()
        self.treeView = QTreeView()

        self.toolbar = QToolBar()
        self.refresh_action = CommonUtils.create_toolbar_action(
            "Refresh/Rescan this Library", QIcon.fromTheme("view-refresh"), self.refresh)
        self.edit_action = CommonUtils.create_toolbar_action(
            "Configure this Library", QIcon.fromTheme("preferences-system"), self.edit)
        self.delete_action = CommonUtils.create_toolbar_action(
            "Delete this Library", QIcon.fromTheme("list-remove"), self.delete)
        self.add_action = CommonUtils.create_toolbar_action(
            "Add a new Library", QIcon.fromTheme("list-add"), self.add)

        self._init_ui()

    def _init_ui(self):
        h_layout = QHBoxLayout()
        h_layout.addWidget(self.info_ico_lbl)
        h_layout.addWidget(self.lib_selector, 1)
        dummy = QWidget()
        dummy.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.toolbar.addWidget(dummy)
        self.toolbar.addActions([self.refresh_action, self.edit_action, self.delete_action, self.add_action])
        self.toolbar.setContentsMargins(0, 0, 0, 0)
        self.toolbar.setIconSize(QSize(16, 16))

        layout = QVBoxLayout()
        layout.setContentsMargins(5, 0, 0, 0)
        layout.setMenuBar(self.toolbar)
        layout.addLayout(h_layout)
        layout.addWidget(self.info_lbl)
        layout.addWidget(self.group_manager)
        layout.addWidget(self.treeView, 1)
        container = QWidget()
        container.setLayout(layout)
        self.setFeatures(QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetClosable)
        self.setWidget(container)
        self.setWindowTitle("Library Manager")
        if self.lib_selector.count() > 0:
            self._lib_changed()

    def refresh(self):
        lib = self.libraries[self.lib_selector.currentText()]
        task_name = f"Refreshing {lib['name']}"
        task_id = f"{time.time()} {task_name}"
        self.task_executor.execute_with_progress(LibraryManagement.refresh_library, (lib, task_id),
                                                 (task_name, task_id))

    def delete(self):
        lib_name = self.lib_selector.currentText()
        choice = QMessageBox.question(self, "Confirm Library Deletion",
                                      f"Are you sure you want to delete {lib_name}. "
                                      f"Please note this action cannot be undone")
        if choice == QMessageBox.Yes:
            lib = self.libraries.pop(lib_name)
            self.task_executor.execute(LibraryManagement.delete_library, (lib,))
            self.lib_selector.removeItem(self.lib_selector.currentIndex())

    def edit(self):
        library = self.libraries[self.lib_selector.currentText()]
        dialog = LibraryEditorPanel(library)
        result = dialog.exec()
        if result == QDialog.Accepted:
            self.libraries.pop(self.lib_selector.currentText())
            lib_new = dialog.get_library()
            self.libraries[self.lib_selector.currentText()] = lib_new
            task_name = f"Adding {lib_new['name']}"
            task_id = f"{time.time()} {task_name}"
            self.task_executor.execute(LibraryManagement.update_library, (lib_new,))
            self._lib_changed()

    def add(self):
        dialog = LibraryEditorPanel()
        result = dialog.exec()
        if result == QDialog.Accepted:
            lib = dialog.get_library()
            self.libraries[lib['name']] = lib
            self.lib_selector.addItem(lib['name'])
            task_name = f"Adding {lib['name']}"
            task_id = f"{time.time()} {task_name}"
            self.task_executor.execute_with_progress(LibraryManagement.create_library,
                                                     (lib['name'], lib['type'], lib['dirs'], None, task_id),
                                                     (task_name, task_id))

    def _lib_changed(self):
        library = self.libraries[self.lib_selector.currentText()]
        info_ico = QIcon.fromTheme(LibraryManagement.Library_Types[library["type"]]["icon"])
        self.info_ico_lbl.setPixmap(info_ico.pixmap(28, 28))
        updated = 'Not updated'
        if library.__contains__('updated'):
            updated = f"Updated on {library['updated']}"
        dir_count = len(library['dirs'])
        lib_dir_details = f"{dir_count} directories"
        if dir_count == 1:
            lib_dir_details = f"{dir_count} directory"
        self.info_lbl.setText(f"Created on {library['created']}<br>{updated}<br>{lib_dir_details}")
        self.group_manager.update_grouping(LibraryManagement.get_group_keys(library["type"]))

    @staticmethod
    def _setup_libraries(lib_combo_selector):
        libraries = LibraryManagement.get_all_libraries()
        lib_lookup = {}
        for lib_type in libraries:
            for lib in libraries[lib_type]:
                key = f"[{lib_type}] {lib['name']}"
                lib_lookup[key] = lib
                lib_combo_selector.addItem(key)
        return lib_lookup


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = LibraryGroupingManager()
    ex.update_grouping(["apple", "ball", "fish", "cat"])
    ex.show()
    sys.exit(app.exec_())