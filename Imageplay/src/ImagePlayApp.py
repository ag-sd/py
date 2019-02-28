import argparse
import os
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QApplication,
                             QMainWindow, QSplitter, QDesktopWidget)

import Imageplay
from Imageplay.src.ImageView import ImageView
from Imageplay.src.PlayList import Controller
from model.PlaylistFileModel import PlaylistFileModel


class ImagePlayApp(QMainWindow):

    def __init__(self):
        super().__init__()
        self.imageView = ImageView()
        self.playlist_model = PlaylistFileModel()
        self.playlistController = Controller(self.playlist_model)
        self.initUI()
        self.show()
        self.parse_args()

    def initUI(self):

        self.playlist_model.image_change_event.connect(self.imageView.set_image)

        splitter1 = QSplitter(Qt.Vertical)
        splitter1.addWidget(self.imageView)
        splitter1.addWidget(self.playlistController)
        splitter1.setSizes([500, 100])

        self.setCentralWidget(splitter1)
        self.resize(600, QDesktopWidget().availableGeometry().height())
        self.setWindowTitle(Imageplay.__APP_NAME__)
        self.setObjectName("MainWindow")
        if not Imageplay.settings.load_ui(self, Imageplay.logger, True):
            self.center_ui()

    def center_ui(self):
        # geometry of the main window
        qr = self.frameGeometry()
        # center point of screen
        cp = QDesktopWidget().availableGeometry().center()
        # move rectangle's center point to screen's center point
        qr.moveCenter(cp)
        # top left of rectangle becomes top left of window centering it
        self.move(qr.topLeft())

    def closeEvent(self, QCloseEvent):
        Imageplay.settings.save_ui(self, Imageplay.logger, True)

    def parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('-f', '--files', nargs='+',
                            help='Browse a set of files', required=False)
        parser.add_argument('-d', '--dirs', nargs='+',
                            help='Browse a set of directories', required=False)
        parser.add_argument('-b', '--browse', type=str,
                            help='Browse a directories starting with the specified file', required=False)
        args = parser.parse_args()
        Imageplay.logger.info(f"Arguments provided: {args}")
        files = []
        start_file = None
        if args.browse and (args.files or args.dirs):
            parser.error("Browse cannot be specified with any other argument")
        if args.browse:
            if os.path.isdir(args.browse):
                parser.error("Start file must not be a directory in Browsing Mode")
            else:
                files = [os.path.dirname(args.browse)]
                start_file = os.path.basename(args.browse)
        else:
            if args.files:
                files += args.files
            if args.dirs:
                files += args.dirs
        self.playlistController.files_from_args(files, start_file)


def main():
    app = QApplication(sys.argv)
    ex = ImagePlayApp()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
