import json
import sqlite3
from collections import defaultdict
import datetime

import MediaLib
import MediaMetaData
from MediaMetaData import MetaDataFields


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


def delete_files(library, files, db_conn):
    """
    Deletes the specified files from the database
    """
    MediaLib.logger.info(f"About to delete {len(files)} records from the library {library.name}")
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
        MediaLib.logger.error(f"Unable to delete files from library because of the error {e}")
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


def insert_files(library, files, db_conn):
    """
    Inserts the specified files into the database
    """
    inserts = []

    def do_insert(_inserts):
        MediaLib.logger.debug(f"Inserting block of {len(_inserts)} records")
        db_conn.executemany(__LIB_INSERT_SQL, _inserts)

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
        MediaLib.logger.error(f"Unable to insert files into library because of the error {e}")
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
