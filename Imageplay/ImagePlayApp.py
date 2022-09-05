import subprocess
import sys

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QApplication

import CommonUtils
import Imageplay
from Imageplay.core.Playlist import Playlist, PlaylistCompleteException
from Imageplay.ui import Settings
from Imageplay.ui.Actions import ToolBar, Action
from Imageplay.ui.Image import ImageView, FileDetails
from Imageplay.ui.Settings import ImagePlaySettings


class ImagePlayApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.imageView = ImageView()
        self.toolbar = ToolBar()
        self.toolbar_hide_action = self.toolbar.toggleViewAction()
        self.playlist = Playlist(shuffle=Settings.get_shuffle(), loop=Settings.get_loop())
        self.timer = CommonUtils.PausableTimer()
        self.info_dialog = FileDetails()
        self.init_ui()

    def init_ui(self):
        self.timer.setInterval(Settings.get_image_delay() * 1000)
        self.timer.timeout.connect(self._timer_timeout)
        self.toolbar.button_pressed.connect(self._toolbar_action)
        self.addToolBar(self.toolbar)
        self.imageView.files_dropped_event.connect(self._files_dropped)
        self.imageView.animation_start_event.connect(self._animation_started)
        self.imageView.animation_end_event.connect(self._animation_stopped)
        self.imageView.image_change_event.connect(self._image_changed)
        self.imageView.set_scaled(Settings.get_image_scaled())
        self.setCentralWidget(self.imageView)
        self.setMinimumSize(800, 600)
        self.setWindowTitle(Imageplay.__APP_NAME__)
        self.setWindowIcon(QIcon.fromTheme("image-x-generic"))
        self.show()

    def enterEvent(self, event):
        if not self.toolbar_hide_action.isChecked():
            self.toolbar_hide_action.trigger()

    def leaveEvent(self, event):
        if self.toolbar_hide_action.isChecked():
            self.toolbar_hide_action.trigger()

    def _files_dropped(self, add, files):
        scanner = CommonUtils.FileScanner(files, recurse=True, is_qfiles=True,
                                          supported_extensions=Imageplay.ui.Image.SUPPORTED_FORMATS)
        if not add:
            self.playlist.clear()
        self.playlist.enqueue(list(scanner.files))
        if self.playlist.has_next():
            self._next_image()
            self.timer.start()

    def _timer_timeout(self):
        self._next_image()

    def _toolbar_action(self, event):
        if event == Action.PREV and self.playlist.has_previous():
            self.timer.stop()
            self.imageView.set_image(self.playlist.previous())
        elif event == Action.NEXT:
            self.timer.stop()
            self._next_image()
        elif event == Action.PLAY:
            if self.timer.isActive():
                self.timer.stop()
            elif self._next_image():
                self.timer.start()
        elif event == Action.SHUFFLE:
            new_shuffle = not self.playlist.is_shuffled()
            Settings.set_shuffle(new_shuffle)
            self.playlist.shuffle(new_shuffle)
        elif event == Action.LOOP:
            new_loop = not self.playlist.is_looped()
            Settings.set_loop(new_loop)
            self.playlist.loop(new_loop)
        elif event == Action.OPTIONS:
            dialog = ImagePlaySettings()
            dialog.setting_changed_event.connect(self._settings_changed)
            dialog.exec()
        elif event == Action.ZOOM_IN:
            self.imageView.zoom_in()
        elif event == Action.ZOOM_OUT:
            self.imageView.zoom_out()
        elif event == Action.SIZE:
            new_scaled = not self.imageView.is_scaled()
            Settings.set_image_scaled(new_scaled)
            self.imageView.set_scaled(new_scaled)
        elif event == Action.INFO:
            if self.info_dialog.isVisible():
                self.info_dialog.hide()
            else:
                self.info_dialog.open()
        elif event == Action.SEND:
            if self.imageView.current_file is not None and Settings.get_external_app() is not None:
                args = [Settings.get_external_app(), self.imageView.current_file]
                Imageplay.logger.info(f"Launching external app with args: {args}")
                subprocess.run(args)

        self.toolbar.toggle_action(event)

    def _next_image(self):
        try:
            if self.playlist.has_next():
                self.imageView.set_image(self.playlist.next())
                return True
            return False
        except PlaylistCompleteException:
            self.timer.stop()
            option = QMessageBox.question(self, "Playlist Finished", "Playlist finished. Start over?")
            if option == QMessageBox.Yes:
                self.playlist.reset()
                self.timer.start()
                self._next_image()
                return True
            return False

    def _animation_started(self):
        if self.timer.isActive():
            self.timer.pause()

    def _animation_stopped(self):
        if self.timer.isPaused():
            self._next_image()
            self.timer.start()

    def _image_changed(self, image_file):
        if self.info_dialog.isVisible():
            self.info_dialog.set_file(image_file)

    def _settings_changed(self, setting, value):
        if setting == Settings.SettingsKeys.image_delay:
            self.timer.setInterval(value * 1000)


def main():
    app = QApplication(sys.argv)
    _ = ImagePlayApp()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
