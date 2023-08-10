from enum import Enum

from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QComboBox,
                             QVBoxLayout, QToolBar, QSizePolicy, QMessageBox, QLineEdit, QGroupBox, QDialog,
                             QDialogButtonBox, QHBoxLayout, QWidget)

import CommonUtils
import MediaLib
from CustomUI import FileChooserListBox, CheckComboBox
from MediaLib.runtime.library import LibraryManagement
from MediaLib.runtime.library.Domain import LibraryType, Library


class Action(Enum):
    Add = "Add"
    Refresh = "Refresh"
    Configure = "Configure"
    Delete = "Delete"
    Select = "Select"
    Search = "Search"


class LibraryEditorDialog(QDialog):
    def __init__(self, library=None):
        super().__init__()
        self.library_name_text = QLineEdit()
        self.library_name_text.setPlaceholderText("Library Name")
        self.library_type_selector = CheckComboBox(LibraryType.__iter__(), "Library Types")
        self.dir_chooser = FileChooserListBox(cue="Select directory", dirs_only=True)
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        self.library = library
        self._init_ui()
        self.set_library(self.library)

    def set_library(self, library):
        self.library = library
        if self.library is not None:
            self.library_name_text.setText(self.library.name)
            self.library_name_text.setEnabled(False)
            for t in self.library.types:
                self.library_type_selector.set_item_checked(t)
            self.dir_chooser.add_items(self.library.dirs)
            self.buttons.button(QDialogButtonBox.Ok).setText("Update")
            self.setWindowTitle("Configure Library")

    def get_library(self):
        self.library = Library(
            name=self.library_name_text.text().strip(),
            types=[LibraryType[t] for t in self.library_type_selector.checked_items()],
            dirs=self.dir_chooser.get_items()
        )
        return self.library

    def validate_library(self):
        if self.library is None:
            existing_libs = [x.name for x in LibraryManagement.get_all_libraries()]
        else:
            existing_libs = []
        errors = ""
        if not self.library_name_text.text():
            errors = "Please enter a name for your library\n"
        elif self.library_name_text.text() in existing_libs:
            errors = "A library with this name already exists\n"
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
        lib_name.addWidget(self.library_name_text)

        lib_type = QHBoxLayout()
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

        self.buttons.button(QDialogButtonBox.Ok).setText("Create")
        layout.addWidget(self.buttons)
        self.buttons.accepted.connect(self.validate_library)
        self.buttons.rejected.connect(self.reject)

        self.setLayout(layout)
        self.setWindowTitle("Add New Library")


class MediaLibToolbar(QToolBar):
    library_action = pyqtSignal(Action, 'PyQt_PyObject')

    def __init__(self):
        super(MediaLibToolbar, self).__init__()

        self.add_action = \
            CommonUtils.create_action(self, Action.Add.name,
                                      self.menu_action, icon=QIcon.fromTheme("list-add"))
        self.refresh_action = \
            CommonUtils.create_action(self, Action.Refresh.name,
                                      self.menu_action, icon=QIcon.fromTheme("view-refresh"))
        self.edit_action = \
            CommonUtils.create_action(self, Action.Configure.name,
                                      self.menu_action, icon=QIcon.fromTheme("preferences-system"))
        self.delete_action = \
            CommonUtils.create_action(self, Action.Delete.name,
                                      self.menu_action, icon=QIcon.fromTheme("list-remove"))

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search...")
        self.search.textChanged.connect(self.search_text_change)

        self.library = None
        self.library_details = QComboBox()
        self.library_details.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.library_details.currentIndexChanged.connect(self.library_changed)

        self.addWidget(self.library_details)
        self.addAction(self.edit_action)
        self.addAction(self.refresh_action)
        self.addAction(self.delete_action)
        self.addAction(self.add_action)
        self.addSeparator()
        dummy = QWidget()
        dummy.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.addWidget(dummy)
        self.addWidget(self.search)
        self.refresh_library_list()
        self.setIconSize(QSize(24, 24))

    def search_text_change(self):
        text = self.search.text()
        if text != "" and self.library is not None:
            self.library_action.emit(Action.Search, self.search.text())

    def menu_action(self, menu_item):
        action = Action[menu_item]
        match action:
            case Action.Add:
                editor = LibraryEditorDialog()
                if editor.exec() == QDialog.Accepted:
                    self.library_action.emit(Action.Add, editor.get_library())
            case Action.Refresh if self.library is not None:
                self.library_action.emit(Action.Refresh, self.library)
            case Action.Delete if self.library is not None:
                self.library_action.emit(Action.Delete, self.library)
            case Action.Configure if self.library is not None:
                editor = LibraryEditorDialog(self.library)
                if editor.exec() == QDialog.Accepted:
                    self.library_action.emit(Action.Refresh, editor.get_library())
            case _:
                MediaLib.logger.error(f"Unable to process action {menu_item}")

    def library_changed(self, index):
        self.library = self.library_details.itemData(index)
        self.library_details.setToolTip(f"{self.library.name} "
                                        f"created on {self.library.created}, last updated {self.library.updated}")
        self.library_action.emit(Action.Select, self.library)

    def refresh_library_list(self):
        libraries = LibraryManagement.get_all_libraries()
        self.library_details.clear()
        for library in libraries:
            self.library_details.addItem(library.name, library)

