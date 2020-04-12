import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableView, QStatusBar

import MediaLib
from MediaLib.runtime.library import AudioLibrary
from MediaLib.ui.LibraryManagerPanels import LibraryManagerPanel, LibraryTaskManager


class MediaLibApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.task_executor = LibraryTaskManager()
        self.lib_Manager = LibraryManagerPanel(self.task_executor)
        self.status_bar = QStatusBar()
        self.init_ui()
        # #"/mnt/Music/Running"
        # # , ["/mnt/Stuff/testing/audio",])
        # #   ["C:\\Users\\sheld\\Downloads\\Test Library",])
        # LibraryManagement.create_library("Test Library1"+str(randint(0, 1000)), "Audio",
        #                                  ["/mnt/Stuff/testing/audio",])

    def init_ui(self):
        MediaLib.logger.debug("Initializing UI")
        self.status_bar.addPermanentWidget(self.task_executor)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.lib_Manager)
        self.setStatusBar(self.status_bar)
        self.setCentralWidget(QTableView())
        self.show()
        MediaLib.logger.debug("Initializing UI - Completed")


if __name__ == '__main__':
    # print("%s" % str(options.allOptions))
    #app = QApplication(sys.argv)
    #ex = MediaLibApp()
    #sys.exit(app.exec_())
    AudioLibrary.create_model_dictionary()
