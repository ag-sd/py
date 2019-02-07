from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy


class ImageView(QWidget):
    def __init__(self):
        super().__init__()
        self.label = QLabel("Drop files into the playlist to view them")
        self.initUI()
        self.image = ""

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
        print("Image View to present " + image_file)
        self.image = image_file
        self.resizeEvent(None)

    def resizeEvent(self, event):
        if self.image != "":
            pixmap = QPixmap(self.image)
            self.label.setPixmap(pixmap.scaled(self.label.width(), self.label.height(), Qt.KeepAspectRatio))
        print("resize")
