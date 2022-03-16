import datetime
import os
from enum import Enum

import CommonUtils
import TransCoda
from TransCoda.ui import TransCodaSettings
from TransCoda.core import ProcessRunners


class EncoderStatus(Enum):
    READY = 1
    WAITING = 2
    SUCCESS = 3
    ERROR = 4
    IN_PROGRESS = 5
    READING_METADATA = 6
    UNSUPPORTED = 7
    SKIPPED = 8
    REMOVE = 9

    def __str__(self):
        return self.name


class TranscodaError(Exception):
    """Thrown when Transcoda encounters an error"""


class EncoderCommand(CommonUtils.Command):

    def __init__(self, file_item):
        super().__init__()
        self.file = file_item

    def work_size(self):
        return 1

    def do_work(self):
        self.file.encode_start_time = datetime.datetime.now()
        encoder = self.file.encoder_props
        try:
            self._check_file()
        except Exception as exception:
            self.emit_exception(exception)
            return

        # Start encoding
        try:
            if not self.file.is_supported():
                copy_extensions = TransCodaSettings.get_copy_extensions()
                _, extension = os.path.splitext(self.file.output_file)
                if extension.startswith("."):
                    extension = extension[1:]
                if extension in copy_extensions:
                    executable = "copy"
                else:
                    self.file.status = EncoderStatus.SKIPPED
                    self.signals.result.emit([self.file])
                    return
            else:
                executable = encoder["executable"]
                self.file.encode_command = encoder["command"]
                if executable not in ProcessRunners.runners_registry:
                    raise TranscodaError(f"Unable to find a process handler for executable {executable}")

            process_runner = ProcessRunners.runners_registry[executable]
            runner = process_runner(input_file=self.file.file,
                                    input_url=self.file.url,
                                    output_file=self.file.output_file,
                                    base_command=self.file.encode_command,
                                    delete_metadata=TransCodaSettings.get_delete_metadata())
            runner.status_event.connect(self.status_event)
            runner.message_event.connect(self.log_message)
            runner.run()
            output_stat = os.stat(self.file.output_file)
            if TransCodaSettings.get_preserve_timestamps():
                os.utime(self.file.output_file, (self.file.access_time, self.file.modify_time))
            self.file.encode_end_time = datetime.datetime.now()
            self.file.encode_cpu_time = (self.file.encode_end_time - self.file.encode_start_time).total_seconds()
            self.file.encode_compression_ratio = 100 - (output_stat.st_size / (self.file.file_size + 1)) * 100
            self.file.status = EncoderStatus.SUCCESS
            self.file.encode_output_size = output_stat.st_size
            self.file.encode_percent = 100
            self.signals.result.emit([self.file])
        except Exception as exception:
            self.emit_exception(exception)

    def emit_exception(self, exception):
        self.file.encode_end_time = datetime.datetime.now()
        self.file.encode_cpu_time = (self.file.encode_end_time - self.file.encode_start_time).total_seconds()
        TransCoda.logger.exception(exception)
        self.file.status = EncoderStatus.ERROR
        self.file.encode_messages = str(exception)
        self.signals.result.emit([self.file])

    def status_event(self, _file, total, completed):
        self.file.encode_percent = (completed / total) * 100
        self.file.status = EncoderStatus.IN_PROGRESS
        self.signals.status.emit(self.file)

    def log_message(self, _file, time, message):
        self.signals.log_message.emit(
            {
                "file": _file,
                "time": time,
                "message": message
            }
        )

    def _check_file(self):
        if not os.path.exists(self.file.file):
            raise TranscodaError("Input File could not be found on the file system")

        # Overwrite if exists only
        if os.path.exists(self.file.output_file) and not TransCodaSettings.get_overwrite_if_exists():
            raise TranscodaError(f"Output file {self.file.output_file} already exists!")

        # Ensure path exists
        if self.file.encoder_props["extension"] == "":
            file_path = self.file.output_file
        else:
            file_path, _ = os.path.split(self.file.output_file)
        os.makedirs(file_path, exist_ok=True)

        # Check History
        if self.file.history_result is not None and TransCodaSettings.is_history_enforced():
            raise TranscodaError(f"{self.file.file} has been previously processed. Skipping this file.\n"
                                 f"Execution Details are: {self.file.history_result}")
