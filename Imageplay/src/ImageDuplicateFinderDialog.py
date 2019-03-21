import sys, datetime

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QDialog, QGroupBox, QHBoxLayout, QApplication, QComboBox, QVBoxLayout, QLabel, \
    QSlider, QPushButton, QProgressBar, QStatusBar, QTabWidget, QWidget

import Imageplay
from Imageplay import SettingsKeys
from common.CommonUtils import FileScanner
from common.CustomUI import FileChooserListBox
from model.ThumbnailGrid import ThumbnailView
from runtime.ImageHash import DuplicateImageFinderRuntime


class ImageDuplicateFinderDialog(QDialog):

    _presets = [(15, 3), (15, 3), (15, 3), (20, 5), (20, 5),
                (20, 5), (25, 10), (25, 10), (25, 10), (25, 10)]
    _PIL_UNSUPPORTED_FORMATS = ['.CUR', '.PBM', '.PGM', '.SVG', '.SVGZ', '.WBMP', '.WEBP']

    def __init__(self):
        super().__init__()
        self.dir_chooser = FileChooserListBox("Select directories to scan...", True)
        self.algorithm = QComboBox()
        self.slider = QSlider(Qt.Horizontal)
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.start_btn = QPushButton("Start")
        self.stop_btn = QPushButton("Stop")
        self.cue_current_file = QLabel("")
        self.cue_current_count = QLabel("Files Scanned\t:")
        self.cue_total_count = QLabel("Total Count\t:")
        self.cue_dupes_found = QLabel("Duplicate Files\t:")
        self.cue_dupe_groups = QLabel("Duplicate Groups\t:")
        self.cue_threads = QLabel("Threads\t\t:")
        self.cue_time_taken = QLabel("Time Taken\t:")
        self.cue_time_remaining = QLabel("Time Remaining\t:")
        self.image_grid = ThumbnailView()
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.timer = QTimer()
        self.timer_ticks = 0
        self.total_files = 0
        self.scanned_files = 0
        self._initUI()
        self.dupe_finder = None

    def _initUI(self):
        tab_widget = QTabWidget()
        tab_widget.addTab(self.setup_select_options(), "Select")
        tab_widget.addTab(self.setup_scan_options(), "Scan")
        tab_widget.addTab(QWidget(), "Review")

        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(5, 5, 5, 0)
        h_layout.addWidget(tab_widget)
        h_layout.addWidget(self.image_grid, 1)

        self.zoom_slider.setMinimum(0)
        self.zoom_slider.setMaximum(15)
        self.zoom_slider.valueChanged.connect(self.zoom_slider_scroll)
        self.zoom_slider.setValue(Imageplay.settings.get_setting(SettingsKeys.dupe_image_view_zoom, 5))

        status_bar = QStatusBar()
        status_bar.addWidget(QWidget(), 1)
        status_bar.addWidget(self.zoom_slider)

        v_layout = QVBoxLayout()
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.addLayout(h_layout)
        v_layout.addWidget(status_bar)

        self.timer.timeout.connect(self.timer_timeout)

        self.setLayout(v_layout)

    def setup_scan_options(self):
        self.start_btn.clicked.connect(self.start_btn_click)
        self.stop_btn.clicked.connect(self.stop_btn_click)
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)

        l1 = QVBoxLayout()
        l1.addWidget(self.cue_current_file)
        l1.addWidget(self.cue_current_count)
        l1.addWidget(self.cue_total_count)
        l1.addWidget(self.cue_dupes_found)
        l1.addWidget(self.cue_dupe_groups)
        l1.addWidget(self.cue_time_taken)
        l1.addWidget(self.cue_time_remaining)
        l1.addWidget(self.cue_threads)
        l1.addWidget(QWidget(), 1)
        l1.addWidget(self.progress_bar)

        gb1 = QGroupBox("Scan Details")
        gb1.setLayout(l1)

        tool_layout = QVBoxLayout()
        tool_layout.addWidget(gb1)
        tool_layout.addLayout(btn_layout)

        widget = QWidget()
        widget.setLayout(tool_layout)
        return widget

    def setup_select_options(self):
        l1 = QHBoxLayout()
        l1.addWidget(self.dir_chooser)
        l1.setContentsMargins(0, 0, 0, 0)
        gb1 = QGroupBox("Directories to scan")
        gb1.setLayout(l1)

        self.algorithm.addItems(["Average Hash", "Perception Hash", "Difference Hash", "Wavelet Hash"])
        self.algorithm.setEditable(False)

        self.slider.setMaximum(10)
        self.slider.setMinimum(0)
        self.slider.setValue(5)
        self.slider.setTickPosition(QSlider.TicksBelow)

        tool_layout = QVBoxLayout()
        tool_layout.addWidget(gb1)
        tool_layout.addWidget(QLabel("\nSearch Algorithm"))
        tool_layout.addWidget(self.algorithm)
        tool_layout.addWidget(QLabel("\nSearch Strictness"))
        tool_layout.addWidget(self.slider)

        widget = QWidget()
        widget.setLayout(tool_layout)
        return widget

    def timer_timeout(self):
        self.timer_ticks += 1
        if self.scanned_files > 0:
            time_per_file = self.timer_ticks / self.scanned_files
            projected = time_per_file * (self.total_files - self.scanned_files)
            self.cue_time_remaining.setText(f"Time Remaining\t: {str(datetime.timedelta(seconds=projected))}")
            self.cue_time_taken.setText(f"Time Elapsed\t: {str(datetime.timedelta(seconds=self.timer_ticks))}")
        else:
            self.cue_time_remaining.setText(f"Time Remaining\t: 0:00:00")
            self.cue_time_taken.setText(f"Time Elapsed\t: 0:00:00")

    def stop_btn_click(self):
        if self.dupe_finder is not None:
            self.dupe_finder.stop_scan()

    def dupes_found(self, cohort, files):
        self.image_grid.add_items(index=cohort, data=files)

    def scan_status(self, current_file, current_count, total_files, active_threads,
                    total_threads, duplicate_pictures, duplicate_groups):
        elided_text = self.cue_current_file.fontMetrics().elidedText(current_file, Qt.ElideLeft,
                                                                     self.cue_current_file.width() - 10)
        self.cue_current_file.setText(elided_text)
        self.cue_threads.setText(f"Threads\t\t: {active_threads} / {total_threads}")
        self.cue_dupe_groups.setText(f"Duplicate Groups\t: {duplicate_groups}")
        self.cue_dupes_found.setText(f"Duplicate Files\t: {duplicate_pictures}")
        self.cue_total_count.setText(f"Total Count\t: {total_files}")
        self.cue_current_count.setText(f"Files Scanned\t: {current_count}")

        self.progress_bar.setValue((current_count / total_files) * 100)

        self.total_files = total_files
        self.scanned_files = current_count

    def scan_finish(self):
        Imageplay.logger.info("Scan complete!")
        self.dupe_finder.wait()
        self.dupe_finder = None
        self.toggle_scan(starting=False)
        # self.cue_label.setText("")
        self.timer.stop()
        self.cue_time_remaining.setText(f"Time Remaining\t: 0:00:00")

    def start_btn_click(self):
        self.toggle_scan(starting=True)
        # 1. Find all valid files in the chosen directories
        app_formats = set(Imageplay.supported_formats) - set(self._PIL_UNSUPPORTED_FORMATS)
        files_to_scan = FileScanner(self.dir_chooser.selection_as_qurls(), True, app_formats).files
        # 2. Get the algorithm and preset
        preset = self._presets[self.slider.value()]
        # 3. Create a duplicate searcher and connect the signals

        # from ImagePlayApp import ImagePlayApp
        # files, start_file = ImagePlayApp.parse_args()
        # urls = []
        # for file in files:
        #     urls.append(QUrl.fromLocalFile(file))
        # found_files = FileScanner(urls, True, None).files
        self.dupe_finder = DuplicateImageFinderRuntime(files_to_scan, preset[0], preset[1], "foo")
        self.dupe_finder.dupes_found_event.connect(self.dupes_found)
        self.dupe_finder.scan_status_event.connect(self.scan_status)
        self.dupe_finder.scan_finish_event.connect(self.scan_finish)
        # 4. Start the runtime
        self.timer.start(1000)
        self.dupe_finder.start()

    def zoom_slider_scroll(self, value):
        Imageplay.settings.apply_setting(SettingsKeys.dupe_image_view_zoom, value)
        self.image_grid.zoom((value + 1) * 16)

    def toggle_scan(self, starting=False):
        self.start_btn.setEnabled(not starting)
        self.stop_btn.setEnabled(starting)
        self.dir_chooser.setEnabled(not starting)
        self.algorithm.setEnabled(not starting)
        self.slider.setEnabled(not starting)
        self.progress_bar.setVisible(starting)
        if starting:
            self.image_grid.clear()
            self.timer_ticks = 0
            self.total_files = 0
            self.scanned_files = 0


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ImageDuplicateFinderDialog()
    ex.show()
    sys.exit(app.exec_())
