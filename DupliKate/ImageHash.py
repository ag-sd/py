import os
import random
import sqlite3

import imagehash
from PIL import Image
from PyQt5.QtCore import QUrl, pyqtSignal, QThread, QRunnable, QThreadPool, QObject

import CommonUtils
from common.CommonUtils import FileScanner


class HashedImage:
    def __init__(self, file, image_hash):
        self.file_name = file
        self.image_hash = image_hash


class HashWorker(CommonUtils.Command):
    result = pyqtSignal('PyQt_PyObject')

    def __init__(self, file, hash_size, algorithm):
        super().__init__()
        self.file = file
        self.hash_size = hash_size
        self.algorithm = algorithm

    def run(self):
        image = Image.open(self.file)
        hash_ = str(imagehash.average_hash(image, hash_size=self.hash_size))
        hashed = HashedImage(self.file, hash_)
        print(f"{self.file} -> {hash_}")
        self.signals.result.emit(hashed)


class DuplicateImageFinderRuntime:
    dupes_found_event = pyqtSignal(int, list)
    scan_status_event = pyqtSignal(str, int, int, int, int, int, int)
    scan_finish_event = pyqtSignal()

    def __init__(self, files_to_scan, hash_size, h_dist_max, algorithm):
        super().__init__()
        self.files_to_scan = files_to_scan
        self.scan_size = len(files_to_scan)
        self.hash_size = hash_size
        self.h_dist_max = h_dist_max
        self.algorithm = algorithm
        self.stop = False
        self.status_counter = random.randint(5, 15)
        self.executor = None
        self.connection, self.cursor = self._setup_database()
        self.cohort_counter = 0
        self.file_counter = 0

    def stop_scan(self):
        self.stop = True

    def run(self):
        self._start_duplicate_search2()

    def test_foo(self, xyz):
        print(xyz)

    def _process_file(self, hash_data):
        self.status_counter -= 1
        self.file_counter += 1

        cohort = None
        self.cursor.execute('''SELECT file_name, cohort_id from file_details f 
                                WHERE hamming_dist(f.hash_code, ?) <= ?''',
                            (hash_data.image_hash, self.h_dist_max,))
        row = self.cursor.fetchone()
        if row is not None:
            found_file = row[0]
            cohort_id = row[1]
            if cohort_id is None:
                cohort = self.cohort_counter
                self.cohort_counter += 1
                # Update existing file
                self.cursor.execute('''UPDATE file_details SET cohort_id=? WHERE file_name=?''', (cohort, found_file,))
            else:
                cohort = cohort_id

        # Insert new file
        self.cursor.execute('''INSERT into file_details VALUES (?, ?, ?)''', (hash_data.file_name,
                                                                              hash_data.image_hash, cohort))

        # Raise an event if required
        if cohort is not None:
            self.cursor.execute('''SELECT file_name from file_details WHERE 
                                                    cohort_id = ?''', (cohort,))
            files = []
            for row in self.cursor:
                files.append(row[0])
            print(f"Dupes found {cohort} -> {files}")
            self.dupes_found_event.emit(cohort, files)

        if self.status_counter == 0:
            self.status_counter = random.randint(5, 15)
            self.scan_status_event.emit(hash_data.file_name,
                                        self.file_counter, self.scan_size,
                                        self.thread_pool.activeThreadCount(),
                                        self.thread_pool.maxThreadCount(),
                                        0, 0)

        if self.stop:
            self._close_database()
            self.scan_finish_event.emit()
            return

    def _start_duplicate_search2(self):
        runnables = []
        for file in self.files_to_scan:
            _, extension = os.path.splitext(file)
            if extension.upper() not in [".JPG", ".JPEG", ".PNG", ".GIF"]:
                print(f"Skipping file {file} as it is not an image file")
            else:
                worker = HashWorker(file, self.hash_size, self.algorithm)
                worker.signals.result.connect(self.test_foo)
                runnables.append(worker)
        self.executor = CommonUtils.CommandExecutionFactory(runnables)
        self.executor.start()
        #
        #
        # while len(self.files_to_scan) > 0:
        #     if self.stop:
        #         self._close_database()
        #         self.scan_finish_event.emit()
        #         return
        #
        #     file = self.files_to_scan.pop()
        #     _, extension = os.path.splitext(file)
        #     if extension.upper() not in [".JPG", ".JPEG", ".PNG", ".GIF"]:
        #         print(f"Skipping file {file} as it is not an image file")
        #     else:
        #         worker = HashWorker(file, self.hash_size, self.algorithm)
        #         worker.signals.result.connect(self.test_foo)
        #         self.executor = CommonUtils.CommandExecutionFactory
        #         # Execute
        #         self.thread_pool.start(worker)
        #
        # self.thread_pool.waitForDone()
        # self.scan_status_event.emit("",
        #                             self.file_counter, self.scan_size,
        #                             self.thread_pool.activeThreadCount(),
        #                             self.thread_pool.maxThreadCount(),
        #                             0, 0)
        # self.scan_finish_event.emit()

    def _setup_database(self):

        # connection = sqlite3.connect(':memory:')
        connection = sqlite3.connect("test_db.sqlite")
        cursor = connection.cursor()
        connection.create_function("hamming_dist", 2, self._hamming_distance)
        connection.row_factory = sqlite3.Row
        sqlite3.enable_callback_tracebacks(True)

        # Create table
        cursor.execute('''CREATE TABLE IF NOT EXISTS file_details (
                file_name text, 
                hash_code text, 
                cohort_id integer)''')
        cursor.execute('''CREATE INDEX IF NOT EXISTS idx_hash on file_details(hash_code)''')
        return connection, cursor

    def _close_database(self):
        self.cursor.close()
        self.connection.close()

    @staticmethod
    def _hamming_distance(s1, s2):
        """Return the Hamming distance between equal-length sequences"""
        if len(s1) != len(s2):
            raise ValueError("Undefined for sequences of unequal length")
        return sum(el1 != el2 for el1, el2 in zip(s1, s2))

    @staticmethod
    def _calculate_hash(file, hash_size):
        image = Image.open(file)
        return imagehash.average_hash(image, hash_size=hash_size)

    @staticmethod
    def _calculate_hash2(file, hash_size):
        image = Image.open(file)
        return HashedImage(file, imagehash.average_hash(image, hash_size=hash_size))


def main():
    # https://docs.python.org/3/library/sqlite3.html#module-sqlite3
    # con = sqlite3.connect(':memory:')

    files = ["/mnt/Stuff/test/"]
    urls = []
    for file in files:
        urls.append(QUrl.fromLocalFile(file))
    found_files = FileScanner(urls, True, None).files
    # start_duplicate_search(con, found_files, 7, 2)
    rt = DuplicateImageFinderRuntime(found_files, 8, 8, "foo")
    rt.run()


if __name__ == '__main__':
    main()
