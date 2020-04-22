import datetime
import os
import re
import shlex
import subprocess
from enum import Enum
from shutil import which

from PyQt5.QtCore import QRunnable, pyqtSignal, QObject
from PyQt5.QtGui import QColor, QBrush

from CommonUtils import ProcessRunnerException


class Encoders(Enum):
    __lookup__ = {}

    Mp3_VBR_Very_High_220_to_260_kBits = "-codec:a libmp3lame -qscale:a 0", ".mp3"
    Mp3_VBR_High_170_to_210_kBits = "-codec:a libmp3lame -qscale:a 2", ".mp3"
    Mp3_VBR_Medium_140_to_185_kBits = "-codec:a libmp3lame -qscale:a 4", ".mp3"
    Mp3_VBR_Low_100_to_130_kBits = "-codec:a libmp3lame -qscale:a 6", ".mp3"
    Mp3_VBR_Acceptable_70k_to_105_kBits = "-codec:a libmp3lame -qscale:a 8", ".mp3"

    Mp3_CBR_Very_High_320_kBits = "-codec:a libmp3lame -b:a 320k", ".mp3"
    Mp3_CBR_High_192_kBits = "-codec:a libmp3lame -b:a 192k", ".mp3"
    Mp3_CBR_Medium_128_kBits = "-codec:a libmp3lame -b:a 128k", ".mp3"
    Mp3_CBR_Low_96_kBits = "-codec:a libmp3lame -b:a 96k", ".mp3"
    Mp3_CBR_Acceptable_48_kBits = "-codec:a libmp3lame -b:a 48k", ".mp3"

    Mp3_ABR_Very_High_320_kBits = "-codec:a libmp3lame -b:a 320k abr", ".mp3"
    Mp3_ABR_High_192_kBits = "-codec:a libmp3lame -b:a 192k abr", ".mp3"
    Mp3_ABR_Medium_128_kBits = "-codec:a libmp3lame -b:a 128k abr", ".mp3"
    Mp3_ABR_Low_96_kBits = "-codec:a libmp3lame -b:a 96k abr", ".mp3"
    Mp3_ABR_Acceptable_48_kBits = "-codec:a libmp3lame -b:a 48k abr", ".mp3"

    def __init__(self, command, extension):
        self.command = command
        self.extension = extension
        self.__class__.__lookup__[self.__str__()] = self

    def __str__(self):
        return self.name.replace("_", " ")


class EncodaStatus(Enum):
    READY = QBrush(QColor(176, 224, 230, 0))
    WAITING = QBrush(QColor(175, 238, 238, 75))
    SUCCESS = QBrush(QColor(152, 251, 152, 75))
    ERROR = QBrush(QColor(255, 192, 203, 75))

    def __init__(self, brush):
        self.brush = brush


class EncodaCommandSignals(QObject):
    result = pyqtSignal('PyQt_PyObject')
    status = pyqtSignal(str, int, int)


class EncodaCommand(QRunnable):

    def __init__(self, input_file, output_file, command):
        super().__init__()
        self.input_file = input_file
        self.output_file = output_file
        self.command = command
        self.signals = EncodaCommandSignals()

    def run(self):
        # Ensure the input file exists
        if not os.path.exists(self.input_file):
            self.signals.result.emit(self.create_result(EncodaStatus.ERROR, "Input file missing!"))
            return
        # Ensure output path exists
        path, file = os.path.split(self.output_file)
        os.makedirs(path, exist_ok=True)

        # Generate the command
        cmd = f"ffmpeg" \
              f" -hide_banner -loglevel repeat+verbose -y" \
              f" -i \"{self.input_file}\" {self.command} \"{self.output_file}\""

        # Start encoding
        start_time = datetime.datetime.now()
        #print("Command to Exec: " + cmd)
        # time.sleep(5)
        try:
            ffmpeg = FFMPEGProcessRunner(self.input_file, cmd)
            ffmpeg.status_event.connect(self.status_event)
            ffmpeg.run()
            end_time = datetime.datetime.now()
            self.signals.result.emit(
                self.create_result(cmd, EncodaStatus.SUCCESS, f"Time taken f{(end_time - start_time).total_seconds()}"))
        except ProcessRunnerException as e:
            self.signals.result.emit(
                self.create_result(cmd, EncodaStatus.ERROR, e.message))

    def status_event(self, file, total, completed):
        self.signals.status.emit(file, total, completed)

    def create_result(self, cmd, status, messages):
        from TransCoda.MainPanel import ItemKeys
        return {
            ItemKeys.input_file_name: self.input_file,
            ItemKeys.output_file_name: self.output_file,
            ItemKeys.encoder_command: cmd,
            ItemKeys.status: status,
            ItemKeys.messages: messages
        }


class FFMPEGNotFoundException(Exception):
    """Thrown when FFMPEG was not found in the system"""


class FFMPEGProcessRunner(QObject):
    status_event = pyqtSignal(str, int, int)

    def __init__(self, file_name, command):
        super().__init__()
        self.file_name = file_name
        self.command = command
        if which("ffmpeg") is None:
            raise FFMPEGNotFoundException

    def run(self):
        process = subprocess.Popen(
            shlex.split(self.command),
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )

        duration_found = False
        time_seeking = False
        total_secs = 0
        for line in process.stderr:
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
                    self.status_event.emit(self.file_name, total_secs, completed)

    @staticmethod
    def get_seconds(string):
        h, m, s = string.split(':')
        return int(datetime.timedelta(hours=int(h), minutes=int(m), seconds=int(s)).total_seconds())

