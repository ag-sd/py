import atexit
import datetime
import os
import shutil
import sqlite3
from collections import defaultdict

import CommonUtils
import MediaLib
from CommonUtils import FileScanner
from MediaLib.runtime.library import AudioLibrary


def create_new_database():
    """
    Will create a new library from the template
    """
    if os.path.exists(db_name):
        os.remove(db_name)
    shutil.copy(db_template, db_name)


def get_library(library_name):
    """
    Returns details about a library
    :param library_name:
    :return: Library details in a dictionary
    """
    conn = db.cursor()
    lib = conn.execute("SELECT name, type, dirs, created, updated from library WHERE name = ?",
                       [library_name]).fetchone()
    conn.close()
    if lib is None:
        return None
    else:
        return {
            "name": lib[0],
            "type": lib[1],
            "dirs": lib[2].split('|'),
            "created": lib[3],
            "modifed": lib[4]
        }


def get_group_keys(libary_type):
    """
    Returns the group keys for a library
    """
    return Library_Types[libary_type]['manager'].get_group_keys()


def get_all_libraries():
    """
        Returns a list of all libraries in the database
        :return: a Dictionary of supported types with a list of libraries per type
    """
    result_dict = defaultdict(list)
    conn = db.cursor()
    results = conn.execute("SELECT name, type, dirs, created, updated from library ORDER BY type")
    for row in results:
        result_dict[row[1]].append(
            {
                "name": row[0],
                "type": row[1],
                "dirs": row[2].split('|'),
                "created": row[3],
                "updated": row[4]
            }
        )
    conn.close()
    return result_dict


def create_library(library_name, library_type, dirs_in_library, created=None, task_id=None):
    """
        Creates a library of the given name and type.

        Note: Will throw an error if the library already exists. It is the responsibility
        of the calling method to determine if a library with the same name exists
    """
    MediaLib.logger.info(f"Creating library name={library_name} of type={library_type} with dirs={dirs_in_library}")
    conn = db.cursor()

    # Step 1: First create the library entry
    if not created:
        created = _get_time_string()
    params = (library_name, library_type, "|".join(dirs_in_library), created)
    conn.execute("INSERT INTO library (name, type, dirs, created) VALUES (?,?,?,?)", params)

    conn.close()
    MediaLib.logger.info(f"Created library {library_name}")

    # Step 2: Refresh the library
    refresh_library({
        "name": library_name,
        "type": library_type,
        "dirs": dirs_in_library
    }, task_id=task_id)


def delete_library(library, skip_file_deletes=False):
    MediaLib.logger.info(f"Deleting {library['name']}")
    conn = db.cursor()
    # Step 1: Delete all files from the library
    if not skip_file_deletes:
        lib_manager = Library_Types[library['type']]['manager']
        lib_manager.delete_library(library['name'], conn)

    # Step 2: Delete the library entry
    conn.execute("DELETE FROM library where name=?", [library['name']])
    MediaLib.logger.info(f"Library deleted")
    conn.close()


def update_library(library):
    # Step 1: Delete the library, but not the files
    delete_library(library, skip_file_deletes=True)

    # Step 2: Refresh the library
    create_library(library['name'], library['type'], library['dirs'], library['created'])


