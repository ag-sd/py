import datetime
import os
import shutil
import sqlite3
import atexit
import MediaLib
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

    # Step 2: Scan the dirs_in_library based on library_type
    Library_Types[library_type]['manager'].scan_files(library_name, dirs_in_library, db_conn=conn)

    conn.close()
    MediaLib.logger.info(f"Created library {library_name}")


def update_library(library_name, dirs_in_library):
    pass


def delete_library(library_name):
    pass


def refresh_library(library_name):
    """
    Updates a library by adding new files, removing non-existent files
    and updating changed files
    :param library_name: The library to update
    :return:
    """
    MediaLib.logger.info(f"Refreshing {library_name}")
    # Step 1: Get the library details
    lib = get_library(library_name)

    # Step 2: Get files in library that are in the database
    files_in_db = Library_Types[lib['type']]['manager']
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
