import hashlib
import itertools
import subprocess
import sys
import tempfile
from datetime import datetime
from os import path
import shlex
from shutil import which

from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QMainWindow, QTextEdit, QHBoxLayout, QWidget, QApplication, QPushButton, QVBoxLayout

import CommonUtils
from CommonUtils import Command
from CustomUI import DropZone

from PIL import Image

__working_dir__ = "/mnt/dev/testing/duplo"


class BaseCommand(Command):
    def __init__(self, input_file):
        super().__init__()
        self.input_file = input_file
        if which("convert") is None:
            raise Exception("Convert Not found")

    def do_work(self):
        output_file = self.get_output_file()
        commands = self.generate_commands(output_file)
        self.signals.status.emit(f"{datetime.now()} -- {self.input_file} >> {commands}")
        self.run_commands(commands)
        self.post_processing(output_file)

    def get_output_file(self, suffix="") -> str:
        file_path, file_name = path.split(self.input_file)
        file_name, extension = path.splitext(file_name)
        md5_hash = hashlib.md5(file_path.encode('utf-8')).hexdigest()
        return f"{__working_dir__}{path.sep}{md5_hash}_{file_name}{suffix}{extension}"

    def generate_commands(self, output_file) -> list:
        return [f"echo {output_file}"]

    def run_commands(self, commands):
        for command in commands:
            print(command)
            process = subprocess.Popen(
                shlex.split(command),
                stdin=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

            for line in process.stderr:
                self.signals.status.emit(line)

    def post_processing(self, output_file: str):
        pass


class HistogramGenerator(BaseCommand):
    def generate_commands(self, output_file):
        tmp_dir = tempfile.gettempdir()
        _, file_name = path.split(output_file)
        tmp_file = path.join(tmp_dir, file_name)
        return [
            # f"convert '{self.input_file}' -verbose -define histogram:unique-colors=false histogram:'{tmp_file}'",
            # f"convert '{tmp_file}' -resize 50x50! {output_file}",
            # f"rm {tmp_file}"
            f"convert '{self.input_file}' -verbose -brightness-contrast 0x100 -colorspace Gray  -resize 32x32! -blur 2x1 -write '{output_file}-2.jpg-mask'"
            ,
            f"convert '{self.input_file}' -verbose -brightness-contrast 0x100 -colorspace Gray  -resize 32x32! -blur 4x2 -write '{output_file}-4.jpg-mask'"
            ,
            f"convert '{self.input_file}' -verbose -brightness-contrast 0x100 -colorspace Gray  -resize 32x32! -blur 8x3 -write '{output_file}-8.jpg-mask'"
            ,
            f"convert '{self.input_file}' -verbose -brightness-contrast 0x100 -colorspace Gray  -resize 32x32! -blur 16x4 -write '{output_file}-16.jpg-mask'"
            ,
            f"convert '{self.input_file}' -verbose -brightness-contrast 0x100 -colorspace Gray  -resize 32x32! -blur 32x5 -write '{output_file}-32.jpg-mask'"
            ,
        ]
    
    def get_output_file(self, suffix="") -> str:
        return super().get_output_file(suffix="-histogram")


class MetaImageGenerator(BaseCommand):
    def generate_commands(self, output_file):
        _, file_name = path.split(output_file)
        return [
            # f"convert '{self.input_file}' -auto-level -colorspace Gray -brightness-contrast 0x100 -resize 20x20! -verbose {output_file}"
            f"convert '{self.input_file}' -verbose -write MPR:{file_name} -auto-level -colorspace Gray "
            f"-brightness-contrast 0x100 -resize 20x20! -write '{output_file}-mask' "
            f"-delete 0--1 MPR:{file_name} "
            f"-resize 96^x96^ -write '{output_file}-thumb'"
        ]

    def post_processing(self, output_file: str):
        """
        Use image to create tiles
        each tile returns either back or white
        collection of tiles = fingerprint
        if resolution  = 1, 400 tiles
        2 -> 200 tiles
        4 -> 100 tiles
        5 -> 80 tiles

        :param output_file:
        :return:
        """
        im = Image.open(f"{output_file}-mask")
        normalized = []
        for pixel in im.getdata():
            if pixel < 128:
                pixel = 0
            elif pixel >= 128:
                pixel = 1
            normalized.append(pixel)
        rle = ((x, sum(1 for _ in y)) for x, y in itertools.groupby(normalized))
        print(rle)




class ImageHash(QObject):
    def __init__(self, files, tightness=100):
        super().__init__()
        self.tightness = self._get_tightness(tightness)
        self.files = files

    def scan(self):
        pass

    @staticmethod
    def _get_tightness(value):
        tightness = (value * 20) / 100
        if tightness <= 10:
            tightness = 10
        elif tightness >= 30:
            tightness = 30
        return tightness


class DuploApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.dropZone = DropZone()
        self.logBox = QTextEdit()
        self.btn = QPushButton("Start")
        self.executor = None
        self.init_ui()

    def init_ui(self):
        self.dropZone.files_dropped_event.connect(self._collect_files)
        base_layout = QHBoxLayout()
        base_layout.addWidget(self.dropZone)
        base_layout.addWidget(self.logBox)

        ctrl_layout = QVBoxLayout()
        ctrl_layout.addLayout(base_layout)
        ctrl_layout.addWidget(self.btn)

        dummy_widget = QWidget()
        dummy_widget.setLayout(ctrl_layout)

        self.setCentralWidget(dummy_widget)
        self.setMinimumWidth(1724)
        self.setMinimumHeight(768)
        self.show()

    def _collect_files(self):
        print(f"files dropped {self.dropZone.dropped_files}")

        source_scanner = CommonUtils.FileScanner(self.dropZone.dropped_files, recurse=True, is_qfiles=True)
        tasks = []
        for file in source_scanner.files:
            # runnable_t = ThumbnailGenerator(input_file=file)
            # runnable_t.signals.result.connect(self.result_received_event)
            # runnable_t.signals.status.connect(self.status_received_event)
            runnable_h = HistogramGenerator(input_file=file)
            runnable_h.signals.result.connect(self.result_received_event)
            runnable_h.signals.status.connect(self.status_received_event)
            runnable_m = MetaImageGenerator(input_file=file)
            runnable_m.signals.result.connect(self.result_received_event)
            runnable_m.signals.status.connect(self.status_received_event)
            # tasks.append(runnable_t)
            tasks.append(runnable_h)
            tasks.append(runnable_m)

        self.executor = CommonUtils.CommandExecutionFactory(tasks)
        self.executor.finish_event.connect(self.jobs_complete_event)
        self.executor.start()

    def jobs_complete_event(self):
        print("Jobs Complete")

    def result_received_event(self, result):
        print(result)

    def status_received_event(self, status):
        print(status)


def main():
    app = QApplication(sys.argv)
    ex = DuploApp()
    sys.exit(app.exec_())


if __name__ == '__main__':
    # main()
    HistogramGenerator("/mnt/dev/testing/duplo/Samples/SIMILAR_IMG_5244.JPG").run()
    HistogramGenerator("/mnt/dev/testing/duplo/Samples/SIMILAR_IMG_5245.JPG").run()
    # MetaImageGenerator("/home/sheldon/Desktop/to-dedup/x/20230406_082110.jpg").run()
