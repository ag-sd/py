
from MediaLib.runtime.library import LibraryManagement

from PyQt5.QtWidgets import (QComboBox,
                             QDockWidget,
                             QVBoxLayout)

class LibraryManagerPanel(QDockWidget):
    class LibrarySelector(QComboBox):
        def __init__(self):
            super().__init__()
            self.libraries = LibraryManagement.get_all_libraries()
            for lib_type in self.libraries:
                for lib_name in self.libraries[lib_type]:
                    self.addItem(f"[{lib_type}] \t {lib_name['name']}")

    def __init__(self):
        super().__init__()
        self.library_selector = self.LibrarySelector()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(self.library_selector)
        # layout.addStretch(1)
        self.setLayout(layout)

