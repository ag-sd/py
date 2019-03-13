from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTableView, QAbstractItemView

import Imageplay
from Settings import SettingsKeys
from common.CommonUtils import FileScanner


class PlayList(QTableView):

    def __init__(self, model):
        super().__init__()
        self.setModel(model)
        model.files_update_event.connect(self.adjust_view)
        self.initUI()

    def initUI(self):
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.verticalHeader().hide()
        self.horizontalHeader().setHighlightSections(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.doubleClicked.connect(self.double_click_event)

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
            self.files_added(event.mimeData().urls())
        else:
            event.ignore()

    def double_click_event(self, qModelIndex):
        self.model().next(
            Imageplay.settings.get_setting("shuffle", False),
            qModelIndex.row()
        )

    def files_added(self, file_urls):
        self.model().add_files(
            FileScanner(file_urls,
                        Imageplay.settings.get_setting(SettingsKeys.recurse_subdirs, False),
                        Imageplay.supported_formats).files)
        self.adjust_view()

    def adjust_view(self):
        self.resizeColumnToContents(0)
        self.resizeRowsToContents()