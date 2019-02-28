from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QPalette
from PyQt5.QtWidgets import QWidget, QLabel, QRubberBand, QHBoxLayout, QSizeGrip, QScrollArea

import Imageplay


class ResizableRubberBand(QWidget):
    """Wrapper to make QRubberBand mouse-resizable using QSizeGrip
    https://stackoverflow.com/questions/19066804/implementing-resize-handles-on-qrubberband-is-qsizegrip-relevant
    Source: http://stackoverflow.com/a/19067132/435253
    """
    def __init__(self, parent=None):
        super(ResizableRubberBand, self).__init__(parent)
        self.setMinimumSize(30, 30)
        self.setWindowFlags(Qt.SubWindow)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.grip1 = QSizeGrip(self)
        self.layout.addWidget(self.grip1, 0, Qt.AlignRight | Qt.AlignBottom)

        self.rubberband = QRubberBand(QRubberBand.Rectangle, self)
        self.rubberband.move(0, 0)
        self.rubberband.show()
        self.move_offset = None
        self.resize(150, 150)

        self.show()

    def resizeEvent(self, event):
        self.rubberband.resize(self.size())

    def mousePressEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move_offset = event.pos()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            new_pos = self.mapToParent(event.pos() - self.move_offset)
            parent_rect = self.parent().rect()
            image_rect = self.parent().pixmap().rect()
            adjustment = parent_rect.bottomRight()-image_rect.bottomRight()
            y_offset = adjustment.y() / 2
            x_offset = adjustment.x() / 2

            new_pos.setX(max(x_offset, min(new_pos.x(), image_rect.width() - self.width() + x_offset)))
            new_pos.setY(max(y_offset, min(new_pos.y(), image_rect.height() - self.height() + y_offset)))

            self.move(new_pos)

    def mouseReleaseEvent(self, event):
        self.move_offset = None


class ImageView(QScrollArea):

    def __init__(self):
        super().__init__()
        self.label = QLabel("Drop files into the playlist to view them")
        self.image = ""
        self.movie = None
        self.band = None
        self.isScaled = True
        self.setBackgroundRole(QPalette.Shadow)
        self.setWidgetResizable(True)
        self.setAlignment(Qt.AlignCenter)
        self.initUI()

    def initUI(self):
        self.label.setMinimumSize(1, 1)
        self.label.setAlignment(Qt.AlignCenter)
        self.setWidget(self.label)

    def set_image(self, qImage, file):
        Imageplay.logger.debug("Image received ")
        self.label.setText(file)
        # self.image = image_file
        # self.resizeEvent(None)

    def set_scaling(self, scaling):
        self.isScaled = scaling
        self.setWidgetResizable(scaling)
        self.resizeEvent(None)

    def resizeEvent(self, event):
        pixmap = None

        if isinstance(self.image, QPixmap):
            pixmap = self.image
        elif isinstance(self.image, str) and self.image != "":
            pixmap = QPixmap(self.image)

        if self.isScaled and pixmap is not None:
            pixmap = pixmap.scaled(self.width(), self.height(), Qt.KeepAspectRatio)

        if pixmap is not None:
            self.label.setPixmap(pixmap)
            self.label.resize(pixmap.size())
            self.label.setMaximumSize(pixmap.size())

