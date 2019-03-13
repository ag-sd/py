import os
import sys

from PyQt5.QtCore import (QDir, Qt, QUrl)
from PyQt5.QtWidgets import \
    (QWidget,
     QLabel,
     QLineEdit,
     QFileDialog,
     QPushButton,
     QHBoxLayout,
     QApplication, QVBoxLayout, QListWidget, QListWidgetItem, QAbstractItemView)


class FileChooserTextBox(QWidget):

    def __init__(self, label, cue, _dir, lbl_align_right=False):
        super().__init__()
        self.label = label
        self.cue = cue
        self.dir = _dir
        self.selection = ''
        self.text = QLineEdit()
        self.lbl_align_right = lbl_align_right
        self.initUI()

    def initUI(self):
        self.text.setReadOnly(True)
        self.text.setObjectName("txtAddress")
        button = QPushButton("...")
        button.clicked.connect(lambda: self.browse_for_item(self.text))
        width = button.fontMetrics().boundingRect("...").width() + 12
        button.setMaximumWidth(width)
        button.setMaximumHeight(self.text.height())
        layout = QHBoxLayout()
        if not self.lbl_align_right:
            layout.addWidget(QLabel(self.label))
        layout.addWidget(self.text)
        layout.addWidget(button)
        if self.lbl_align_right:
            layout.addWidget(QLabel(self.label))
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def browse_for_item(self, text):
        if self.dir:
            file = QFileDialog.getExistingDirectory(caption=self.cue)
        else:
            file, _filter = QFileDialog.getOpenFileName(caption=self.cue)

        self.selection = QDir.toNativeSeparators(file)
        text.setText(self.selection)

    def getSelection(self):
        return self.selection

    def setSelection(self, selection):
        self.selection = selection
        self.text.setText(selection)


class _ListWidgetDragDrop(QListWidget):
    def __init__(self, dirs_only):
        super().__init__()
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        # self.viewport().setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.dirs_only = dirs_only

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls and self.isValidFiles(event.mimeData().urls()):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls and self.isValidFiles(event.mimeData().urls()):
            event.setDropAction(Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls and self.isValidFiles(event.mimeData().urls()):
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    lf = url.toLocalFile()
                    if os.path.isdir(lf) and self.dirs_only:
                        self.addItem(lf)
                    elif os.path.isfile(lf) and not self.dirs_only:
                        self.addItem(lf)
        else:
            event.ignore()

    def isValidFiles(self, urls):
        for url in urls:
            if url.isLocalFile():
                lf = url.toLocalFile()
                # One directory was found
                if os.path.isdir(lf) and self.dirs_only:
                    return True
                elif os.path.isfile(lf) and not self.dirs_only:
                    return True
        return False


class FileChooserListBox(QWidget):

    def __init__(self, cue, dirs_only):
        super().__init__()
        self.cue = cue
        self.dirs_only = dirs_only
        self.add_button = QPushButton("+")
        self.del_button = QPushButton("-")
        self.list_box = _ListWidgetDragDrop(dirs_only)
        self._initUI()

    def _initUI(self):
        self.add_button.clicked.connect(self._add_items)
        self.del_button.clicked.connect(self._del_items)
        b_layout = QHBoxLayout()
        b_layout.setContentsMargins(0, 0, 0, 0)
        b_layout.addWidget(QWidget(), 1)
        b_layout.addWidget(self.add_button)
        b_layout.addWidget(self.del_button)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.list_box)
        main_layout.addLayout(b_layout)
        self.setLayout(main_layout)

    def _add_items(self):
        if self.dirs_only:
            file = QFileDialog.getExistingDirectory(self, caption=self.cue)
        else:
            file, _filter = QFileDialog.getOpenFileName(self, caption=self.cue)

        selection = QDir.toNativeSeparators(file)
        if selection is not "":
            item = QListWidgetItem(selection)
            self.list_box.addItem(item)

    def _del_items(self):
        items = self.list_box.selectedItems()
        for item in items:
            self.list_box.takeItem(self.list_box.row(item))

    def selection(self):
        for i in range(self.list_box.count()):
            yield self.list_box.item(i).text()

    def selection_as_qurls(self):
        for i in range(self.list_box.count()):
            yield QUrl.fromLocalFile(self.list_box.item(i).text())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = FileChooserListBox("cue", True)
    ex.show()
    sys.exit(app.exec_())
