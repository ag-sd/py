import atexit
import datetime
import os
import random
import shutil
import sqlite3
import tempfile

import CommonUtils
import MediaLib
from MediaLib.runtime.library import FileManagement
from MediaLib.runtime.library.Domain import Library, Task, TaskStatus

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
    rez = []
    conn = db.cursor()
    results = conn.execute(f"{__LIB_SELECT_STATEMENT} ORDER BY type")
    for row in results:
        rez.append(Library.from_database_record(row))
    conn.close()
    return rez


def create_library(library, task):
    """
        Creates a library of the given name and type.

        Note: Will throw an error if the library already exists. It is the responsibility
        of the calling method to determine if a library with the same name exists
    """
    conn = db.cursor()
    task.log_and_save(status=TaskStatus.Running,
                      message=f"Creating library name={library.name} of types={library.types} "
                              f"with dirs={library.dirs}", db_conn=conn)

    # Step 1: First create the library entry
    conn.execute(__LIB_CREATE_STATEMENT, library.get_db_params())

    task.log_and_save(status=TaskStatus.Running, message=f"Created library {library.name}", db_conn=conn)
    conn.close()

    # Step 2: Refresh the library
    refresh_library(library, task)


def delete_library(library, task, skip_file_deletes=False):
    conn = db.cursor()
    task.log_and_save(status=TaskStatus.Running, message=f"Deleting {library.name}", db_conn=conn)
    conn.execute("begin")
    try:
        # Step 1: Delete all files from the library
        if not skip_file_deletes:
            FileManagement.delete_library(library, conn)

        # Step 2: Delete the library entry
        conn.execute(__LIB_DELETE_STATEMENT, [library.name])

        # Step 3: Commit
        conn.execute('commit')
        task.log_and_save(TaskStatus.Complete, f"Library deleted", conn)
    except sqlite3.Error as e:
        task.log_and_save(TaskStatus.Failed, f"Unable to delete library because of the error {e}", conn)
        conn.execute("rollback")

    conn.close()


def delete_from_library(library, files, task):
    conn = db.cursor()  # TODO FIXME Use With
    FileManagement.delete_files(library, files, conn, task)
    conn.close()


def rebuild_library(library, task):
    # Step 1: Delete the library, but not the files
    delete_library(library, task, skip_file_deletes=True)

    # Step 2: Refresh the library
    create_library(library, task)


def refresh_library(library, task):
    """
        Updates a library by adding new files, removing non-existent files
        and updating changed files
    :param library:
    :param task
    :return:
    """
    conn = db.cursor()
    task.log_and_save(status=TaskStatus.Running, message=f"Refreshing {library.name}", db_conn=conn)

    # Step 1: Get files in library that are in the database
    db_files = {}
    for file in get_files_in_library(library):
        db_files[file.file] = file
    task.log_and_save(status=TaskStatus.Running, message="DB files fetched...", db_conn=conn)

    task.log_and_save(status=TaskStatus.Running, message="Scanning filesystem now...", db_conn=conn)
    scanner = CommonUtils.FileScanner(library.dirs, recurse=True,
                                      partial_mimetypes_list=[t.name for t in library.types], is_qfiles=False)
    MediaLib.logger.debug(f"Will scan for the following extensions: {scanner.supported_extensions}")
    task.log_and_save(status=TaskStatus.Running, message="Filesystem scan complete", db_conn=conn)

    # Step 2: Compare the 2 data-sets and identify inserts, updates and deletes
    updates = []
    inserts = []
    deletes = []
    counter = 0
    f_count = len(scanner.files)

    for file_p in scanner.files:
        file = FileManagement.FileRecord(file_p, metadata=None)
        if file.file in db_files:
            if not db_files[file.file].__eq__(file):
                deletes.append(file)
                file.catalog_updated = datetime.datetime.now()
                updates.append(file)
                db_files.pop(file.file)
            else:
                # file unchanged. Leave it as is
                db_files.pop(file.file)
        else:
            # New File
            inserts.append(file)
        counter += 1
        if counter % 5 == 0:
            pct = counter * 100 / f_count
            task.log_and_save(status=TaskStatus.Running, message=f"Completed {pct}", db_conn=conn, percent=pct)

    # What is left in the db needs to be deleted as it was not found in the filesystem
    for f in db_files.values():
        deletes.append(f)

    task.log_and_save(status=TaskStatus.Running, message=f"{len(updates)} files to be updated", db_conn=conn)
    if len(updates):
        MediaLib.logger.debug("******* Updated Files ******* \n" + "\n".join([e.file for e in updates]) + "\n\n")

    task.log_and_save(status=TaskStatus.Running, message=f"{len(inserts)} files to be added", db_conn=conn)
    if len(inserts):
        MediaLib.logger.debug("******* Inserted Files ******* \n" + "\n".join([e.file for e in inserts]) + "\n\n")

    task.log_and_save(status=TaskStatus.Running, message=f"{len(deletes)} files to be deleted", db_conn=conn)
    if len(deletes):
        MediaLib.logger.debug("******* Deleted Files ******* \n" + "\n".join([e.file for e in deletes]) + "\n\n")

    # Step 3: Insert the data
    FileManagement.delete_files(library, deletes, conn, task)
    MediaLib.logger.info("Obsolete files deleted")

    FileManagement.insert_files(library, inserts + updates, conn, task)
    MediaLib.logger.info("Updated files added")

    task.log_and_save(status=TaskStatus.Complete, message="Scan completed", db_conn=conn)
    conn.close()


