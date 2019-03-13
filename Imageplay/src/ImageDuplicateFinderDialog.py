import random
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QGroupBox, QHBoxLayout, QApplication, QComboBox, QVBoxLayout, QLabel, \
    QSlider, QPushButton, QFrame, QTableView, QHeaderView

from common.CommonUtils import FileScanner
from common.CustomUI import FileChooserListBox
from model.DuplicateImageDisplay import DuplicateImageDisplayModel, DuplicateImageDisplayDelegate
from runtime.ImageHash import DuplicateImageFinderRuntime


class ImageDuplicateFinderDialog(QDialog):

    _presets = [(2, 0), (3, 0), (4, 0), (5, 2), (6, 2),
                (7, 2), (8, 3), (9, 3), (10, 3), (11, 4)]

    def __init__(self):
        super().__init__()
        self.dir_chooser = FileChooserListBox("Select directories to scan...", True)
        self.algorithm = QComboBox()
        self.slider = QSlider(Qt.Horizontal)
        self.start_btn = QPushButton("Start")
        self.stop_btn = QPushButton("Stop")
        self.cue_label = QLabel("\n\n")
        self.image_display = QTableView()
        self.image_display_model = DuplicateImageDisplayModel()
        self._initUI()

        self.test_counter = 0

    def _initUI(self):
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

        self.start_btn.clicked.connect(self.start_btn_click)
        self.stop_btn.clicked.connect(self.stop_btn_click)
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)

        self.cue_label.setFrameShape(QFrame.Panel)
        self.cue_label.setFrameShadow(QFrame.Sunken)
        self.cue_label.setMinimumHeight(50)

        tool_layout = QVBoxLayout()
        tool_layout.addWidget(gb1)
        tool_layout.addWidget(QLabel("\nSearch Algorithm"))
        tool_layout.addWidget(self.algorithm)
        tool_layout.addWidget(QLabel("\nSearch Strictness"))
        tool_layout.addWidget(self.slider)
        tool_layout.addWidget(self.cue_label)
        tool_layout.addLayout(btn_layout)

        self.image_display.setShowGrid(False)
        self.image_display.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.image_display.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.image_display.horizontalHeader().hide()
        self.image_display.setModel(self.image_display_model)
        self.image_display.setItemDelegate(DuplicateImageDisplayDelegate())

        layout = QHBoxLayout()
        layout.addLayout(tool_layout)
        layout.addWidget(self.image_display, 1)
        self.setLayout(layout)

    def stop_btn_click(self):
        pass

    def dupes_found(self, cohort, files):
        self.image_display_model.add_items(cohort=cohort, items=files)

    def start_btn_click(self):
        # arr = []
        # for i in range(self.test_counter + 1):
        #     arr.append(f"Item {i}")
        # self.image_display_model.add_items(cohort=self.test_counter, items=arr)
        # self.test_counter += 1
        # self.image_display.update()

        # 1. Find all valid files in the chosen directories
        files_to_scan = FileScanner(self.dir_chooser.selection_as_qurls(), True, None).files
        # 2. Create a duplicate searcher and connect the duplicate signals
        dupe_finder = DuplicateImageFinderRuntime(files_to_scan)
        dupe_finder.dupes_found_event.connect(self.dupes_found)
        # 3. Get the algorithm and preset
        preset = self._presets[self.slider.value()]
        # 4. Start the runtime
        dupe_finder.start_duplicate_search(preset[0], preset[1], "foo")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ImageDuplicateFinderDialog()
    ex.show()
    sys.exit(app.exec_())
