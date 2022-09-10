import os

from PyQt5.QtCore import Qt, QMimeDatabase, QSize
from PyQt5.QtGui import QIcon, QBrush, QColor
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QComboBox

from FileWrangler import logger, FileWranglerCore
from FileWrangler.FileWranglerCore import DisplayKeys


class FileOperationSelector(QComboBox):

    SEP = FileWranglerCore.DEFAULT_SPLITTER

    def __init__(self, file_operations: dict):
        super().__init__()
        self.display_texts = []
        self.file_operations = file_operations
        for op in file_operations.values():
            disp_text = f"{op.name}{self.SEP}{op.description}"
            self.display_texts.append(disp_text)
        self.addItems(self.display_texts)

    def selected_operation(self):
        return self.operation_at(self.currentIndex())

    def operation_at(self, index):
        text = self.itemText(index)
        tokens = text.split(self.SEP)
        if tokens[0] not in self.file_operations:
            raise KeyError(f"{tokens[0]} was not found.")
        return self.file_operations[tokens[0]]

    # def paintEvent(self, event):
    #     style = QApplication.style()
    #     opt = QStyleOptionComboBox()
    #     opt.rect = self.rect()
    #     self.initStyleOption(opt)
    #     painter = QPainter(self)
    #     painter.save()
    #     style.drawComplexControl(QStyle.CC_ComboBox, opt, painter)
    #     doc = QTextDocument()
    #     doc.setHtml(self.currentText() + "<i>This should be italicized</i>")
    #     opt.currentText = ""
    #     style.drawControl(QStyle.CE_ComboBoxLabel, opt, painter)
    #     rect = QRectF(0, 0, opt.rect.width(), opt.rect.height())
    #     doc.drawContents(painter, rect)
    #     painter.restore()


class MainTable(QTableWidget):
    _error_brush = QBrush(QColor(220, 20, 60, 75))
    _mime_database = QMimeDatabase()

    def __init__(self):
        super().__init__()
        self._reset()
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.verticalHeader().setDefaultSectionSize(self.verticalHeader().fontMetrics().height() + 3)
        self.verticalHeader().hide()
        self.horizontalHeader().setHighlightSections(False)
        self.horizontalHeader().setSectionsMovable(True)
        self.horizontalHeader().setSectionsClickable(True)
        self.setSortingEnabled(True)
        self.reset()
        self.model = None

    def is_selected(self, source_file):
        matches = self.findItems(source_file, Qt.MatchExactly)
        if len(matches):
            return matches[0].checkState() == Qt.Checked
        else:
            return False

    def remove_file(self, source_file):
        matches = self.findItems(source_file, Qt.MatchExactly)
        if len(matches):
            self.removeRow(matches[0].row())

    def set_model(self, file_items):
        self._reset()
        self.setRowCount(len(file_items))
        self.setSortingEnabled(False)
        for i in range(0, len(file_items)):
            source = file_items[i][DisplayKeys.source]
            target = file_items[i][DisplayKeys.target]
            source_item = QTableWidgetItem(source)
            target_item = QTableWidgetItem(target)
            mime = MainTable._mime_database.mimeTypesForFileName(source)
            if len(mime):
                source_item.setIcon(QIcon.fromTheme(mime[0].iconName()))
            else:
                logger.error("Unable to determine mime type for " + source)
                source_item.setIcon(QIcon.fromTheme("text-x-generic"))
            source_item.setCheckState(Qt.Checked)
            _, file_name = os.path.split(target)
            if file_name.startswith(FileWranglerCore.UNKNOWN_KEY):
                target_item.setBackground(MainTable._error_brush)
                source_item.setBackground(MainTable._error_brush)
                source_item.setCheckState(Qt.Unchecked)
            self.setItem(i, 0, source_item)
            self.setItem(i, 1, target_item)
        self.setSortingEnabled(True)
        self.model = file_items
        # Hack to make first column resize to contents and also be interactive
        first_column_width = self.horizontalHeader().sectionSize(0)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        self.setColumnWidth(0, first_column_width)

    def _reset(self):
        self.clear()
        self.setColumnCount(2)
        self.setHorizontalHeaderItem(0, QTableWidgetItem("Source File"))
        self.setHorizontalHeaderItem(1, QTableWidgetItem("Destination File"))
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)