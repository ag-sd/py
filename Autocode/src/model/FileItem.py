
from datetime import datetime
from os import path

from PyQt5.QtCore import QFileInfo


class FileItem:
    """
    Encapsulation of a Autocode File
    """
    FILE_STATUS_INIT = "INIT"
    FILE_STATUS_STARTED = "STARTED"
    FILE_STATUS_COMPLETE = "COMPLETED"

    def __init__(self, file_name, file_path, file_size):
        super().__init__()
        self.file_name = file_name
        self.file_path = file_path
        self.file_size = file_size
        self.file_status = self.FILE_STATUS_INIT
        self.start_time = 0
        self.end_time = 0
        self.encoded_file_name = ""
        self.encoded_file_path = ""
        self.encoded_file_size = -1
        self.codec = ""
        self.file_info = QFileInfo(path.join(file_path, file_name))

    @classmethod
    def from_db(cls, file_name, file_path, file_size, file_status, start_time, finish_time, encoded_file_name,
                encoded_file_path, encoded_file_size, codec):
        item = cls(file_name, file_path, file_size)
        item.file_status = file_status
        item.start_time = start_time
        item.end_time = finish_time
        item.encoded_file_name = encoded_file_name
        item.encoded_file_path = encoded_file_path
        item.encoded_file_size = encoded_file_size
        item.codec = codec
        return item

    def __repr__(self):
        return path.join(self.file_path, self.file_name) + " [" + str(self.file_size) + " b] "

    def set_started(self, op_file_path, op_file_name, codec):
        """
        Mark the file as started to encode.
        :param op_file_path: The output file path
        :param op_file_name: The output file name
        :return:
        """
        self.file_status = self.FILE_STATUS_STARTED
        self.start_time = datetime.now()
        self.encoded_file_path = op_file_path
        self.encoded_file_name = op_file_name
        self.codec = codec

    def set_complete(self):
        """
        Marks the file as complete
        :return:
        """
        self.file_status = self.FILE_STATUS_COMPLETE
        self.end_time = datetime.now()
        output_file = path.join(self.encoded_file_path, self.encoded_file_name)
        if path.exists(output_file):
            self.encoded_file_size = path.getsize(output_file)
