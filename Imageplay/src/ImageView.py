from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QMovie
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy


class ImageView(QWidget):
    animation_started = pyqtSignal(str, int)
    animation_stopped = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.label = QLabel("Drop files into the playlist to view them")
        self.initUI()
        self.image = ""
        self.movie = None

    def initUI(self):
        self.label.setMinimumSize(1, 1)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("QLabel {background-color: #0E0E0E;}")
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.label)
        self.setLayout(layout)

    def set_image(self, image_file):
        print("Image View to present ")
        self.image = image_file
        self.resizeEvent(None)

    def resizeEvent(self, event):
        if isinstance(self.image, QPixmap):
            self.label.setPixmap(self.image.scaled(self.label.width(), self.label.height(), Qt.KeepAspectRatio))
        elif isinstance(self.image, str) and self.image != "":
            pixmap = QPixmap(self.image)
            self.label.setPixmap(pixmap.scaled(self.label.width(), self.label.height(), Qt.KeepAspectRatio))

