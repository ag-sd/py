import argparse
import os
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QApplication,
                             QMainWindow, QSplitter, QDesktopWidget, QVBoxLayout, QWidget)

import Imageplay
from ControlBar import ControlBar
from ImageDetails import ImageDetails
from Imageplay.src.ImageView import ImageView
from PlayList import PlayList
from model.PlaylistFileModel import PlaylistFileModel


class ImagePlayApp(QMainWindow):

    def __init__(self):
        super().__init__()
        self.imageView = ImageView()
        self.playlist_model = PlaylistFileModel()
        self.playlist_table = PlayList(self.playlist_model)
        self.playlistController = ControlBar(self.playlist_model)
        self.imageDetails = ImageDetails()
        self.initUI()
        self.show()
        files, start_file = self.parse_args()
        self.playlistController.files_from_args(files, start_file)

    def initUI(self):

        self.playlist_model.image_change_event.connect(self.imageView.set_image)
        self.playlist_model.image_change_event.connect(self.imageDetails.refresh_details)
        self.playlistController.image_edit_event.connect(self.imageView.editEvent)
        self.playlistController.image_edit_complete_event.connect(self.imageView.image_edit_complete)
        self.playlistController.image_edit_starting_event.connect(self.image_editing_started)
        self.playlistController.image_edit_complete_event.connect(self.image_editing_complete)
        self.playlistController.image_zoom_event.connect(self.imageView.change_zoom)

        splitter_list = QSplitter(Qt.Horizontal)
        splitter_list.addWidget(self.imageDetails)
        splitter_list.addWidget(self.playlist_table)
        splitter_list.setSizes([250, 500])
        splitter_list.setObjectName("_stateful_splitter_list")

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.playlistController)
        layout.addWidget(splitter_list, 1)

        dummy = QWidget()
        dummy.setLayout(layout)

        splitter_main = QSplitter(Qt.Vertical)
        splitter_main.addWidget(self.imageView)
        splitter_main.addWidget(dummy)
        splitter_main.setSizes([500, 100])
        splitter_main.setObjectName("_stateful_splitter_main")

        self.setCentralWidget(splitter_main)
        self.resize(600, QDesktopWidget().availableGeometry().height())
        self.setWindowTitle(Imageplay.__APP_NAME__)
        self.setObjectName("MainWindow")
        if not Imageplay.settings.load_ui(self, Imageplay.logger):
            self.center_ui()

    def image_editing_started(self):
        self.playlist_table.setEnabled(False)
        self.imageDetails.setEnabled(False)

    def image_editing_complete(self):
        self.playlist_table.setEnabled(True)
        self.imageDetails.setEnabled(True)

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
        Imageplay.settings.save_ui(self, Imageplay.logger)

    @staticmethod
    def parse_args():
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
        return files, start_file


def main():
    app = QApplication(sys.argv)
    ex = ImagePlayApp()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
