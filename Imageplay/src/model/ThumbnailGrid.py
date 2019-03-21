import time, os

from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPalette, QPixmap, QPaintEvent, QPainter, QFont
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QGridLayout, QScrollArea, QVBoxLayout


class Thumbnail(QWidget):
    _base_dimensions = 96
    _padding_left = 0
    _padding_top = 0
    _text_padding = 4
    _text_scaler = 0.08
    _text_weight = 60
    _padding = _padding_left + _padding_top

    # TODO Add Pixmap Cache

    def __init__(self, image_file: str):
        super().__init__()
        self.image_size = self._base_dimensions
        self.setFont(QFont("sans", round(self.image_size * self._text_scaler, 0), self._text_weight))
        self.image_file = image_file
        self.base_pixmap = QPixmap(image_file)
        self.file_size = f"{round(os.path.getsize(image_file) / 1024, 2)}Kb."
        self.m_time = time.strftime("%d %b %Y", time.gmtime(os.path.getmtime(image_file)))
        self.pixmap = self.base_pixmap.scaled(self.image_size, self.image_size, Qt.KeepAspectRatio)
        self.setMaximumSize(QSize(self.pixmap.width() + self._padding,
                                  self.pixmap.height() + self._padding))
        self.setMinimumSize(QSize(self.pixmap.width() + self._padding,
                                  self.pixmap.height() + self._padding))
        self.setContentsMargins(0, 0, 0, 0)
        self.details_view = False

    def sizeHint(self):
        return QSize(self.pixmap.width() + self._padding, self.pixmap.height() + self._padding)

    def paintEvent(self, a0: QPaintEvent):
        painter = QPainter(self)
        top_left = self.rect().topLeft()
        if self.details_view:
            painter.setOpacity(0.40)
        painter.drawPixmap(top_left.x() + self._padding_left, top_left.y() + self._padding_top, self.pixmap)
        painter.setOpacity(1)
        painter.setPen(Qt.black)
        if self.details_view:
            text = f"{self.base_pixmap.width()}x{self.base_pixmap.height()}px\n" \
                   f"{self.file_size}\n" \
                   f"{self.m_time}"
            rect = self.rect()
            rect.adjust(self._text_padding, self._text_padding, 0, 0)
            painter.drawText(rect, Qt.AlignCenter, text)

    def zoom(self, scale):
        self.image_size = scale
        self.pixmap = self.base_pixmap.scaled(self.image_size, self.image_size, Qt.KeepAspectRatio)
        self.setMaximumSize(QSize(self.pixmap.width() + self._padding, self.pixmap.height() + self._padding))
        self.setMinimumSize(QSize(self.pixmap.width() + self._padding,
                                  self.pixmap.height() + self._padding))
        self.setFont(QFont("sans", round(self.image_size * self._text_scaler, 0), self._text_weight))
        self.update()

    def enterEvent(self, a0: QtCore.QEvent):
        self.details_view = True
        self.update()

    def leaveEvent(self, a0: QtCore.QEvent):
        self.details_view = False
        self.update()


class ThumbnailRow(QWidget):

    def __init__(self):
        super().__init__()
        self.labels = []
        self.layout = QHBoxLayout()
        self.layout.setSpacing(3)
        self.layout.setContentsMargins(3, 0, 0, 3)
        self.setLayout(self.layout)
        self.items = []

    def add_items(self, items):
        self.items = items
        self.draw_items()

    def draw_items(self):
        self.clear()
        for item in self.items:
            thumbnail = Thumbnail(item)
            self.layout.addWidget(thumbnail, 0)
        self.layout.addWidget(QWidget(), 1)

    def clear(self):
        for i in reversed(range(self.layout.count())):
            widget = self.layout.itemAt(i).widget()
            # remove it from the layout list
            self.layout.removeWidget(widget)
            # remove it from the gui
            widget.setParent(None)

    def zoom(self, scale):
        for i in reversed(range(self.layout.count())):
            widget = self.layout.itemAt(i).widget()
            if isinstance(widget, Thumbnail):
                widget.zoom(scale)

    def mousePressEvent(self, a0: QtGui.QMouseEvent):
        print("Mouse Press")

    def mouseDoubleClickEvent(self, a0: QtGui.QMouseEvent):
        print("Mouse Double Click")


class ThumbnailGrid(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QGridLayout()
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.data = {}
        self.setLayout(self.layout)

    def add_items(self, index, data):
        if not self.data.__contains__(index):
            row = ThumbnailRow()
            self.data[index] = row
            self.layout.addWidget(row, index, 0)
            self.layout.setColumnStretch(index, 1)
            self.layout.setRowStretch(index, 1)
        self.data[index].add_items(data)

    def clear(self):
        for val, widget in self.data.items():
            widget.clear()
            self.layout.removeWidget(widget)
            widget.setParent(None)
        self.data.clear()

    def zoom(self, scale):
        for val, widget in self.data.items():
            widget.zoom(scale)


class ThumbnailView(QScrollArea):
    def __init__(self):
        super().__init__()
        self.setBackgroundRole(QPalette.Light)
        self.setWidgetResizable(True)
        self.grid = ThumbnailGrid()

        grid_layout = QVBoxLayout()
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.addWidget(self.grid)
        grid_layout.addWidget(QWidget(), 1)

        tmp_widget = QWidget()
        tmp_widget.setLayout(grid_layout)
        self.setWidget(tmp_widget)

    def add_items(self, index, data):
        self.grid.add_items(index, data)

    def clear(self):
        self.grid.clear()

    def zoom(self, scale):
        self.grid.zoom(scale)
