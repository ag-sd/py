from datetime import datetime
from time import sleep
from PyQt5.QtCore import (QObject, pyqtSignal, )
import AutocodeUtils


class TaskRunner(QObject):
    encode_started = pyqtSignal('PyQt_PyObject', 'PyQt_PyObject')
    encode_completed = pyqtSignal('PyQt_PyObject')

    def __init__(self):
        super().__init__()
        self.file_model = []
        self.output_dir = ''
        self.encoder = None
        self.max_hours = 150
        self.logger = AutocodeUtils.get_logger("Autocode.TaskRunner")

    def start(self, file_model, output_dir, encoder, max_hours):
        self.file_model = file_model
        self.output_dir = output_dir
        self.encoder = encoder
        self.max_hours = max_hours

        #   Log the start time
        print("Started at " + str(datetime.now()))
        hours_elapsed = 0
        process_count = 0

        items = file_model.file_items
        while len(items) > process_count and hours_elapsed <= self.max_hours:
            curr_file = items[process_count]
            self.logger.info("Evaluating " + str(curr_file))

            #   TODO if encoder.can_process(curr_file)...
            #   TODO Database lookup...

            #   1. Start timer
            #   2. Send message: File has started
            #   3. Encode file
            #   4. End timer
            #   5. Send message: File has completed, new file name, time taken
            process_count += 1
            # Setup encoding
            start_timer = datetime.now()

            curr_file.set_started(self.output_dir, curr_file.file_name, self.encoder)
            file_model.update_view(process_count)

            self.encode_file(curr_file)

            curr_file.set_complete()
            file_model.update_view(process_count)

            td = datetime.now() - start_timer
            mints = (td.total_seconds() / 60)
            hours = mints / 60
            hours_elapsed += hours
            self.logger.info("File encoded in " + str(mints) + " minutes [ " + str(hours) + " hours]")
            self.logger.info("Total time taken so far is " + str(hours_elapsed) + " hours")

        self.logger.info("Encoding completed. Processed " + str(process_count) + " files.")

    def encode_file(self, file_item):
        self.logger.info("INPUT - " + file_item.file_name)
        self.logger.info("INPUT - " + file_item.file_path)
        self.logger.info("OUTPUT - " + file_item.encoded_file_name)
        self.logger.info("OUTPUT - " + file_item.encoded_file_path)
        #sleep(1)
        self.logger.info("COMPLETE!")