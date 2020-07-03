import datetime
import os
from enum import Enum

from PyQt5.QtGui import QColor, QBrush

import CommonUtils
import TransCoda
from TransCoda import ProcessRunners
from TransCoda.ProcessRunners import FFMPEGProcessRunner


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
    READY = 176, 224, 230, 0, True
    WAITING = 255, 140, 0, 50, True
    SUCCESS = 152, 251, 152, 75, True
    ERROR = 220, 20, 60, 75, True
    IN_PROGRESS = 244, 164, 96, 75, True
    READING_METADATA = 192, 192, 192, 255, False

    def __init__(self, r, g, b, a, is_background):
        self.brush = QBrush(QColor(r, g, b, a))
        self.is_background = is_background
        self.is_foreground = not is_background

    def __str__(self):
        return self.name


class EncodaCommand(CommonUtils.Command):

    def __init__(self, input_file, output_file, command,
                 overwrite_if_exists=True,
                 preserve_timestamps=False,
                 delete_metadata=False):
        super().__init__()
        self.input_file = input_file
        self.output_file = output_file
        self.command = command
        self.overwrite_if_exists = overwrite_if_exists
        self.preserve_timestamps = preserve_timestamps
        self.delete_metadata = delete_metadata

    def do_work(self):
        start_time = datetime.datetime.now()
        # Ensure the input file exists
        if not os.path.exists(self.input_file):
            self.signals.result.emit(self.create_result(EncodaStatus.ERROR, "Input file missing!"))
            return
        # Ensure output path exists
        path, _ = os.path.split(self.output_file)
        # Overwrite if exists only
        if os.path.exists(self.output_file) and not self.overwrite_if_exists:
            cpu_time = (datetime.datetime.now() - start_time).total_seconds()
            self.signals.result.emit(
                [self.create_result("", EncodaStatus.ERROR, f"{self.output_file} exists", cpu_time, 0, 0)])
            return
        os.makedirs(path, exist_ok=True)
        # Input file details
        input_stat = os.stat(self.input_file)

        # Start encoding
        try:
            process_runner = ProcessRunners.runners_registry["ffmpeg"]
            encoder = process_runner(input_file=self.input_file,
                                     output_file=self.output_file,
                                     base_command=self.command,
                                     delete_metadata=self.delete_metadata)
            encoder.status_event.connect(self.status_event)
            encoder.message_event.connect(self.log_message)
            encoder.run()
            cpu_time = (datetime.datetime.now() - start_time).total_seconds()
            output_stat = os.stat(self.output_file)
            ratio = 100 - (output_stat.st_size / input_stat.st_size) * 100
            if self.preserve_timestamps:
                os.utime(self.output_file, (input_stat.st_atime, input_stat.st_mtime))
            self.signals.result.emit(
                [self.create_result(EncodaStatus.SUCCESS,
                                    f"Time taken {CommonUtils.human_readable_time(cpu_time)}",
                                    cpu_time, ratio, output_stat.st_size)])
        except Exception as g:
            cpu_time = (datetime.datetime.now() - start_time).total_seconds()
            TransCoda.logger.error(g)
            self.signals.result.emit([self.create_result(EncodaStatus.ERROR, str(g), cpu_time, 0, 0)])

    def status_event(self, _file, total, completed):
        from TransCoda.MainPanel import ItemKeys
        self.signals.status.emit(
            {
                ItemKeys.input_file_name: _file,
                ItemKeys.percent_compete: f"{(completed/total * 100):.2f}%",
                ItemKeys.status: EncodaStatus.IN_PROGRESS
            }
        )

    def log_message(self, _file, time, message):
        self.signals.log_message.emit(
            {
                "file": _file,
                "time": time,
                "message": message
            }
        )

    def create_result(self, status, messages, cpu_time, compression_ratio, op_file_size):
        from TransCoda.MainPanel import ItemKeys
        response = {
            ItemKeys.input_file_name: self.input_file,
            ItemKeys.output_file_name: self.output_file,
            ItemKeys.status: status,
            ItemKeys.messages: messages,
            ItemKeys.cpu_time: cpu_time,
            ItemKeys.compression_ratio: compression_ratio,
            ItemKeys.output_file_size: op_file_size
        }
        if status == EncodaStatus.SUCCESS:
            response.update({
                ItemKeys.percent_compete: "100%"
            })
        return response


