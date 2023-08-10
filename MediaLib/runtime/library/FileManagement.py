import datetime
import json
import sqlite3
from collections import defaultdict

import MediaLib
from MediaLib.runtime.library.Domain import TaskStatus, FileRecord
from MediaMetaData import MetaDataFields


def delete_files(library, files, db_conn, task):
    """
    Deletes the specified files from the database
    """
    task.log_and_save(TaskStatus.Running,
                      f"About to delete {len(files)} records from the library {library.name}", db_conn)
    filez = list(map(lambda x: x.file, files))
    batches = [filez[x:x + __LIB_BATCH_SIZE] for x in range(0, len(filez), __LIB_BATCH_SIZE)]

    db_conn.execute("begin")
    try:
        for batch in batches:
            sql = f"DELETE from 'files' where library=? and file in ({','.join('?' * len(batch))})"
            batch.insert(0, library.name)
            db_conn.execute(sql, batch)
        db_conn.execute('commit')
    except sqlite3.Error as e:
        task.log_and_save(TaskStatus.Failed, f"Unable to delete files because of the error {e}", db_conn)
        db_conn.execute("rollback")

    MediaLib.logger.info(f"Files deleted")


def delete_library(library, db_conn):
    """
    Deletes all files from the specified library
    """
    MediaLib.logger.info(f"About to delete all files from the library {library.name}")
    db_conn.execute("DELETE FROM 'files' where library=?", [library.name])
    MediaLib.logger.info(f"Files deleted")


def get_files(library, db_conn):
    def dict_factory(cursor, _row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = _row[idx]
        return d

    MediaLib.logger.info(f"Fetching files from library: {library.name}")
    db_files = []
    results = db_conn.execute(__LIB_SELECT_SQL, [library.name])

    for row in results:
        data = dict_factory(results, row)
        file = data.pop(__LIB_FIELD_FILE)
        cataloged = datetime.datetime.fromisoformat(data.pop(__LIB_FIELD_CATALOGED))
        catalog_updated = data.pop(__LIB_FIELD_CATALOG_UPDATED)
        if catalog_updated:
            catalog_updated = datetime.datetime.fromisoformat(catalog_updated)
        metadata = {MetaDataFields[k]: v for k, v in data.items()}
        db_files.append(FileRecord(file, metadata, cataloged, catalog_updated))

    MediaLib.logger.info(f"Found {len(db_files)} records in the database")
    return db_files


def insert_files(library, files, db_conn, task):
    """
    Inserts the specified files into the database
    """
    inserts = []

    def do_insert(_inserts):
        MediaLib.logger.debug(f"Inserting block of {len(_inserts)} records")
        db_conn.executemany(__LIB_INSERT_SQL, _inserts)

    task.log_and_save(TaskStatus.Running,
                      f"About to insert {len(files)} records into library {library.name}", db_conn)
    db_conn.execute("begin")
    try:
        for file in files:
            params = defaultdict(lambda: None)
            params[__LIB_FIELD_LIBRARY] = library.name
            params[__LIB_FIELD_FILE] = file.file
            params[__LIB_FIELD_CATALOGED] = file.cataloged
            params[__LIB_FIELD_CATALOG_UPDATED] = file.catalog_updated
            for field in MetaDataFields:
                if field == MetaDataFields.exif_tags:
                    params[field.name] = json.dumps(file.metadata[field])
                else:
                    params[field.name] = file.metadata[field]
            inserts.append(params)
            if len(inserts) > __LIB_BATCH_SIZE:
                do_insert(inserts)
                inserts = []
        if len(inserts):
            do_insert(inserts)
        db_conn.execute('commit')
    except sqlite3.Error as e:
        task.log_and_save(TaskStatus.Running,
                          f"Unable to insert files into library because of the error {e}", db_conn)
        db_conn.execute("rollback")


__LIB_INSERT_SQL = f"INSERT INTO 'files' (library, file, cataloged, catalog_updated, " \
                   f"{', '.join([e.name for e in MetaDataFields])}) " \
                   f"VALUES(:library, :file, :cataloged, :catalog_updated, " \
                   f":{', :'.join([e.name for e in MetaDataFields])})"
__LIB_SELECT_SQL = f"SELECT file, cataloged, catalog_updated, " \
                   f"{', '.join([e.name for e in MetaDataFields])} " \
                   f"FROM 'files' WHERE library = ? ORDER BY 'file'"
__LIB_BATCH_SIZE = 100
__LIB_FIELD_LIBRARY = "library"
__LIB_FIELD_FILE = "file"
__LIB_FIELD_CATALOGED = "cataloged"
__LIB_FIELD_CATALOG_UPDATED = "catalog_updated"