def refresh_library(library, task_id=None):
    """
    Updates a library by adding new files, removing non-existent files
    and updating changed files
    :param task_id:
    :param library: The library to update
    :return:
    """
    MediaLib.logger.info(f"Refreshing {library['name']}")
    conn = db.cursor()
    if task_id:
        create_task(task_id, "Starting library refresh", 0, conn)
    # Step 1: Get the library details
    lib_manager = Library_Types[library['type']]['manager']

    # Step 2: Get files in library that are in the database
    db_files = lib_manager.get_files(library['name'], conn)
    MediaLib.logger.debug("DB files fetched...")
    if task_id:
        update_task(task_id, f"Scanning Medialib for files found {len(db_files)}", 10, conn)

    # Step 3: Get the files of this library from the filesystem
    MediaLib.logger.debug("Scanning files in filesystem...")
    scanner = FileScanner(library['dirs'], recurse=True, supported_extensions=lib_manager.supported_types(),
                          is_qfiles=False)
    fs_files = scanner.files
    rejects = scanner.rejected_files
    if task_id:
        update_task(task_id, f"Scanning Filesystem for files, found {len(fs_files)}", 20, conn)

    MediaLib.logger.debug("Comparing files now...")
    # Step 4: Compare the 2 data-sets and identify inserts, updates and deletes
    updates = {}
    inserts = {}
    counter = 0
    for file in fs_files:
        db_checksum = None
        if file in db_files:
            db_checksum = db_files.pop(file)
        fs_checksum = CommonUtils.calculate_sha256_hash(file)
        if db_checksum is None:
            # New file
            inserts[file] = fs_checksum
        elif db_checksum != fs_checksum:
            # File exists in db but checksum is different. Update the file in database
            updates[file] = fs_checksum
        counter = counter + 1
        if task_id:
            if counter % 10 == 0:
                percent_30 = 20+int((counter * 30)/len(fs_files))
                update_task(task_id, f"Comparing files in db and filesystem", percent_30, conn)
    # What is left in the db needs to be deleted as it was not found in the filesystem
    deletes = db_files.keys()

    MediaLib.logger.info(f"{len(updates)} files to be updated in library")
    if len(updates):
        MediaLib.logger.debug("*********** Updated Files *********** \n" + "\n".join(updates) + "\n\n")
    MediaLib.logger.info(f"{len(inserts)} files to be inserted in library")
    if len(inserts):
        MediaLib.logger.debug("*********** Inserted Files *********** \n" + "\n".join(inserts) + "\n\n")
    MediaLib.logger.info(f"{len(deletes)} files to be deleted from library")
    if len(deletes):
        MediaLib.logger.debug("*********** Deleted Files *********** \n" + "\n".join(deletes) + "\n\n")
    MediaLib.logger.info(f"{len(rejects)} files to be excluded from library")
    if len(rejects):
        MediaLib.logger.debug("*********** Rejected Files *********** \n" + "\n".join(rejects) + "\n\n")

    # Step 5: Insert the data
    lib_manager.delete_files(library['name'], list(updates.keys()) + list(deletes), conn)
    MediaLib.logger.info("Obsolete files deleted")
    all_updates = updates.copy()
    all_updates.update(inserts)
    lib_manager.insert_files(library['name'], all_updates, conn, task_id=task_id)
    MediaLib.logger.info("Updated files added")

    conn.execute("UPDATE library set updated=? where name=?", (_get_time_string(), library['name']))
    if task_id:
        finish_task(task_id, "Completed", 100, conn)
    conn.close()
    MediaLib.logger.info("Complete")


def get_task_status(task_id):
    sql = "select status, status_message, percent_complete from tasks where task_id = ? order by seq_id desc limit 1"
    conn = db.cursor()
    result = conn.execute(sql, (task_id,)).fetchone()
    conn.close()
    return {
        "status": result[0],
        "status_message": result[1],
        "percent_complete": result[2]
    }


def create_task(task_id, message, percent_complete, db_conn):
    update_task(task_id, message, percent_complete, db_conn, status="STARTING")


def finish_task(task_id, message, percent_complete, db_conn):
    update_task(task_id, message, percent_complete, db_conn, status="COMPLETE")


def fail_task(task_id, message, percent_complete, db_conn):
    update_task(task_id, message, percent_complete, db_conn, status="FAILED")


def update_task(task_id, message, percent_complete, db_conn, status="RUNNING"):
    db_conn.execute("INSERT INTO tasks (task_id, status, status_message, percent_complete) VALUES (?, ?, ?, ?)",
                    (task_id, status, message, percent_complete,))


def get_available_library_types():
    return set(Library_Types.keys())


def close_database():
    db.commit()
    db.close()
    MediaLib.logger.info(f"Committed and closed {MediaLib.__APP_NAME__} library")
    # MediaLib.logger.info("Waiting for all background tasks to complete")
    # thread_pool_executor.shutdown()
    # MediaLib.logger.info("Exiting")


def _get_time_string():
    return "{:%Y-%m-%d %H:%M:%S}".format(datetime.datetime.now())


atexit.register(close_database)
Library_Types = {
    "Audio": {
        "manager": AudioLibrary,
        "icon": "audio-x-generic"
    },
    "Video": [],
    "Image": []
}

db_name = "media_lib.sqlite"  # os.path.join(os.getcwd(), "media_lib.sqlite")
db_template = "media_lib_template.sqlite"
if not os.path.exists(db_name):
    MediaLib.logger.warn("Media library not found. Creating new library from template")
    create_new_database()

db = sqlite3.connect(db_name, check_same_thread=False)
db.isolation_level = None