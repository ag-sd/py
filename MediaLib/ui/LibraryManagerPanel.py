from PyQt5.QtCore import QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QComboBox,
                             QDockWidget,
                             QVBoxLayout, QTreeView, QToolBar, QAction, QSizePolicy)
from PyQt5.QtWidgets import (QWidget, QLabel, QHBoxLayout)

from MediaLib.runtime.library import LibraryManagement


class LibraryManagerPanel(QDockWidget):
    def __init__(self):
        super().__init__()
        self.lib_selector = QComboBox()
        self.libraries = self._setup_libraries(self.lib_selector)
        self.lib_selector.currentIndexChanged.connect(self._lib_changed)
        self.info_ico_lbl = QLabel("ico")
        self.info_lbl = QLabel("Library Information")
        self.info_lbl.setStyleSheet('font-size: 8pt;')

        self.toolbar = QToolBar()
        self.refresh_action = self._create_action(
            "Refresh/Rescan this Library", QIcon.fromTheme("view-refresh"), self.refresh)
        self.edit_action = self._create_action(
            "Configure this Library", QIcon.fromTheme("preferences-system"), self.refresh)
        self.delete_action = self._create_action(
            "Delete this Library", QIcon.fromTheme("list-remove"), self.refresh)
        self.add_action = self._create_action(
            "Add a new Library", QIcon.fromTheme("list-add"), self.refresh)

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
        layout.addStretch(1)
        container = QWidget()
        container.setLayout(layout)
        self.setFeatures(QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetClosable)
        self.setWidget(container)
        self.setWindowTitle("Library Manager")
        if self.lib_selector.count() > 0:
            self._lib_changed()

    def refresh(self):
        lib = self.libraries[self.lib_selector.currentText()]
        LibraryManagement.refresh_library(lib)
        pass

    def _lib_changed(self):
        library = self.libraries[self.lib_selector.currentText()]
        info_ico = QIcon.fromTheme(LibraryManagement.Library_Types[library["type"]]["icon"])
        self.info_ico_lbl.setPixmap(info_ico.pixmap(28, 28))
        updated = 'Not updated'
        if library.__contains__('updated'):
            updated = f"Last updated on {library['updated']}"
        dir_count = len(library['dirs'])
        lib_dir_details = f"{dir_count} directories"
        if dir_count == 1:
            lib_dir_details = f"{dir_count} directory"
        self.info_lbl.setText(f"Created on {library['created']}<br>{updated}<br>{lib_dir_details}")

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

    @staticmethod
    def _create_action(tooltip, icon, func):
        action = QAction("")
        action.setToolTip(tooltip)
        action.setIcon(icon)
        action.triggered.connect(func)
        return action
