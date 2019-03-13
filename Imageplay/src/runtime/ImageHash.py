from pathlib import Path

import imagehash
import sqlite3
from PIL import Image
from PyQt5.QtCore import QUrl, pyqtSignal, QObject

from ImagePlayApp import ImagePlayApp
from common.CommonUtils import FileScanner


class DuplicateImageFinderRuntime(QObject):
    dupes_found_event = pyqtSignal(int, list)

    def __init__(self, files_to_scan):
        super().__init__()
        self.files_to_scan = files_to_scan
        self.counter = 0
        self.stop = False
        self.connection = sqlite3.connect(':memory:')

    def stop(self):
        self.stop = True

    def start_duplicate_search(self, hash_size, h_dist, algorithm):
        cursor = self.connection.cursor()
        self.connection.create_function("hamming_dist", 2,
                                        self._hamming_distance)
        self.connection.row_factory = sqlite3.Row
        sqlite3.enable_callback_tracebacks(True)

        # Create table
        cursor.execute('''CREATE TABLE IF NOT EXISTS file_details (
        file_name text, 
        hash_code text, 
        cohort_id integer)''')
        cursor.execute('''CREATE INDEX IF NOT EXISTS idx_hash on file_details(hash_code)''')

        cohort_counter = 0
        # Start reading files
        while len(self.files_to_scan) > 0:
            file = self.files_to_scan.pop()
            image_hash = str(self._calculate_hash(file, hash_size))
            cohort = None
            cursor.execute('''SELECT file_name, cohort_id from file_details f 
                        WHERE hamming_dist(f.hash_code, ?) <= ?''', (image_hash, h_dist,))
            row = cursor.fetchone()
            if row is not None:
                found_file = row[0]
                cohort_id = row[1]
                print("Duplicate found", found_file)
                if cohort_id is None:
                    cohort = cohort_counter
                    cohort_counter += 1
                    # Update existing file
                    cursor.execute('''UPDATE file_details SET cohort_id=? WHERE file_name=?''', (cohort, found_file,))
                else:
                    cohort = cohort_id

            # Insert new file
            cursor.execute('''INSERT into file_details VALUES (?, ?, ?)''', (file, image_hash, cohort))

            # Raise an event if required
            if cohort is not None:
                cursor.execute('''SELECT file_name from file_details WHERE 
                                            cohort_id = ?''', (cohort,))
                files = []
                for row in cursor:
                    files.append(row[0])
                self.dupes_found_event.emit(cohort, files)

            if self.stop:
                return

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


def main():
    # https://docs.python.org/3/library/sqlite3.html#module-sqlite3
    # con = sqlite3.connect(':memory:')

    files, start_file = ImagePlayApp.parse_args()
    urls = []
    for file in files:
        urls.append(QUrl.fromLocalFile(file))
    found_files = FileScanner(urls, True, None).files
    # start_duplicate_search(con, found_files, 7, 2)
    rt = DuplicateImageFinderRuntime(found_files)
    rt.start_duplicate_search(found_files, 7, 2, "foo")


if __name__ == '__main__':
    main()
