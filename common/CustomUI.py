import os
import sys
from os import path

from PyQt5.QtCore import (QDir, Qt, QUrl, QParallelAnimationGroup, QPropertyAnimation, QAbstractAnimation, pyqtSignal)
from PyQt5.QtGui import QDropEvent, QPalette, QDragLeaveEvent
from PyQt5.QtWidgets import \
    (QWidget,
     QLabel,
     QLineEdit,
     QFileDialog,
     QPushButton,
     QHBoxLayout,
     QApplication, QVBoxLayout, QListWidget, QListWidgetItem, QAbstractItemView, QScrollArea, QFrame, QToolButton,
     QSizePolicy)


class FileChooserTextBox(QWidget):

    file_selection_changed = pyqtSignal(str)

    def __init__(self, label, cue, _dir, lbl_align_right=False, initial_selection=''):
        super(FileChooserTextBox, self).__init__()
        self.label = label
        self.cue = cue
        self.dir = _dir
        if path.exists(initial_selection):
            self.selection = initial_selection
        else:
            self.selection = ""
        self.text = QLineEdit()
        self.lbl_align_right = lbl_align_right
        self.initUI()

    def initUI(self):
        self.text.setReadOnly(True)
        self.text.setObjectName("txtAddress")
        button = QPushButton("...")
        button.clicked.connect(self.browse_for_item)
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

    def browse_for_item(self):
        if self.text.text() != '' and path.exists(self.text.text()):
            initial_dir = path.dirname(self.text.text())
        else:
            initial_dir = path.expanduser("~")

        if self.dir:
            file = QFileDialog.getExistingDirectory(self, self.cue, initial_dir, QFileDialog.ShowDirsOnly)
        else:
            file, _filter = QFileDialog.getOpenFileName(self, self.cue, initial_dir)

        self.selection = QDir.toNativeSeparators(file)
        self.text.setText(self.selection)
        self.file_selection_changed.emit(self.selection)

    def getSelection(self):
        return self.selection

    def setSelection(self, selection):
        if path.exists(selection):
            self.selection = selection
            self.text.setText(selection)


class DropZone(QLabel):
    files_dropped_event = pyqtSignal('PyQt_PyObject')

    def __init__(self):
        super().__init__()
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)
        self.setText("Drag and drop files here")
        self.setAlignment(Qt.AlignCenter)
        self.setAcceptDrops(True)
        self.setAutoFillBackground(True)
        self.setMinimumWidth(300)
        self.dropped_files = None

    def dragEnterEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
            self.setBackgroundRole(QPalette.Light)
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            self.dropped_files = event.mimeData().urls()
            self.files_dropped_event.emit(self.dropped_files)
        self.setBackgroundRole(QPalette.Window)
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)

    def dragLeaveEvent(self, event: QDragLeaveEvent):
        self.setBackgroundRole(QPalette.Window)
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)


class ListWidgetDragDrop(QListWidget):
    def __init__(self, dirs_only, items=None):
        super().__init__()
        if items is not None:
            for item in items:
                self.addItem(item)

        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        # self.viewport().setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.dirs_only = dirs_only

    def update_list(self, items):
        self.clear()
        if items is not None:
            for item in items:
                self.addItem(item)

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
        self.list_box = ListWidgetDragDrop(dirs_only)
        self._init_ui()

    def add_items(self, paths):
        for path in paths:
            item = QListWidgetItem(path)
            self.list_box.addItem(item)

    def _init_ui(self):
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
        if selection != "":
            item = QListWidgetItem(selection)
            self.list_box.addItem(item)

    def _del_items(self):
        items = self.list_box.selectedItems()
        for item in items:
            self.list_box.takeItem(self.list_box.row(item))

    def selection(self):
        for i in range(self.list_box.count()):
            yield self.list_box.item(i).text()

    def get_items(self):
        items = []
        for i in range(self.list_box.count()):
            items.append(self.list_box.item(i).text())
        return items

    def selection_as_qurls(self):
        for i in range(self.list_box.count()):
            yield QUrl.fromLocalFile(self.list_box.item(i).text())


