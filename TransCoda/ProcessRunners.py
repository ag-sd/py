import datetime
import re
import shlex
import subprocess
from shutil import which

from PyQt5.QtCore import QObject, pyqtSignal


class HandbrakeProcessRunner(QObject):
    status_event = pyqtSignal(str, int, int)
    message_event = pyqtSignal(str, 'PyQt_PyObject', str)

    def __init__(self, input_file, output_file, base_command, delete_metadata=False):
        super().__init__()
        self.input_file = input_file
        self.output_file = output_file
        self.base_command = base_command
        self.delete_metadata = delete_metadata
        if which("HandBrakeCLI") is None:
            raise EncoderNotFoundException

    def run(self):
        process = subprocess.Popen(
            shlex.split(self.generate_command()),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )

        for line in process.stdout:
            self.message_event.emit(self.file_name, datetime.datetime.now(), line)
            progress = re.search("Encoding: task 1 of 1", line)
            if progress:
                txt = line.replace("Encoding: task 1 of 1, ", "")
                tokens = txt.split("%")
                print(f"PERCENT FOUND --> {tokens[0]}")
                self.status_event.emit(self.file_name, 100, float(tokens[0]))
            elif line.startswith("Encode done!"):
                print("ENCODING DONE")
                self.status_event.emit(self.file_name, 100, 100)

    def generate_command(self):
        pass


class FFMPEGProcessRunner(QObject):
    status_event = pyqtSignal(str, int, int)
    message_event = pyqtSignal(str, 'PyQt_PyObject', str)

    def __init__(self, input_file, output_file, base_command, delete_metadata=False):
        super().__init__()
        self.input_file = input_file
        self.output_file = output_file
        self.base_command = base_command
        self.delete_metadata = delete_metadata
        if which("ffmpeg") is None:
            raise EncoderNotFoundException

    def run(self):
        process = subprocess.Popen(
            shlex.split(self.generate_command()),
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )

        duration_found = False
        time_seeking = False
        total_secs = 0
        for line in process.stderr:
            self.message_event.emit(self.input_file, datetime.datetime.now(), line)
            if not duration_found:
                dur = re.search("duration: [0-9:]+", line.lower())
                if dur:
                    total_secs = self.get_seconds(dur.group(0)[10:])
                    duration_found = True
                    time_seeking = True
            elif time_seeking:
                time = re.search("time=[0-9:]+", line.lower())
                if time:
                    completed = self.get_seconds(time.group(0)[5:])
                    self.status_event.emit(self.input_file, total_secs, completed)

    @staticmethod
    def get_seconds(string):
        h, m, s = string.split(':')
        return int(datetime.timedelta(hours=int(h), minutes=int(m), seconds=int(s)).total_seconds())

    def generate_command(self):
        return f"ffmpeg" \
               f" -hide_banner -loglevel repeat+verbose -y" \
               f" {'-map_metadata -1' if self.delete_metadata else ''}" \
               f" -i \"{self.input_file}\" {self.base_command} \"{self.output_file}\""


class EncoderNotFoundException(Exception):
    """Thrown when FFMPEG was not found in the system"""


runners_registry = {
    "ffmpeg": FFMPEGProcessRunner,
    "HandbrakeCLI": HandbrakeProcessRunner
}