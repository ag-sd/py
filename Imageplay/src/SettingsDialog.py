from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QHBoxLayout, QSpinBox, QLabel, QVBoxLayout, QCheckBox

import Imageplay


class SettingsDialog(QDialog):

    def __init__(self):
        super().__init__()
        self.imageSpinner = QSpinBox()
        self.imageSpinner.setMinimum(1)
        self.imageSpinner.setValue(Imageplay.settings.get_setting("image_delay", 3000) / 1000)
        self.imageSpinner.valueChanged.connect(self.image_delay_change)
        self.gifSpinner = QSpinBox()
        self.gifSpinner.setMinimum(1)
        self.gifSpinner.setValue(Imageplay.settings.get_setting("gif_delay", 1000) / 1000)
        self.gifSpinner.valueChanged.connect(self.animation_delay_change)
        self.recurse = QCheckBox("Add all child folders when a directory is added")
        self.recurse.setChecked(Imageplay.settings.get_setting("recurse_subdirs", False))
        self.recurse.stateChanged.connect(self.recurse_change)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.addLayout(self.createSpinnerLayout("Load next image in (seconds)", self.imageSpinner))
        layout.addLayout(self.createSpinnerLayout("Load next animation in (seconds)", self.gifSpinner))
        layout.addWidget(self.recurse)

        self.setLayout(layout)
        self.setWindowTitle("Configure Imageplay")
        self.setWindowModality(Qt.ApplicationModal)

    @staticmethod
    def createSpinnerLayout(label, spinbox):
        layout = QHBoxLayout()
        layout.addWidget(QLabel(label))
        layout.addStretch(1)
        layout.addWidget(spinbox)
        return layout

    @staticmethod
    def image_delay_change(delay):
        Imageplay.settings.apply_setting("image_delay", delay * 1000)

    @staticmethod
    def animation_delay_change(delay):
        Imageplay.settings.apply_setting("gif_delay", delay * 1000)

    def recurse_change(self):
        Imageplay.settings.apply_setting("recurse_subdirs", self.recurse.isChecked())