class CollapsibleWidget(QWidget):
    def __init__(self, title="", parent=None, animation_duration=300):
        """
        References:
            # Adapted from c++ version
            http://stackoverflow.com/questions/32476006/how-to-make-an-expandable-collapsable-section-widget-in-qt
        """
        super(CollapsibleWidget, self).__init__(parent)
        self.title = title
        self.toggle_button = QToolButton()
        self.toggle_animation = QParallelAnimationGroup(self)
        self.content_area = QScrollArea()
        self.animation_duration = animation_duration
        self._init_base_ui()

    def _init_base_ui(self):
        self.toggle_button.setStyleSheet("QToolButton { border: none; }")
        self.toggle_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.toggle_button.setArrowType(Qt.RightArrow)
        self.toggle_button.pressed.connect(self.on_pressed)
        self.toggle_button.setText(str(self.title))
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(False)

        self.content_area.setMaximumHeight(0)
        self.content_area.setMinimumHeight(0)
        self.content_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.content_area.setFrameShape(QFrame.NoFrame)

        self.toggle_animation.addAnimation(QPropertyAnimation(self, b"minimumHeight"))
        self.toggle_animation.addAnimation(QPropertyAnimation(self, b"maximumHeight"))
        self.toggle_animation.addAnimation(QPropertyAnimation(self.content_area, b"maximumHeight"))

        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.toggle_button)
        layout.addWidget(self.content_area)

    def on_pressed(self):
        checked = self.toggle_button.isChecked()
        self.toggle_button.setArrowType(Qt.DownArrow if not checked else Qt.RightArrow)
        self.toggle_animation.setDirection(QAbstractAnimation.Forward if not checked else QAbstractAnimation.Backward)
        self.toggle_animation.start()

    def set_content_layout(self, layout):
        initial_layout = self.content_area.layout()
        del initial_layout
        self.content_area.setLayout(layout)
        collapsed_height = (self.sizeHint().height() - self.content_area.maximumHeight())
        content_height = layout.sizeHint().height()
        for i in range(self.toggle_animation.animationCount()):
            animation = self.toggle_animation.animationAt(i)
            animation.setDuration(self.animation_duration)
            animation.setStartValue(collapsed_height)
            animation.setEndValue(collapsed_height + content_height)

        content_animation = self.toggle_animation.animationAt(self.toggle_animation.animationCount() - 1)
        content_animation.setDuration(self.animation_duration)
        content_animation.setStartValue(0)
        content_animation.setEndValue(content_height)

    def set_content_widget(self, widget):
        initial_layout = self.content_area.layout()
        del initial_layout
        self.content_area.setWidget(widget)
        collapsed_height = (self.sizeHint().height() - self.content_area.maximumHeight())
        content_height = widget.sizeHint().height()
        for i in range(self.toggle_animation.animationCount()):
            animation = self.toggle_animation.animationAt(i)
            animation.setDuration(self.animation_duration)
            animation.setStartValue(collapsed_height)
            animation.setEndValue(collapsed_height + content_height)

        content_animation = self.toggle_animation.animationAt(self.toggle_animation.animationCount() - 1)
        content_animation.setDuration(self.animation_duration)
        content_animation.setStartValue(0)
        content_animation.setEndValue(content_height)


class QHLine(QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)


class QVLine(QFrame):
    def __init__(self):
        super(QVLine, self).__init__()
        self.setFrameShape(QFrame.VLine)
        self.setFrameShadow(QFrame.Sunken)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = CollapsibleWidget("Test Widget Fooo", animation_duration=150)
    lay = QVBoxLayout()
    for j in range(8):
        label = QLabel("This is label # {}".format(j))
        label.setAlignment(Qt.AlignCenter)
        lay.addWidget(label)
    w = QWidget()
    w.setLayout(lay)
    ex.set_content_widget(w)
    ex.show()
    sys.exit(app.exec_())
