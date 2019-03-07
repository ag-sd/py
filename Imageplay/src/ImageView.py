from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QPalette
from PyQt5.QtWidgets import QWidget, QLabel, QRubberBand, QHBoxLayout, QSizeGrip, QScrollArea, QSizePolicy

import Imageplay
from Imageplay import SettingsKeys
from model.Actions import ActionType


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
            adjustment = parent_rect.bottomRight() - image_rect.bottomRight()
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
        # self.movie = None
        self.band = None
        self.edit_action = None
        self.zoom = 1
        self.isScaled = True
        self.current_file = ""
        self.current_image = None
        self.current_pixmap = None
        Imageplay.settings.settings_change_event.connect(self.set_scaling)
        self.initUI()
        self.set_scaling(SettingsKeys.image_scaled,
                         Imageplay.settings.get_setting(SettingsKeys.image_scaled, True))

    def initUI(self):
        self.label.setMinimumSize(1, 1)
        self.label.setAlignment(Qt.AlignCenter)
        self.setWidget(self.label)
        self.setWidgetResizable(True)
        self.setAlignment(Qt.AlignCenter)
        self.setBackgroundRole(QPalette.Text)

    def set_image(self, qImage, file):
        Imageplay.logger.debug("Image received ")
        self.label.setText(file)
        self.current_file = file
        self.current_image = qImage
        self.zoom = 1
        self.current_pixmap = QPixmap.fromImage(qImage)
        self.setup_image()

    def set_scaling(self, setting, value):
        if setting == SettingsKeys.image_scaled:
            self.isScaled = value
            self.setWidgetResizable(value)
            self.setup_image()

    def change_zoom(self, zoom_factor):
        if self.current_pixmap is not None:
            self.zoom *= zoom_factor
            pixmap = self.current_pixmap.scaled(self.current_image.width() * self.zoom,
                                                self.current_image.height() * self.zoom,
                                                Qt.KeepAspectRatio)
            self.label.setMaximumSize(pixmap.size())
            self.label.setPixmap(pixmap)
            self.label.adjustSize()
            self.setWidgetResizable(False)
            # Force the scroll area to re-evaluate the viewport
            self.widget().resize(10, 10)
            self.widget().resize(pixmap.size())
            print(pixmap.size())
            print(self.viewport().size())
            print(self.label.size())

    def setup_image(self):
        if self.current_pixmap is not None:
            if self.isScaled:
                pixmap = self.current_pixmap.scaled(self.width(), self.height(), Qt.KeepAspectRatio)
            else:
                pixmap = self.current_pixmap

            self.label.setMaximumSize(pixmap.size())
            self.label.setPixmap(pixmap)

            # Force the scroll area to re-evaluate the viewport
            self.widget().resize(10, 10)
            self.widget().resize(pixmap.size())

    def resizeEvent(self, event):
        self.setup_image()

    def editEvent(self, action):
        if self.edit_action is not None:
            return
        self.edit_action = action
        if action == ActionType.CROP:
            self.band = ResizableRubberBand(self.label)
            self.band.move(100, 100)
            self.band.resize(50, 50)
            self.band.setMinimumSize(30, 30)

    def image_edit_complete(self, action):
        if action == ActionType.CANCEL:
            self.set_image(self.current_image, self.current_file)
        else:
            if self.edit_action == ActionType.CROP:
                # Get position of rubberband with reference to label
                top_left = self.band.mapToParent(self.band.rect().topLeft())
                new_image = ActionType.CROP.value.apply(top_left, self.band.width(),
                                                        self.band.height(), self.label.width(),
                                                        self.label.height(), self.current_image)
                new_image.save(self.current_file)
                self.set_image(new_image, self.current_file)
                self.band.hide()
                self.band = None

        # Cleanup
        self.edit_action = None
        if self.band is not None:
            self.band.hide()
            self.band = None
