import json
import subprocess
from json import JSONDecodeError

from PyQt5.QtCore import QModelIndex, Qt
from PyQt5.QtGui import QStandardItem, QStandardItemModel, QIcon
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTreeView, QLabel, QHBoxLayout

import Imageplay


class ImageDetails(QWidget):
    summary_keys = ["Composite:ImageSize",
                    "Composite:Megapixels",
                    "File:FileSize",
                    "File:FileModifyDate"]
    skip_keys = ["SourceFile", "ExifTool:ExifToolVersion"]
    exif_url = "https://www.sno.phy.queensu.ca/~phil/exiftool/"

    def __init__(self):
        super().__init__()
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderItem(0, QStandardItem("Property"))
        self.model.setHorizontalHeaderItem(1, QStandardItem("Value"))
        self.tree_view = QTreeView()
        self.tree_view.setModel(self.model)
        self.exiftool_installed, self.exiftool_version = ImageDetails.check_ver()
        if self.exiftool_installed:
            Imageplay.logger.info(f"ExifTool version {self.exiftool_version}")
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        if self.exiftool_installed:
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            layout.addWidget(self.tree_view)
        else:
            error_lbl = QLabel()
            error_ico = QIcon.fromTheme("dialog-error")
            error_lbl.setPixmap(error_ico.pixmap(32, 32))
            error_ttl = QLabel("<h3>ExifTool was not found on your System</h3>")
            error_ttl.setWordWrap(True)
            error_msg = QLabel(f"{Imageplay.__APP_NAME__} uses ExifTool in order to fetch details about the image."
                               f"<br>You can download ExifTool from <a href='{ImageDetails.exif_url}'>"
                               f"here!</a>")
            error_msg.setWordWrap(True)
            error_msg.setTextInteractionFlags(Qt.TextBrowserInteraction)
            error_msg.setOpenExternalLinks(True)
            hlayout = QHBoxLayout()
            hlayout.addWidget(error_lbl)
            hlayout.addWidget(error_ttl, 1)
            layout.addLayout(hlayout)
            layout.addWidget(error_msg, 1)

        self.setLayout(layout)

    def refresh_details(self, _, file):
        if not self.exiftool_installed:
            return

        # loosely based on https://github.com/smarnach/pyexiftool/blob/master/exiftool.py
        exitcode, err, out = ImageDetails.run_command(f"exiftool -G -j -sort '{file}'")
        try:
            data_dict = json.loads(out)
            self.display_details(data_dict[0])
        except JSONDecodeError as e:
            Imageplay.logger.error(e)

    def display_details(self, data_dict):
        self.model.removeRows(0, self.model.rowCount())
        self.model.beginInsertRows(QModelIndex(), 0, len(data_dict))
        self.create_summary(data_dict, self.model)

        roots = {}
        for key in data_dict:
            if ImageDetails.summary_keys.__contains__(key):
                continue
            if ImageDetails.skip_keys.__contains__(key):
                continue
            separator = key.find(":")
            if separator < 0:
                continue
            root = key[: separator]
            data_key = key[separator + 1:]
            root_item = roots[root] if roots.__contains__(root) else ImageDetails.create_item(root)
            root_item.appendRow([ImageDetails.create_item(f"{data_key}", isbold=True),
                                 ImageDetails.create_item(str(data_dict[key]))])
            roots[root] = root_item

        for key in roots:
            self.model.appendRow(roots[key])
        self.model.endInsertRows()

        proxy = self.tree_view.model()
        index = proxy.index(0, 0)
        self.tree_view.expand(index)
        self.tree_view.resizeColumnToContents(0)

    @staticmethod
    def create_item(string, isbold=False):
        item = QStandardItem(string)
        item.setEditable(False)
        if isbold:
            font = item.font()
            font.setBold(isbold)
            item.setFont(font)
        return item

    @staticmethod
    def create_summary(data_dict, model):
        for key in ImageDetails.summary_keys:
            model.appendRow([ImageDetails.create_item(f"{key[key.find(':') + 1:]}", isbold=True),
                             ImageDetails.create_item(str(data_dict[key]))])

    @staticmethod
    def check_ver():
        exitcode, err, out = ImageDetails.run_command("exiftool -ver")
        if exitcode != 0:
            Imageplay.logger.error(f"Exiftool was not found!! error is {err}")
            return False, ""
        return True, out

    @staticmethod
    def run_command(command):
        exitcode, err, out = 0, None, None
        try:
            out = subprocess.check_output(command,
                                          shell=True,
                                          stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            exitcode, err = e.returncode, e.output
        return exitcode, err, out
