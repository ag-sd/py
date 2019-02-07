import sys

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QApplication,
                             QMainWindow, QSplitter, QLabel)

import Imageplay
from Imageplay.ImageView import ImageView
from Imageplay.PlayList import PlayList


class ImagePlayApp(QMainWindow):
    def __init__(self):
        super().__init__()
        # self.image_view = QLabel("Foooos")
        self.playlist = PlayList()
        self.imageView = ImageView()
        self.playlist.image_change_event.connect(self.image_changed)
        self.initUI()
        self.show()

    def initUI(self):

        splitter1 = QSplitter(Qt.Vertical)
        splitter1.addWidget(self.imageView)
        splitter1.addWidget(self.playlist)
        splitter1.setSizes([500, 100])

        self.setCentralWidget(splitter1)
        self.resize(600, QtWidgets.QDesktopWidget().availableGeometry().height())
        self.setWindowTitle('ImagePlay ' + Imageplay.__VERSION__)
        self.center_ui()

    def center_ui(self):
        # geometry of the main window
        qr = self.frameGeometry()
        # center point of screen
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        # move rectangle's center point to screen's center point
        qr.moveCenter(cp)
        # top left of rectangle becomes top left of window centering it
        self.move(qr.topLeft())

    def image_changed(self, image_path):
        self.imageView.set_image(image_path)


def main():
    app = QApplication(sys.argv)
    ex = ImagePlayApp()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
