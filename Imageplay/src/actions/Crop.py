from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QSizeGrip, QRubberBand

from actions.BaseEditAction import BaseEditAction


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


class CropAction(BaseEditAction):
    def __init__(self):
        super().__init__("◳", "Crop Image", QIcon("resources/default_action.svg"))
        self.band = None

    def setup(self, image_widget):
        self.band = ResizableRubberBand(image_widget)
        self.band.move(100, 100)
        self.band.resize(50, 50)
        self.band.setMinimumSize(30, 30)

    def apply(self, image_widget):
        top_left = self.band.mapToParent(self.band.rect().topLeft())
        new_image = CropAction.crop(top_left,
                                    self.band.width(), self.band.height(),
                                    image_widget.rect(),
                                    image_widget.current_image.rect(),
                                    image_widget.current_image)
        new_image.save(image_widget.current_file)
        image_widget.reset()

    def cleanup(self, image_widget):
        if self.band is not None:
            self.band.hide()
            self.band = None

    @staticmethod
    def crop(crop_start, crop_width, crop_height, widget_rect, image_rect, base_image):
        # image scale
        # x_ratio = image_rect.width() / widget_rect.width()
        # y_ratio = image_rect.height() / widget_rect.height()
        if image_rect.width() > image_rect.height():
            ratio = image_rect.width() / widget_rect.width()
        else:
            ratio = image_rect.height() / widget_rect.height()

        left_shift = (widget_rect.width() - image_rect.width()) / 2
        top_shift = (widget_rect.height() - image_rect.height()) / 2

        top = crop_start.y() * ratio
        left = crop_start.x() * ratio
        width = crop_width * ratio
        height = crop_height * ratio

        return base_image.copy(top, left, width, height)
        #
        #
        #
        #
        #
        # # image location
        # # Left shift of image - (How much the image needs to shift left to start at 0)
        # left_shift = (widget_rect.width() - image_rect.width()) / 2
        # # Top shift of image - (How much the image needs to shift top to start at 0)
        # top_shift = (widget_rect.height() - image_rect.height()) / 2
        #
        #
        #
        # top = crop_start.y() - top_shift
        # left = crop_start.x() - left_shift
        # width = left + crop_width
        # height = top + crop_height
        #
        # return base_image.copy(left, top, crop_width, crop_height)


    @staticmethod
    def crop1(top_left, crop_width, crop_height,
             view_width, view_height, base_image):
        # Compute x ratio, y ratio from dimension of view and dimension of image
        x_ratio = base_image.width() / view_width
        y_ratio = base_image.height() / view_height

        top = top_left.x() * y_ratio
        left = top_left.y() * x_ratio
        width = crop_width * x_ratio
        height = crop_height * y_ratio

        return base_image.copy(top, left, width, height)

