import atexit
import datetime
import os
import random
import shutil
import sqlite3
import tempfile
from collections import defaultdict

import MediaLib
from CommonUtils import FileScanner
from MediaLib.runtime.library import FileManagement


class Library:
    def __init__(self, name, types, dirs, created=None, updated=None):
        self.name = name
        self.types = types
        self.dirs = dirs
        self.created = created if created is not None else datetime.datetime.now()
        self.updated = updated if updated is not None else datetime.datetime.now()

    def get_db_params(self):
        return self.name, "|".join(self.types), "|".join(self.dirs), self.created, self.updated

    @staticmethod
    def from_database_record(lib_record):
        """
            Extracts data from a library record
            :param lib_record: a db row that represents a library
            :return: a dict representing the library
            """
        return Library(
            name=lib_record[0],
            types=lib_record[1].split('|'),
            dirs=lib_record[2].split('|'),
            created=lib_record[3],
            updated=lib_record[4]
        )


__LIB_SELECT_STATEMENT = "SELECT name, type, dirs, created, updated from library "
__LIB_CREATE_STATEMENT = "INSERT INTO library (name, type, dirs, created, updated) VALUES (?, ?, ?, ?, ?) "
__LIB_DELETE_STATEMENT = "DELETE FROM library where name=?"


def reset_database(db_path):
    """
    Will create a new library from the template
    """
    if os.path.exists(db_path):
        os.remove(db_path)
    shutil.copy(MediaLib.db_template_path, db_path)


def get_library(library_name):
    """
    Returns details about a library
    :param library_name:
    :return: Library details in a dictionary
    """
    conn = db.cursor()
    lib = conn.execute(f"{__LIB_SELECT_STATEMENT} WHERE name = ?", [library_name]).fetchone()
    conn.close()
    if lib is None:
        return None
    else:
        return Library.from_database_record(lib)


def get_all_libraries():
    """
        Returns a list of all libraries in the database
        :return: a Dictionary of supported types with a list of libraries per type
    """
    result_dict = defaultdict(list)
    conn = db.cursor()
    results = conn.execute(f"{__LIB_SELECT_STATEMENT} ORDER BY type")
    for row in results:
        result_dict[row[1]].append(Library.from_database_record(row))
    conn.close()
    return result_dict


def create_library(library_name, library_types, dirs_in_library):
    """
        Creates a library of the given name and type.

        Note: Will throw an error if the library already exists. It is the responsibility
        of the calling method to determine if a library with the same name exists
    """
    MediaLib.logger.info(f"Creating library name={library_name} of types={library_types} with dirs={dirs_in_library}")
    conn = db.cursor()

    # Step 1: First create the library entry
    lib = Library(name=library_name, types=library_types, dirs=dirs_in_library)
    conn.execute(__LIB_CREATE_STATEMENT, lib.get_db_params())

    conn.close()
    MediaLib.logger.info(f"Created library {library_name}")

    # Step 2: Refresh the library
    refresh_library(lib)


def delete_library(library, skip_file_deletes=False):
    MediaLib.logger.info(f"Deleting {library.name}")
    conn = db.cursor()
    conn.execute("begin")
    try:
        # Step 1: Delete all files from the library
        if not skip_file_deletes:
            FileManagement.delete_library(library, conn)

        # Step 2: Delete the library entry
        conn.execute(__LIB_DELETE_STATEMENT, [library.name])

        # Step 3: Commit
        conn.execute('commit')
        MediaLib.logger.info(f"Library deleted")
    except sqlite3.Error as e:
        MediaLib.logger.error(f"Unable to delete library because of the error {e}")
        conn.execute("rollback")

    conn.close()


def delete_from_library(library, files):
    file_ps = []
    for file in files:
        file_ps.append(file.file)

    conn = db.cursor() # TODO FIXME Use With
    FileManagement.delete_files(library, file_ps, conn)
    conn.close()


def rebuild_library(library):
    # Step 1: Delete the library, but not the files
    delete_library(library, skip_file_deletes=True)

    # Step 2: Refresh the library
    create_library(library.name, library.types, library.dirs)


