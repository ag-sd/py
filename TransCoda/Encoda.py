import datetime
import os
from enum import Enum

from PyQt5.QtGui import QColor, QBrush

import CommonUtils
import TransCoda
from TransCoda import ProcessRunners, TransCodaSettings


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


class TranscodaError(Exception):
    """Thrown when Transcoda encounters an error"""


class EncodaCommand(CommonUtils.Command):

    def __init__(self, input_file):
        super().__init__()
        self.input_file = input_file

    def get_output_file(self, encoder):
        # Ensure the input file exists
        if not os.path.exists(self.input_file):
            raise TranscodaError("Input File could not be found on the file system")

        # Determine output file
        _, file_path = os.path.splitdrive(self.input_file)
        file_path, file = os.path.split(file_path)
        name, extension = os.path.splitext(file)

        output_dir = TransCodaSettings.get_output_dir() + file_path \
            if TransCodaSettings.get_preserve_dir() else TransCodaSettings.get_output_dir()

        if encoder["extension"] == "*":
            output_file = os.path.join(output_dir, name + extension)
        else:
            output_file = os.path.join(output_dir, name + encoder["extension"])

        # Overwrite if exists only
        if os.path.exists(output_file) and not TransCodaSettings.get_overwrite_if_exists():
            raise TranscodaError(f"Output file {output_file} already exists!")

        # Ensure path exists
        os.makedirs(output_dir, exist_ok=True)

        return output_file

    def do_work(self):
        start_time = datetime.datetime.now()
        encoder = TransCodaSettings.get_encoder()
        try:
            output_file = self.get_output_file(encoder)
        except Exception as g:
            self.emit_exception(start_time, g, None, None)
            return

        input_stat = os.stat(self.input_file)

        # Start encoding
        try:
            executable = encoder["executable"]
            if executable not in ProcessRunners.runners_registry:
                raise TranscodaError(f"Unable to find a process handler for executable {executable}")
            process_runner = ProcessRunners.runners_registry[executable]
            runner = process_runner(input_file=self.input_file,
                                    output_file=output_file,
                                    base_command=encoder["command"],
                                    delete_metadata=TransCodaSettings.get_delete_metadata())
            runner.status_event.connect(self.status_event)
            runner.message_event.connect(self.log_message)
            runner.run()
            end_time = datetime.datetime.now()
            cpu_time = (end_time - start_time).total_seconds()
            output_stat = os.stat(output_file)
            ratio = 100 - (output_stat.st_size / input_stat.st_size) * 100
            if TransCodaSettings.get_preserve_timestamps():
                os.utime(output_file, (input_stat.st_atime, input_stat.st_mtime))
            self.signals.result.emit(
                [self.create_result(EncodaStatus.SUCCESS,
                                    f"Time taken {CommonUtils.human_readable_time(cpu_time)}", cpu_time, ratio,
                                    CommonUtils.human_readable_filesize(output_stat.st_size), output_file, start_time,
                                    end_time, encoder["command"],
                                    CommonUtils.human_readable_filesize(input_stat.st_size))])
        except Exception as g:
            self.emit_exception(start_time, g, output_file, encoder["command"])

    def emit_exception(self, start_time, exception, output_file, encoder):
        end_time = datetime.datetime.now()
        cpu_time = (end_time - start_time).total_seconds()
        TransCoda.logger.exception(exception)
        input_stat = os.stat(self.input_file)
        self.signals.result.emit([self.create_result(EncodaStatus.ERROR, str(exception), cpu_time, 0, 0, output_file,
                                                     start_time, end_time, encoder,
                                                     CommonUtils.human_readable_filesize(input_stat.st_size))])

    def status_event(self, _file, total, completed):
        from TransCoda.MainPanel import ItemKeys
        self.signals.status.emit(
            {
                ItemKeys.input_file_name: _file,
                ItemKeys.percent_compete: f"{(completed / total * 100):.2f}%",
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

    def create_result(self, status, messages, cpu_time, compression_ratio, op_file_size, output_file, start_time,
                      end_time, encoder_command, input_size):
        from TransCoda.MainPanel import ItemKeys
        response = {
            ItemKeys.input_file_name: self.input_file,
            ItemKeys.output_file_name: output_file,
            ItemKeys.status: status,
            ItemKeys.messages: messages,
            ItemKeys.cpu_time: cpu_time,
            ItemKeys.compression_ratio: compression_ratio,
            ItemKeys.output_file_size: op_file_size,
            ItemKeys.input_file_size: input_size,
            ItemKeys.start_time: start_time,
            ItemKeys.end_time: end_time,
            ItemKeys.encoder_command: encoder_command
        }
        if status == EncodaStatus.SUCCESS:
            response.update({
                ItemKeys.percent_compete: "100%"
            })
        return response