def get_files_in_library(library):
    conn = db.cursor()
    files = FileManagement.get_files(library, conn)
    conn.close()
    return files


def close_database():
    db.commit()
    db.close()
    MediaLib.logger.info(f"Committed and closed {MediaLib.__APP_NAME__} library")


# ------------------------ ----------------------------- ------------------------ #
# ------------------------ # TASK MANAGEMENT FUNCTIONS # ------------------------ #
# ------------------------ ----------------------------- ------------------------ #

__LIB_TASK_SELECT_STATEMENT = "select status, message, event_time, percent from tasks " \
                              "where task_id = ? order by seq_id desc limit 1"

__LIB_TASK_SELECT_CURRENTLY_RUNNING = "select distinct task_id from tasks t where not exists " \
                                      "(select 1 from tasks ti where ti.task_id = t.task_id " \
                                      "and ti.status in ('Complete', 'Failed'))"


def get_task(task_id):
    conn = db.cursor()
    result = conn.execute(__LIB_TASK_SELECT_STATEMENT, [task_id]).fetchone()
    conn.close()
    return Task(
        task_id=task_id,
        status=TaskStatus[result[0]],
        message=result[1],
        event_time=datetime.datetime.fromisoformat(result[2]),
        percent=result[3],
    )


def get_currently_running_tasks():
    conn = db.cursor()
    tasks = conn.execute(__LIB_TASK_SELECT_CURRENTLY_RUNNING).fetchall()
    conn.close()
    return [get_task(task[0]) for task in tasks]


def save_task(task):
    conn = db.cursor()
    task.log_and_save(status=task.status, message=task.message, db_conn=conn, percent=task.percent)
    conn.close()


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
    _task = Task("Test : Create a library of type audio, video, images")
    create_library(Library(name="lib_test", types=[LibraryType.Audio, LibraryType.Video, LibraryType.Image],
                           dirs=["/mnt/Dev/testing"]), task=_task)

    MediaLib.logger.info("Test : Get library")
    _library = get_library("lib_test")
    assert (_library.name == "lib_test")

    MediaLib.logger.info("Test : Get all libraries")
    _all = get_all_libraries()
    assert len(_all) == 1

    MediaLib.logger.info("Test : Delete a few files from the library")
    _task = Task("Test : Delete a few files from the library")
    _db_files = get_files_in_library(_library)
    _dels = random.choices(_db_files, k=4)
    delete_from_library(_library, _dels, _task)
    _db_files_post_dels = get_files_in_library(_library)
    assert (len(_db_files) - 4 == len(_db_files_post_dels))
    for d in _dels:
        assert d not in _db_files_post_dels

    MediaLib.logger.info("Test : Refresh the library")
    _task = Task("Test : Refresh the library")
    refresh_library(_library, _task)
    _db_files_post_refresh = get_files_in_library(_library)
    assert (len(_db_files) - 4 == len(_db_files_post_dels))

    MediaLib.logger.info("Test : Delete the library")
    _task = Task("Test : Delete the library")
    delete_library(_library, _task, skip_file_deletes=False)
    assert get_library("lib_test") is None
    assert len(get_files_in_library(_library)) == 0
