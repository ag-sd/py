import os

from PyQt5.QtCore import (Qt, pyqtSignal, QMargins)
from PyQt5.QtGui import QIcon, QCursor
from PyQt5.QtWidgets import QTableView, QAbstractItemView, QMenu, QStyledItemDelegate, \
    QStyleOptionProgressBar, QApplication, QStyle

import CommonUtils
from TransCoda.ui.TransCodaSettings import SettingsKeys
from TransCoda.ui import File, TransCodaSettings
from TransCoda.ui.Actions import Action
from TransCoda.ui.File import FileItemModel, Header


class OutputDirectoryNotSet(Exception):
    """Raise when the output folder is not set"""


class EncoderNotSelected(Exception):
    """Raise when the Encoder is not selected"""


class MainPanel(QTableView):

    class ProgressBarDelegate(QStyledItemDelegate):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.style = QApplication.style()
            self.ok = QIcon(os.path.join(os.path.dirname(__file__), "../resource/2714.svg"))

        def paint(self, painter, option, index):
            column_key = self.parent().get_column_key(index.column())
            if column_key == Header.percent_compete:
                item = self.parent().get_items(index=index.row())
                column_value = item.encode_percent
                if not column_value:
                    # If no progress value, just let the system draw the value
                    super().paint(painter, option, index)
                    return
                painter.save()
                if column_value == 100:
                    status_color = File.get_item_color(item)
                    if status_color.is_background_color:
                        painter.fillRect(option.rect, status_color.brush)
                    self.ok.paint(painter, option.rect)
                else:
                    progressbar_options = QStyleOptionProgressBar()
                    progressbar_options.rect = option.rect.marginsRemoved(QMargins(1, 1, 1, 1))
                    progressbar_options.minimum = 0
                    progressbar_options.maximum = 100
                    progressbar_options.textAlignment = Qt.AlignCenter
                    progressbar_options.progress = int(column_value)
                    progressbar_options.text = f"{progressbar_options.progress}%"
                    progressbar_options.textVisible = True
                    self.style.drawControl(QStyle.CE_ProgressBar, progressbar_options, painter)
                painter.restore()
            else:
                super().paint(painter, option, index)

    files_changed_event = pyqtSignal(bool, 'PyQt_PyObject')
    menu_item_event = pyqtSignal(Action, set)

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.verticalHeader().setDefaultSectionSize(self.verticalHeader().fontMetrics().height() + 3)
        self.verticalHeader().hide()
        self.horizontalHeader().setHighlightSections(False)
        self.horizontalHeader().setSectionsMovable(True)
        self.horizontalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.horizontalHeader().customContextMenuRequested.connect(self.get_header_context_menu)
        self.horizontalHeader().setSectionsClickable(True)
        self.setSortingEnabled(True)
        self.file_model = None
        self.clear_table()
        self.menu = self.create_context_menu()
        self.progressbarDelegate = MainPanel.ProgressBarDelegate(parent=self)
        self.setItemDelegate(self.progressbarDelegate)
        TransCodaSettings.settings.settings_change_event.connect(self.settings_changed)

    def create_context_menu(self):
        menu = QMenu()
        # menu.addAction(CommonUtils.create_action(self, "Open", self.menu_item_selected,
        #                                          icon=QIcon.fromTheme("document-open")))
        menu.addAction(CommonUtils.create_action(self, Action.DEL_FILE.value, self.menu_item_selected,
                                                 icon=QIcon.fromTheme("list-remove")))
        menu.addAction(CommonUtils.create_action(self, Action.DEL_ALL.value, self.menu_item_selected,
                                                 icon=QIcon.fromTheme("edit-delete")))
        menu.addSeparator()
        menu.addAction(CommonUtils.create_action(self, Action.ENCODE.value, self.menu_item_selected,
                                                 icon=QIcon.fromTheme("media-playback-start")))
        submenu = menu.addMenu("Change Status")
        submenu.addAction(CommonUtils.create_action(self, Action.CHANGE_STATUS_SUCCESS.value, self.menu_item_selected,
                                                    icon=QIcon.fromTheme("face-smile")))
        submenu.addAction(CommonUtils.create_action(self, Action.CHANGE_STATUS_READY.value, self.menu_item_selected,
                                                    icon=QIcon.fromTheme("face-plain")))
        return menu

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
            self.files_changed_event.emit(True, event.mimeData().urls())
        else:
            event.ignore()

    def contextMenuEvent(self, event):
        if self.selectedIndexes() and self.selectedIndexes()[0].row() >= 0:
            self.menu.exec(QCursor.pos())

    def add_files(self, files):
        total_added = self.file_model.add_rows(files)
        self.file_model.layoutChanged.emit()
        self.adjust_columns()
        return total_added

    def remove_files(self, indices):
        self.file_model.remove_rows(indices)
        self.files_changed_event.emit(False, len(indices))

    def clear_table(self):
        self.file_model = FileItemModel()
        self.setModel(self.file_model)
        self.files_changed_event.emit(False, 0)

    def adjust_columns(self):
        for i in range(self.file_model.columnCount(self)):
            self.resizeColumnToContents(i)

    def row_count(self):
        return self.file_model.rowCount()

    def get_items(self, index=None):
        return self.file_model.get_items(index)

    def set_items(self, items):
        self.file_model.set_items(items)
        self.adjust_columns()
        self.files_changed_event.emit(False, 0)

    def update_items(self, file_data):
        self.file_model.update_items(file_data)
        self.adjust_columns()

    def update_item_status(self, item_indices, new_status):
        for index in item_indices:
            self.file_model.update_status(index, new_status)

    def settings_changed(self, setting, _):
        if setting == SettingsKeys.encoder_path:
            self.file_model.encoder_changed()
        elif setting == SettingsKeys.output_dir:
            self.file_model.output_dir_changed()
        elif setting == SettingsKeys.preserve_dir:
            self.file_model.output_dir_changed()

    def menu_item_selected(self, item_value):
        rows = set()
        for selected in self.selectedIndexes():
            rows.add(selected.row())
        if len(rows) > 0:
            self.menu_item_event.emit(Action(item_value), rows)

    def get_header_context_menu(self, _):
        # Get Available Headers
        available = sorted(Header.__headers__, key=lambda key: key.display_name)
        # Get Selected Headers
        selected = self.file_model.get_columns()
        # Build Menu
        menu = QMenu()
        for column in available:
            checked = selected.__contains__(column)
            menu.addAction(CommonUtils.create_action(self, column.display_name,
                                                     self.column_header_selection, checked=checked))
        menu.exec(QCursor.pos())

    def column_header_selection(self, item_name):
        for index, column in enumerate(self.file_model.get_columns()):
            if column.display_name == item_name:
                # Remove
                self.file_model.remove_column(column)
                return
        # if column was not found, add it
        for column in Header:
            if column.display_name == item_name:
                self.file_model.add_column(column)
                return

    def get_column_key(self, index):
        return self.file_model.get_column_key(index)
