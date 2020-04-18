import datetime
import os
from enum import Enum

from PyQt5.QtCore import QRunnable, pyqtSignal, QThread, QThreadPool, QObject
from PyQt5.QtGui import QColor

from CommonUtils import ProcessRunner, ProcessRunnerException

available_encoders = {
    "Mp3 VBR Very High 220-260 kBit/s": {"command": "-codec:a libmp3lame -qscale:a 0", "extension": ".mp3"},
    "Mp3 VBR High 170-210 kBit/s": {"command": "-codec:a libmp3lame -qscale:a 2", "extension": ".mp3"},
    "Mp3 VBR Medium 140-185 kBit/s": {"command": "-codec:a libmp3lame -qscale:a 4", "extension": ".mp3"},
    "Mp3 VBR Low 100-130 kBit/s": {"command": "-codec:a libmp3lame -qscale:a 6", "extension": ".mp3"},
    "Mp3 VBR Acceptable 70k-105 kBit/s": {"command": "-codec:a libmp3lame -qscale:a 8", "extension": ".mp3"},

    "Mp3 CBR Very High 320 kBit/s": {"command": "-codec:a libmp3lame -b:a 320k", "extension": ".mp3"},
    "Mp3 CBR High 192 kBit/s": {"command": "-codec:a libmp3lame -b:a 192k", "extension": ".mp3"},
    "Mp3 CBR Medium 128 kBit/s": {"command": "-codec:a libmp3lame -b:a 128k", "extension": ".mp3"},
    "Mp3 CBR Low 96 kBit/s": {"command": "-codec:a libmp3lame -b:a 96k", "extension": ".mp3"},
    "Mp3 CBR Acceptable 48 kBit/s": {"command": "-codec:a libmp3lame -b:a 48k", "extension": ".mp3"},

    "Mp3 ABR Very High 320 kBit/s": {"command": "-codec:a libmp3lame -b:a 320k abr", "extension": ".mp3"},
    "Mp3 ABR High 192 kBit/s": {"command": "-codec:a libmp3lame -b:a 192k abr", "extension": ".mp3"},
    "Mp3 ABR Medium 128 kBit/s": {"command": "-codec:a libmp3lame -b:a 128k abr", "extension": ".mp3"},
    "Mp3 ABR Low 96 kBit/s": {"command": "-codec:a libmp3lame -b:a 96k abr", "extension": ".mp3"},
    "Mp3 ABR Acceptable 48 kBit/s": {"command": "-codec:a libmp3lame -b:a 48k abr", "extension": ".mp3"}
}


class EncodaStatus(Enum):
    READY = QColor(176, 224, 230, 50)
    WAITING = QColor(175, 238, 238, 75)
    SUCCESS = QColor(152, 251, 152, 75)
    ERROR = QColor(255, 192, 203, 75)

    def __init__(self, color):
        self.color = color


class EncodaCommandSignals(QObject):
    result = pyqtSignal('PyQt_PyObject')


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
              f" -loglevel repeat+verbose -y" \
              f" -i \"{self.input_file}\" {self.command} \"{self.output_file}\""

        # Start encoding
        start_time = datetime.datetime.now()
        print("Command to Exec: " + cmd)
        # time.sleep(5)
        try:
            ProcessRunner(cmd).run()
            end_time = datetime.datetime.now()
            self.signals.result.emit(
                self.create_result(EncodaStatus.SUCCESS, f"Time taken f{(end_time - start_time).total_seconds()}"))
        except ProcessRunnerException as e:
            self.signals.result.emit(
                self.create_result(EncodaStatus.ERROR, e.message))

    def create_result(self, status, messages):
        return {
            "input_file_name": self.input_file,
            "output_file_name": self.output_file,
            "command": self.command,
            "status": status,
            "messages": messages
        }



