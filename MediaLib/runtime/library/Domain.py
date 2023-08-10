import datetime
from enum import Enum

import MediaLib
import MediaMetaData
from MediaMetaData import MetaDataFields


class Library:
    def __init__(self, name, types, dirs, created=None, updated=None):
        self.name = name
        self.types = types
        self.dirs = dirs
        self.created = created if created is not None else datetime.datetime.now()
        self.updated = updated if updated is not None else datetime.datetime.now()

    def get_db_params(self):
        return self.name, "|".join([t.name for t in self.types]), "|".join(self.dirs), self.created, self.updated

    @staticmethod
    def from_database_record(lib_record):
        """
            Extracts data from a library record
            :param lib_record: a db row that represents a library
            :return: a dict representing the library
        """
        return Library(
            name=lib_record[0],
            types=[LibraryType[t] for t in lib_record[1].split('|')],
            dirs=lib_record[2].split('|'),
            created=lib_record[3],
            updated=lib_record[4]
        )

    def __str__(self):
        return self.name


class LibraryType(Enum):
    Audio = 1
    Video = 2
    Image = 3
    File = 4

    def __str__(self):
        return self.name


class Task:
    __LIB_TASK_INSERT_STATEMENT = "INSERT INTO tasks (task_id, status, message, percent, event_time) " \
                                  "VALUES (?, ?, ?, ?, ?)"

    def __init__(self, task_id, status=None, message=None, event_time=None, percent=None):
        self.task_id = task_id
        self.status = status if status is not None else TaskStatus.Created
        self.message = message
        self.event_time = event_time if event_time is not None else datetime.datetime.now()
        self.percent = percent if percent is not None else 0

    def log_and_save(self, status, message, db_conn, percent=None, ):
        self.status = status
        self.message = message
        self.percent = percent if percent is not None else 0
        MediaLib.logger.info(f"{self.task_id} {self.status.name} {self.percent}%: {self.message} at {self.event_time}")
        db_conn.execute(Task.__LIB_TASK_INSERT_STATEMENT,
                        (self.task_id, self.status.name, self.message, self.percent, self.event_time))

    def __str__(self):
        return f"Task:{self.task_id}: {self.message} at {self.event_time}"


class TaskStatus(Enum):
    Created = "Created"
    Running = "Running"
    Complete = "Complete"
    Failed = "Failed"


class FileRecord:
    def __init__(self, file, metadata=None, cataloged=None, catalog_updated=None):
        super(FileRecord, self).__init__()
        self.file = file
        self.metadata = metadata if metadata is not None else MediaMetaData.get_metadata(file, include_checksum=True)
        self.cataloged = cataloged if cataloged is not None else datetime.datetime.now()
        self.catalog_updated = catalog_updated

    def __repr__(self):
        return f"file:{self.file}\nmetadata:{self.metadata}"

    def __eq__(self, other):
        if isinstance(other, FileRecord):
            return self.file == other.file and \
                   self.metadata[MetaDataFields.filesize] == other.metadata[MetaDataFields.filesize] and \
                   self.metadata[MetaDataFields.checksum] == other.metadata[MetaDataFields.checksum]
        else:
            return False
