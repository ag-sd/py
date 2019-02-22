import sys

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QApplication,
                             QMainWindow, QSplitter)

import Imageplay
from Imageplay.src.ImageView import ImageView
from Imageplay.src.PlayList import PlayListController


class ImagePlayApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.playlistController = PlayListController()
        self.imageView = ImageView()
        self.playlistController.image_change_event.connect(self.imageView.set_image)
        self.playlistController.image_crop_event.connect(self.imageView.crop_image)
        self.initUI()
        self.show()

    def initUI(self):

        splitter1 = QSplitter(Qt.Vertical)
        splitter1.addWidget(self.imageView)
        splitter1.addWidget(self.playlistController)
        splitter1.setSizes([500, 100])

        self.setCentralWidget(splitter1)
        self.resize(600, QtWidgets.QDesktopWidget().availableGeometry().height())
        self.setWindowTitle(Imageplay.__APP_NAME__)
        self.setObjectName("MainWindow")
        if not Imageplay.settings.load_ui(self, Imageplay.logger, True):
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

    def closeEvent(self, QCloseEvent):
        Imageplay.settings.save_ui(self, Imageplay.logger, True)


def main():
    app = QApplication(sys.argv)
    ex = ImagePlayApp()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
