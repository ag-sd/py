import datetime
import re
import shlex
import shutil
import subprocess
from shutil import which

from PyQt5.QtCore import QObject, pyqtSignal


class ProcessRunner(QObject):
    status_event = pyqtSignal(str, int, int)
    message_event = pyqtSignal(str, 'PyQt_PyObject', str)

    def __init__(self, **kwargs):
        super().__init__()
        self.__dict__.update(kwargs)


class FileCopyProcessRunner(ProcessRunner):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def run(self):
        shutil.copy(src=self.input_file, dst=self.output_file, follow_symlinks=True)
        self.status_event.emit(self.input_file, 100, 100)


class FFMPEGProcessRunner(ProcessRunner):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if which("ffmpeg") is None:
            raise EncoderNotFoundException

    def run(self):
        command = self.generate_command()
        self.message_event.emit(self.input_file, datetime.datetime.now(), command)
        process = subprocess.Popen(
            shlex.split(command),
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


class HandbrakeProcessRunner(ProcessRunner):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if which("HandBrakeCLI") is None:
            raise EncoderNotFoundException

    def run(self):
        command = self.generate_command()
        self.message_event.emit(self.input_file, datetime.datetime.now(), command)
        process = subprocess.Popen(
            shlex.split(command),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )

        for line in process.stdout:
            self.message_event.emit(self.input_file, datetime.datetime.now(), line)
            progress = re.search("Encoding: task 1 of 1", line)
            if progress:
                txt = line.replace("Encoding: task 1 of 1, ", "")
                tokens = txt.split("%")
                self.status_event.emit(self.input_file, 100, float(tokens[0]))
            elif line.startswith("Encode done!"):
                self.status_event.emit(self.input_file, 100, 100)

    def generate_command(self):
        return f"HandBrakeCLI"\
               f" -i \"{self.input_file}\" {self.base_command} -o \"{self.output_file}\""


class EncoderNotFoundException(Exception):
    """Thrown when FFMPEG was not found in the system"""


runners_registry = {
    "ffmpeg": FFMPEGProcessRunner,
    "HandBrakeCLI": HandbrakeProcessRunner,
    "copy": FileCopyProcessRunner
}