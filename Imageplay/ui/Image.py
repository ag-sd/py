import json
import os
import sys

from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QFontDatabase
from PyQt5.QtGui import QPixmap, QPalette, QMovie, QImageReader
from PyQt5.QtWidgets import QDialog, QVBoxLayout
from PyQt5.QtWidgets import QScrollArea, QApplication, QLabel

import CommonUtils
import Imageplay
import MediaMetaData
from Imageplay.ui import Settings

SUPPORTED_FORMATS = list(map(lambda x: f'.{str(x, "utf-8").upper()}', QImageReader.supportedImageFormats()))
_supported_animation_formats = "|".join(map(lambda x: str(x, "utf-8").upper(), QMovie.supportedFormats()))


class ImageView(QScrollArea):
    files_dropped_event = pyqtSignal(bool, 'PyQt_PyObject')
    image_change_event = pyqtSignal(str)
    animation_start_event = pyqtSignal()
    animation_end_event = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setBackgroundRole(QPalette.Text)
        self.setWidgetResizable(True)
        self.image = QLabel("Image")
        self.current_file = None
        self.pixmap = None
        self.animation = None
        self.animation_loop_count = 0
        self.zoom = 1
        self.scaled = False
        self.setAcceptDrops(True)
        self.init_ui()

    def init_ui(self):
        self.setAlignment(Qt.AlignCenter)
        self.image.setAlignment(Qt.AlignCenter)
        self.setWidget(self.image)

    def set_image(self, image_file):
        self.current_file = image_file
        self.zoom = 1
        if _supported_animation_formats.__contains__(os.path.splitext(image_file)[1][1:].upper()):
            Imageplay.logger.info(f"Animation file received: {image_file}")
            # Animation file received
            self.pixmap = None
            self.animation = QMovie(image_file)
            self.animation_loop_count = 0
            self.animation.frameChanged.connect(self._animation_frame_changed)
        else:
            self.pixmap = QPixmap(image_file)
            self.animation = None
        self._display_image()
        Imageplay.logger.info(f"Image set to {image_file}")
        self.image_change_event.emit(image_file)

    def set_scaled(self, scaled):
        self.scaled = scaled
        self.zoom = 1
        self._display_image()

    def is_scaled(self):
        return self.scaled

    def zoom_in(self):
        self.zoom += self.zoom * 0.2
        self._display_image()

    def zoom_out(self):
        self.zoom -= self.zoom * 0.2
        self._display_image()

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
            self.files_dropped_event.emit(event.keyboardModifiers() == Qt.ControlModifier, event.mimeData().urls())
        else:
            event.ignore()

    def resizeEvent(self, event):
        self._display_image()

    def _animation_frame_changed(self, frame_number):
        if self.animation is not None and frame_number == self.animation.frameCount() - 1:
            # Final frame reached. Decide what to do next
            self.animation_loop_count += 1
            # Looping
            looping_count = Settings.get_animation_loop()
            if looping_count == -1 and self.animation.loopCount() != -1:
                # Forcibly loop image
                self.animation.jumpToFrame(0)
                Imageplay.logger.info("Animation restart for infinite loop")
            elif self.animation_loop_count >= looping_count:
                self.animation.stop()
                Imageplay.logger.info(f"Animation stopped after loop limit ({looping_count}) reached")
                self.animation_end_event.emit()

    def _get_adjusted_dimensions(self, base_width, base_height):
        if self.scaled:
            viewport = self.viewport().rect()
            return viewport.width() * self.zoom, viewport.height() * self.zoom
        return base_width * self.zoom, base_height * self.zoom

    def _display_image(self):
        if self.pixmap is None and self.animation is None:
            return

        if self.pixmap is not None:
            width, height = self._get_adjusted_dimensions(self.pixmap.width(), self.pixmap.height())
            pixmap = self.pixmap.scaled(width, height, Qt.KeepAspectRatio)
            self.image.setPixmap(pixmap)
        elif self.animation is not None:
            if self.animation.state() == QMovie.NotRunning:
                self.animation.jumpToFrame(0)
            animation_size = self.animation.currentImage().size()
            aspect_ratio = animation_size.width() / animation_size.height()
            width, height = self._get_adjusted_dimensions(animation_size.width(), animation_size.height())
            animation_width = height * aspect_ratio
            if animation_width <= width:
                size = QSize(animation_width, height)
            else:
                animation_height = width / aspect_ratio
                size = QSize(width, animation_height)
            self.animation.setScaledSize(size)
            if self.animation.state() == QMovie.NotRunning:
                # Setup the movie
                self.image.setMovie(self.animation)
                self.animation.start()
                self.animation_start_event.emit()
        Imageplay.logger.debug("Label Size - " + str(self.viewport().rect()) + " image size " + str(self.image.rect()))


class FileDetails(QDialog):
    def __init__(self):
        super().__init__()
        self._file = ""
        self._details = QLabel()
        self._scroll_area = QScrollArea()
        self.executor = None
        self.init_ui()

    def init_ui(self):
        self.setBackgroundRole(QPalette.Window)
        self._details.setFont(QFontDatabase.systemFont(QFontDatabase.FixedFont))
        self._scroll_area.setWidget(self._details)
        self._details.setContentsMargins(5, 5, 5, 5)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._scroll_area)
        self.setLayout(layout)
        self.setMinimumSize(720, 540)
        self.setWindowTitle("Image Details")

    def set_file(self, image_file):
        self._file = image_file
        self.setWindowTitle(f"Image Details: {self._file}")
        self._show_message(self._MetaDataResult(image_file, "Fetching metadata, please wait..."))
        runnable = self._MetaDataCommand(image_file)
        runnable.signals.result.connect(self._show_message)
        self.executor = CommonUtils.CommandExecutionFactory([runnable], logger=Imageplay.logger)
        self.executor.start()

    def _show_message(self, metadata_result):
        if metadata_result.file != self._file:
            Imageplay.logger.debug(f"Skipping metadata result for for {metadata_result.file}")
            return
        self._details.setText(f"File: {metadata_result.file}\n\n{metadata_result.result}")
        self._details.adjustSize()

    class _MetaDataResult:
        def __init__(self, file, result):
            super().__init__()
            self.file = file
            self.result = result

    class _MetaDataCommand(CommonUtils.Command):
        def __init__(self, file):
            super().__init__()
            self.file = file

        def do_work(self):
            metadata = MediaMetaData.get_metadata(self.file)
            sanitized = {}
            for key in metadata:
                sanitized[str(key)] = metadata[key]
            self.signals.result.emit(FileDetails._MetaDataResult(self.file, json.dumps(sanitized, indent=5)))



if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = FileDetails()
    ex.show()
    # ex.set_file("/mnt/Stuff/testing/audio/1_XdqiA-pdkeFuX5W2-NSaNg.jpeg")
    ex.set_file("/mnt/Stuff/test/1animated_Test_image.gif")
    sys.exit(app.exec_())


# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     ex = ImageView()
#     ex.show()
#     ex.set_image("/mnt/Stuff/test/1animated_Test_image.gif")
#     sys.exit(app.exec_())