def refresh_library(library):
    """
    Updates a library by adding new files, removing non-existent files
    and updating changed files
    :param library: The library to update
    :return:
    """
    MediaLib.logger.info(f"Refreshing {library.name}")
    conn = db.cursor()

    # Step 1: Get files in library that are in the database
    db_files = {}
    for file in get_files_in_library(library):
        pass

    MediaLib.logger.debug("DB files fetched...")

    # Step 2: Get the files of this library from the filesystem
    MediaLib.logger.debug("Scanning files in filesystem...")
    # TODO: Option to not exclude any file type
    scanner = FileScanner(library.dirs, recurse=True, partial_mimetypes_list=library.types, is_qfiles=False)
    MediaLib.logger.debug(f"Will scan for the following extensions: {scanner.supported_extensions}")
    fs_files = scanner.files
    rejects = scanner.rejected_files

    MediaLib.logger.debug("Comparing files now...")
    # Step 3: Compare the 2 data-sets and identify inserts, updates and deletes
    updates = []
    inserts = []
    deletes = []
    counter = 0
    for file_p in fs_files:
        file = FileManagement.FileRecord(file_p, metadata=None)
        if file_p in db_files:
            if not db_files[file].__eq__(file):
                deletes.append(file_p)
                file.updated = datetime.datetime.now()
                updates.append(file)
                db_files.pop(file_p)
            # Else, file unchanged. Leave it as is
        else:
            # New File
            inserts.append(file)

        counter = counter + 1
    # What is left in the db needs to be deleted as it was not found in the filesystem
    for file_p in db_files.keys():
        deletes.append(file_p)

    MediaLib.logger.info(f"{len(updates)} files to be updated in library")
    if len(updates):
        MediaLib.logger.debug("*********** Updated Files *********** \n" + "\n".join([e.file for e in updates]) + "\n\n")
    MediaLib.logger.info(f"{len(inserts)} files to be inserted in library")
    if len(inserts):
        MediaLib.logger.debug("*********** Inserted Files *********** \n" + "\n".join([e.file for e in inserts]) + "\n\n")
    MediaLib.logger.info(f"{len(deletes)} files to be deleted from library")
    if len(deletes):
        MediaLib.logger.debug("*********** Deleted Files *********** \n" + "\n".join([e.file for e in deletes]) + "\n\n")
    MediaLib.logger.info(f"{len(rejects)} files to be excluded from library")
    if len(rejects):
        MediaLib.logger.debug("*********** Rejected Files *********** \n" + "\n".join(rejects) + "\n\n")

    # Step 5: Insert the data
    FileManagement.delete_files(library, deletes, conn)
    MediaLib.logger.info("Obsolete files deleted")

    FileManagement.insert_files(library, inserts + updates, conn)
    MediaLib.logger.info("Updated files added")

    conn.close()
    MediaLib.logger.info("Complete")


def get_files_in_library(library):
    conn = db.cursor()
    files = FileManagement.get_files(library, conn)
    conn.close()
    return files


def close_database():
    db.commit()
    db.close()
    MediaLib.logger.info(f"Committed and closed {MediaLib.__APP_NAME__} library")


atexit.register(close_database)


if __name__ != '__main__':
    if not os.path.exists(MediaLib.db_path):
        MediaLib.logger.warn(f"Media library not found at {MediaLib.db_path}. Creating new library from template")
        reset_database(MediaLib.db_path)

    db = sqlite3.connect(MediaLib.db_path, check_same_thread=False)
    # Autocommit on by default, but disabled by a `begin` statement
    db.isolation_level = None

else:
    # Tests
    temp_db = os.path.join(tempfile.gettempdir(), "medialib_tests_delete_me.sqlite")
    reset_database(temp_db)

    db = sqlite3.connect(temp_db, check_same_thread=False)
    # Autocommit on by default, but disabled by a `begin` statement
    db.isolation_level = None

    MediaLib.logger.info("Test : Create a library of type audio, video, images")
    create_library(library_name="lib_test", library_types=["audio", "video", "image"],
                   dirs_in_library=["/mnt/Dev/testing"])

    MediaLib.logger.info("Test : Get library")
    _library = get_library("lib_test")
    assert(_library.name == "lib_test")

    MediaLib.logger.info("Test : Get all libraries")
    _all = get_all_libraries()
    assert len(_all) == 1

    MediaLib.logger.info("Test : Delete a few files from the library")
    _db_files = get_files_in_library(_library)
    _dels = random.choices(_db_files, k=4)
    delete_from_library(_library, _dels)
    _db_files_post_dels = get_files_in_library(_library)
    assert(len(_db_files) - 4 == len(_db_files_post_dels))
    for d in _dels:
        assert d not in _db_files_post_dels

    MediaLib.logger.info("Test : Delete the library")
    delete_library(_library, skip_file_deletes=False)
    assert get_library("lib_test") is None
    assert len(get_files_in_library(_library)) == 0


