import datetime
import sqlite3
import atexit
import MediaLib
from MediaLib.runtime.library import AudioLibrary

Library_Types = {
    "Audio": AudioLibrary,  # "aac", "aiff", "asf", "ape", "flac", "mp3", "mp4", "ogg", "midi"],
    "Video": [],
    "Image": []
}
db_name = "media_lib.sqlite" # os.path.join(os.getcwd(), "media_lib.sqlite")
db = sqlite3.connect(db_name)
#--------------->db.isolation_level = None


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
    db.commit()

    # Step 2: Scan the dirs_in_library based on library_type
    Library_Types[library_type].scan_files(library_name, dirs_in_library, db_conn=conn)

    MediaLib.logger.info(f"Created library {library_name}")


def update_library(library_name, dirs_in_library):
    pass


def delete_library(library_name):
    pass


def rescan_library(library_name):
    pass


def close_database():
    print("Bye Bye!")
    db.commit()
    db.close()


atexit.register(close_database)
