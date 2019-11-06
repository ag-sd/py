import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableView

import MediaLib
from MediaLib.runtime.library import LibraryManagement
from MediaLib.ui.LibraryManagerPanel import LibraryManagerPanel


class MediaLibApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.lib_Manager = LibraryManagerPanel()
        self.init_ui()
        from random import randint
        # #"/mnt/Music/Running"
        # # , ["/mnt/Stuff/testing/audio",])
        # #   ["C:\\Users\\sheld\\Downloads\\Test Library",])
        # LibraryManagement.create_library("Test Library1"+str(randint(0, 1000)), "Audio",
        #                                  ["/mnt/Stuff/testing/audio",])

    def init_ui(self):
        MediaLib.logger.debug("Initializing UI")
        # splitter = QSplitter()
        # self.setCentralWidget(splitter)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.lib_Manager)
        self.setCentralWidget(QTableView())
        self.show()
        MediaLib.logger.debug("Initializing UI - Completed")


if __name__ == '__main__':
    # print("%s" % str(options.allOptions))
    app = QApplication(sys.argv)
    ex = MediaLibApp()
    sys.exit(app.exec_())
