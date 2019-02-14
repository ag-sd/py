import random
from os import path

from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import QTableView, QAbstractItemView, QMenu, QAction

from Imageplay.src.model.FileItemModel import FileItemModel


class CircularLRUQueue:
    def __init__(self, size):
        self.size = size
        self.queue = []

    def enqueue(self, item=-1):
        if len(self.queue) >= self.size:
            self.queue = []

        if item < 0:
            item = len(self.queue)

        self.queue.append(item)
        return item

    def prev(self):
        # TODO
        print("TODO")

    def next(self, is_random):
        if not is_random:
            return self.enqueue()
        else:
            # Find a random number between 0 and size not present in the queue
            rand = random.randint(0, self.size - 1)
            while self.queue.__contains__(rand):
                rand = random.randint(0, self.size - 1)
            return self.enqueue(rand)

    def resize(self, new_size):
        # if new size > current size set max size
        if new_size > self.size:
            self.size = new_size
        # if new size < current size remove all numbers > new size
        elif new_size < self.size:
            for i in range(new_size, self.size):
                if self.queue.__contains__(i):
                    self.queue[self.queue.index(i)] = -1
        self.reset()

    def reset(self):
        self.queue.clear()


class AnimationHandler:

    def __init__(self, animation_file):
        self.animation_file = animation_file
        self.movie = QtGui.QMovie(animation_file)
        self.current_frame = 0

    def next_frame(self):
        print("Current frame is " + str(self.current_frame))
        self.movie.jumpToFrame(self.current_frame)
        self.current_frame += 1
        return self.movie.currentPixmap()

    def has_next(self):
        return self.current_frame < self.movie.frameCount()

    def prev_frame(self):
        if self.current_frame == 0:
            return self.movie.currentPixMap
        else:
            self.current_frame -= 1
            return next()


class PlayList(QTableView):
    image_change_event = pyqtSignal('PyQt_PyObject')

    def __init__(self):
        super().__init__()
        self.initUI()

        self.queue = CircularLRUQueue(0)
        self.playedSoFar = 0
        self.animation_handler = None

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.time_changed)

        self.playPause_action = self.create_action("Play", "F5", self.play_or_pause)
        self.addAction(self.playPause_action)

        self.previous_action = self.create_action("Previous", "Left", self.previous)
        self.addAction(self.previous_action)

        self.next_action = self.create_action("Next", "Right", self.next)
        self.addAction(self.next_action)

        self.loop_action = self.create_action("Loop", "L", self.loop, True, True)
        self.loop_action.setCheckable(True)
        self.addAction(self.loop_action)

        self.shuffle_action = self.create_action("Shuffle", "S", None, True, False)
        self.addAction(self.shuffle_action)
        self.toggle_playback(False)

    def initUI(self):
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        # stylesheet = "QHeaderView::section{" \
        #              "border-top:0px solid #D8D8D8;" \
        #              "border-left:0px solid #D8D8D8;" \
        #              "border-right:1px solid #D8D8D8;" \
        #              "border-bottom: 1px solid #D8D8D8;" \
        #              "padding:4px;" \
        #              "}"
        # self.horizontalHeader().setStyleSheet(stylesheet)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.verticalHeader().hide()
        self.horizontalHeader().setHighlightSections(False)
        self.setModel(FileItemModel())
        self.horizontalHeader().setStretchLastSection(True)

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
            self.files_added(event.mimeData().urls())
        else:
            event.ignore()

    def files_added(self, file_urls):
        # Use existing model if available
        if isinstance(self.model(), FileItemModel):
            item_model = self.model()
        else:
            item_model = FileItemModel()
        for file in file_urls:
            if file.isLocalFile():
                _dir, file = path.split(file.path())
                # TODO-Supported files only
                item_model.append_row(_dir, file)
        self.setModel(item_model)
        self.resizeColumnsToContents()
        self.resizeRowsToContents()
        self.horizontalHeader().setStretchLastSection(True)
        if item_model.rowCount(self):
            self.toggle_playback(True)
            self.queue.resize(item_model.rowCount(self))
            self.timer.start(1000)
            self.playPause_action.setText("Pause")
            self.playedSoFar = 0

    def time_changed(self):
        if self.animation_handler is not None:
            print("In animation...")
            if self.animation_handler.has_next():
                self.image_change_event.emit(self.animation_handler.next_frame())
                return
            else:
                # Discard the animation handler and chose next file
                self.animation_handler = None

        if self.playedSoFar >= self.model().rowCount(self):
            if self.loop_action.isChecked():
                self.playedSoFar = 0
                self.queue.reset()
            else:
                self.timer.stop()
                self.toggle_playback(False)
                return

        index = self.queue.next(self.shuffle_action.isChecked())
        file = path.join(self.model().index(index, 0).data(), self.model().index(index, 1).data())
        if file.upper().endswith(".GIF"):
            print("GIF MODE")
            self.animation_handler = AnimationHandler(file)
        else:
            self.animation_handler = None
            self.image_change_event.emit(file)

        self.playedSoFar = self.playedSoFar + 1
        self.selectRow(index)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.addAction(self.playPause_action)
        menu.addAction(self.previous_action)
        menu.addAction(self.next_action)
        menu.addSeparator()
        menu.addAction(self.loop_action)
        menu.addAction(self.shuffle_action)

        menu.exec_(self.mapToGlobal(event.pos()))

    def play_or_pause(self):
        if self.playPause_action.text() == "Play":
            self.playPause_action.setText("Pause")
            self.timer.start()
        else:
            self.playPause_action.setText("Play")
            self.timer.stop()

    def previous(self):
        print("Previous")

    def next(self):
        print("next")

    def loop(self):
        self.queue.reset()

    def animation_stopped(self):
        print("Stop")
        self.timer.start()

    def animation_started(self, file, frame_count):
        print(file, frame_count)
        self.timer.stop()

    def toggle_playback(self, toggle):
        self.playPause_action.setEnabled(toggle)
        self.previous_action.setEnabled(toggle)
        self.next_action.setEnabled(toggle)

    @staticmethod
    def create_action(text, shortcut, slot, checkable=False, checked=False):
        action = QAction(text)
        action.setShortcut(shortcut)
        action.setCheckable(checkable)
        action.setChecked(checked)
        if slot is not None:
            action.triggered.connect(slot)
        return action

