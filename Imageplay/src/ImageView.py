from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QPalette
from PyQt5.QtWidgets import QLabel, QScrollArea, QFrame

import Imageplay
from Imageplay import SettingsKeys
from model.Actions import ActionType


class ImageWidget(QLabel):

    def __init__(self, parent_viewport_rect):
        super().__init__("Drop files into the playlist to view them")
        self.zoom = 1
        self.is_scaled = False
        self.current_pixmap = None
        self.current_file = None
        self.current_image = None
        self.parent_viewport_rect = parent_viewport_rect
        self.initUI()

    def initUI(self):
        Imageplay.settings.settings_change_event.connect(self.set_scaling_setting)
        self.set_scaling_setting(SettingsKeys.image_scaled,
                                 Imageplay.settings.get_setting(SettingsKeys.image_scaled, True))
        self.setAlignment(Qt.AlignCenter)
        # self.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)
        # self.setLineWidth(2)

    def set_image(self, qImage, file):
        Imageplay.logger.debug("Image received " + file)
        self.current_file = file
        self.current_image = qImage
        self.zoom = 1
        self.current_pixmap = QPixmap.fromImage(qImage)
        self.display_image()

    def reset(self):
        self.set_image(self.current_image, self.current_file)

    def set_scaling_setting(self, setting, value):
        if setting == SettingsKeys.image_scaled:
            self.set_scaling(value)

    def set_scaling(self, scaling):
        self.is_scaled = scaling
        self.zoom = 1
        self.display_image()

    def zoom_in(self):
        self.zoom += self.zoom * 0.2
        self.display_image()

    def zoom_out(self):
        self.zoom -= self.zoom * 0.2
        self.display_image()

    def parent_resize(self, parent_viewport_rect):
        self.parent_viewport_rect = parent_viewport_rect
        self.display_image()

    def display_image(self):
        if self.current_pixmap is not None:
            if self.is_scaled:
                width = self.parent_viewport_rect.width() * self.zoom
                height = self.parent_viewport_rect.height() * self.zoom
            else:
                width = self.current_image.width() * self.zoom
                height = self.current_image.height() * self.zoom

            pixmap = self.current_pixmap.scaled(width, height, Qt.KeepAspectRatio)
            self.setPixmap(pixmap)
            print("Label Size - " + str(self.rect()) + " image size " + str(pixmap.rect()))


class ImageView(QScrollArea):
    _BORDERS = -10

    def __init__(self):
        super().__init__()
        self.setBackgroundRole(QPalette.Text)
        self.setWidgetResizable(True)
        self.setContentsMargins(self._BORDERS, self._BORDERS, self._BORDERS, self._BORDERS)
        self.image_widget = ImageWidget(self.viewport().rect())
        self.edit_action = None
        self.initUI()

    def initUI(self):
        self.setAlignment(Qt.AlignCenter)
        self.setWidget(self.image_widget)

    def set_image(self, qImage, file):
        self.image_widget.set_image(qImage, file)

    def set_scaling(self, scaling):
        self.image_widget.set_scaling(scaling)

    def change_zoom(self, zoom_in=False):
        if zoom_in:
            self.image_widget.zoom_in()
        else:
            self.image_widget.zoom_out()

    def image_edit_start(self, edit_action):
        if self.edit_action is not None:
            return
        self.edit_action = edit_action
        edit_action.setup(self.image_widget)

    def image_edit_complete(self, action):
        if action == ActionType.CANCEL:
            self.image_widget.reset()
        else:
            self.edit_action.apply(self.image_widget)

        if self.edit_action is not None:
            self.edit_action.cleanup(self.image_widget)
            self.edit_action = None

    def resizeEvent(self, event):
        self.image_widget.parent_resize(self.viewport().rect())