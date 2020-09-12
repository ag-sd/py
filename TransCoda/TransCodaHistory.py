import json
import os
import threading
from datetime import datetime
from enum import Enum


class TransCodaHistoryFields(Enum):
    start_time = "start_time"
    end_time = "end_time"
    output_file = "output_file"
    status = "status"
    message = "message"
    output_size = "output_size"
    input_size = "input_size"
    encoder = "encoder"


_history_lock = threading.RLock()


class TransCodaHistory:
    def __init__(self):
        super().__init__()

        self.history_file = os.path.join(os.path.dirname(__file__), "resource/history.json")
        with open(self.history_file) as h:
            self.history = json.load(h)

    def check_history(self, input_file):
        return input_file in self.history

    def get_execution_details(self, input_file):
        if input_file in self.history:
            return self.history[input_file]
        else:
            return None

    def add_history_item(self, input_file, output_file, start_time, end_time, input_size, output_size, status, message,
                         encoder):
        with _history_lock:
            self.history[input_file] = {
                TransCodaHistoryFields.output_file.value: output_file,
                TransCodaHistoryFields.start_time.value: start_time.strftime("%Y.%m.%d"),
                TransCodaHistoryFields.end_time.value: end_time.strftime("%Y.%m.%d"),
                TransCodaHistoryFields.status.value: status.name,
                TransCodaHistoryFields.message.value: message,
                TransCodaHistoryFields.input_size.value: input_size,
                TransCodaHistoryFields.output_size.value: output_size,
                TransCodaHistoryFields.encoder.value: encoder
            }
            with open(self.history_file, "w") as history_file:
                json.dump(self.history, history_file, indent=4)

    def backup_history_file(self):
        file = self.history_file
        backup = file + ".backup-" + datetime.now().strftime("%Y-%m-%d_%H_%M_%S")
        os.rename(file, backup)
        return backup









