from os import path

from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import QTableView, QAbstractItemView

from Imageplay.model.FileItemModel import FileItemModel


class PlayList(QTableView):
    file_drop_event = pyqtSignal('PyQt_PyObject')
    image_change_event = pyqtSignal('PyQt_PyObject')

    def __init__(self):
        super().__init__()
        self.initUI()

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.time_changed)
        self.currentFileIndex = 0

    def initUI(self):
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        # stylesheet = "QHeaderView::section{" \
        #              "border-top:0px solid #D8D8D8;" \
        #              "border-left:0px solid #D8D8D8;" \
        #              "border-right:1px solid #D8D8D8;" \
        #              "border-bottom: 1px solid #D8D8D8;" \
        #              "padding:4px;" \
        #              "}"
        # self.horizontalHeader().setStyleSheet(stylesheet)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.verticalHeader().hide()
        self.horizontalHeader().setHighlightSections(False)
        self.setModel(FileItemModel())
        self.horizontalHeader().setStretchLastSection(True)
        self.file_drop_event.connect(self.files_added)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls:
            event.setDropAction(Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls:
            self.file_drop_event.emit(event.mimeData().urls())
        else:
            event.ignore()

    def files_added(self, file_urls):
        item_model = FileItemModel()
        for file in file_urls:
            if file.isLocalFile():
                _dir, file = path.split(file.path())
                # TODO-Supported files only
                item_model.append_row(_dir, file)
        self.setModel(item_model)
        self.resizeColumnsToContents()
        self.resizeRowsToContents()
        self.horizontalHeader().setStretchLastSection(True)
        if item_model.rowCount(self):
            self.timer.start(1000)
            self.currentFileIndex = 0

    def time_changed(self):
        index = self.currentFileIndex
        if index >= self.model().rowCount(self):
            # TODO-Loop
            print("STOP")
            self.timer.stop()
        else:
            # TODO-Shuffle
            file = path.join(self.model().index(index, 0).data(), self.model().index(index, 1).data())
            self.image_change_event.emit(file)
        self.currentFileIndex = self.currentFileIndex + 1

