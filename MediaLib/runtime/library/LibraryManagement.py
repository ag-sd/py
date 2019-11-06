import datetime
import os
import shutil
import sqlite3
import atexit

import CommonUtils
import MediaLib
from CommonUtils import FileScanner
from MediaLib.runtime.library import AudioLibrary
from collections import defaultdict


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
                "modifed": row[4]
            }
        )
    conn.close()
    return result_dict


def create_library(library_name, library_type, dirs_in_library):
    """
        Creates a library of the given name and type.

        Note: Will throw an error if the library already exists. It is the responsibility
        of the calling method to determine if a library with the same name exists
    """
    MediaLib.logger.info(f"Creating library name={library_name} of type={library_type} with dirs={dirs_in_library}")
    conn = db.cursor()

    # Step 1: First create the library entry
    params = (library_name, library_type, "|".join(dirs_in_library), "{:%Y-%m-%d %H:%M:%S}".format(datetime.datetime.now()))
    conn.execute("INSERT INTO library (name, type, dirs, created) VALUES (?,?,?,?)", params)

    lib_manager = Library_Types[library_type]['manager']
    refresh_library({
        "name": library_name,
        "type": library_type,
        "dirs": dirs_in_library
    })

    # Step 2: Scan the dirs_in_library based on library_type
    # Library_Types[library_type]['manager'].scan_files(library_name, dirs_in_library, db_conn=conn)

    conn.close()
    MediaLib.logger.info(f"Created library {library_name}")


def update_library(library_name, dirs_in_library):
    pass


def delete_library(library_name):
    pass


def refresh_library(library):
    """
    Updates a library by adding new files, removing non-existent files
    and updating changed files
    :param library_name: The library to update
    :return:
    """
    MediaLib.logger.info(f"Refreshing {library['name']}")
    # Step 1: Get the library details
    conn = db.cursor()
    lib_manager = Library_Types[library['type']]['manager']

    # Step 2: Get files in library that are in the database
    db_files = lib_manager.get_files(library['name'], conn)

    # Step 3: Get the files of this library from the filesystem
    fs_files = FileScanner(library['dirs'], recurse=True,
                           supported_extensions=lib_manager.supported_types(),
                           is_qfiles=False).files

    # Step 4: Compare the 2 data-sets and identify inserts, updates and deletes
    updates = {}
    inserts = {}
    for file in fs_files:
        db_checksum = db_files.pop(file)
        fs_checksum = CommonUtils.calculate_sha256_hash(file)
        if db_checksum is None:
            # New file
            inserts[file] = fs_checksum
        elif db_checksum != fs_checksum:
            # File exists in db but checksum is different. Update the file in database
            updates[file] = fs_checksum
    # What is left in the db needs to be deleted as it was not found in the filesystem
    deletes = db_files.keys()

    MediaLib.logger.info(f"{len(updates)} files require to be updated in library")
    MediaLib.logger.info(f"{len(inserts)} files require to be inserted in library")
    MediaLib.logger.info(f"{len(deletes)} files require to be deleted from library")

    # Step 5: Insert the data
    lib_manager.delete_files(library['name'], list(updates.keys()) + list(deletes), conn)
    lib_manager.insert_files(library['name'], updates.update(inserts), conn)

    conn.close()
    pass


def close_database():
    db.commit()
    db.close()
    MediaLib.logger.info(f"Committed and closed {MediaLib.__APP_NAME__} library")


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

db = sqlite3.connect(db_name)
db.isolation_level = None
