import sys

from PyQt5.QtWidgets import QApplication, QMainWindow, QSplitter

import MediaLib
from MediaLib.runtime.library import LibraryManagement


class MediaLibApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        from random import randint
        #"/mnt/Music/Running"
        LibraryManagement.create_library("Test Library1"+str(randint(0, 1000)), "Audio", ["/mnt/Stuff/testing/audio",])

    def init_ui(self):
        MediaLib.logger.debug("Initializing UI")
        splitter = QSplitter()
        self.setCentralWidget(splitter)
        self.show()
        MediaLib.logger.debug("Initializing UI - Completed")


if __name__ == '__main__':
    # print("%s" % str(options.allOptions))
    app = QApplication(sys.argv)
    ex = MediaLibApp()
    sys.exit(app.exec_())
