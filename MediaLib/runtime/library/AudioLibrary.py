import os
from collections import defaultdict

import mutagen
from mutagen.id3 import ID3

import CommonUtils
import MediaLib
from MediaLib.runtime.library import LibraryManagement


def supported_types():
    """
        List out all the types supported by this Library
    """
    return _supported_types_readers.keys()


def get_group_keys():
    return set(_param_group_keys.keys())


def get_files(library_name, db_conn):
    MediaLib.logger.info(f"Fetching files in library {library_name}")
    db_files = {}
    results = db_conn.execute(
        f"SELECT file_path || '{os.path.sep}' || file_name, checksum FROM audio WHERE library=? ORDER BY file_path",
        [library_name])
    for row in results:
        db_files[row[0]] = row[1]

    MediaLib.logger.info(f"Found {len(db_files)} records in the database")
    return db_files


def delete_files(library_name, files, db_conn):
    """
    Deletes the specified files from the database
    """
    MediaLib.logger.info(f"About to delete {len(files)} records from the library {library_name}")
    chunks = [files[x:x + _lib_batch_size] for x in range(0, len(files), _lib_batch_size)]
    for chunk in chunks:
        sql = f"DELETE from audio where library=? and file_path || '{os.path.sep}' || file_name  " \
              f"in ({','.join('?' * len(chunk))})"
        chunk.insert(0, library_name)
        db_conn.execute(sql, chunk)

    MediaLib.logger.info(f"Files deleted")


def delete_library(library_name, db_conn):
    """
    Deletes all files from the specified library
    """
    MediaLib.logger.info(f"About to delete all files from the library {library_name}")
    db_conn.execute("DELETE FROM audio where library=?", [library_name])
    MediaLib.logger.info(f"Files deleted")


def insert_files(library_name, files, db_conn, task_id=None):
    """
    Inserts the specified files into the database
    """
    inserts = []
    counter = 0
    for file in files:
        _, ext = os.path.splitext(file)
        file_path, file_name = os.path.split(file)
        stats = os.stat(file)

        params = defaultdict(lambda: None)
        params[_param_library_name] = library_name
        params[_param_file_name] = file_name
        params[_param_file_path] = file_path
        params[_param_file_size] = stats.st_size
        params[_param_checksum] = files[file]
        params[_param_created] = stats.st_ctime
        params[_param_accessed] = stats.st_atime
        params = _supported_types_readers[ext.lower()](file, params)
        inserts.append(params)
        counter = counter + 1

        if len(inserts) > _lib_batch_size:
            MediaLib.logger.debug(f"Inserting block of {len(inserts)} records")
            db_conn.execute("BEGIN TRANSACTION")
            db_conn.executemany(_lib_insert_sql, inserts)
            db_conn.execute("COMMIT")

            if task_id:
                percent_50 = 50 + int((counter * 50) / len(files))
                LibraryManagement.update_task(task_id, f"Adding metadata for files", percent_50, db_conn)
            inserts = []

    if len(inserts):
        MediaLib.logger.debug(f"Inserting final block of {len(inserts)} records")
        db_conn.execute("BEGIN TRANSACTION")
        db_conn.executemany(_lib_insert_sql, inserts)
        db_conn.execute("COMMIT")


def create_model_dictionary(library_name, group_keys, db_conn):
    """
    Creates a model dictionary based on the group keys
    :param library_name
    :param group_keys:
    :param db_conn
    :return:
    """
    model = {}
    records = db_conn.execute("SELECT * FROM main.audio where library = ?", (library_name,))
    for record in records:
        print(record)


def _extract_tags_and_save(library_name, files, db_conn):
    inserts = []
    for file in files:
        _, ext = os.path.splitext(file)
        file_path, file_name = os.path.split(file)
        stats = os.stat(file)

        params = defaultdict(lambda: None)
        # Mime Type
        # Time of insertion
        params[_param_library_name] = library_name
        params[_param_file_name] = file_name
        params[_param_file_path] = file_path
        params[_param_file_size] = stats.st_size
        params[_param_checksum] = CommonUtils.calculate_sha256_hash(file)
        params[_param_created] = stats.st_ctime
        params[_param_accessed] = stats.st_atime
        params = _supported_types_readers[ext.lower()](file, params)
        inserts.append(params)

        # MediaLib.logger.debug(f"Extracted the following data for audio file {params}")

        if len(inserts) > _lib_batch_size:
            MediaLib.logger.debug(f"Inserting block of {len(inserts)} records")
            db_conn.execute("BEGIN TRANSACTION")
            db_conn.executemany(_lib_insert_sql, inserts)
            db_conn.execute("COMMIT")
            inserts = []

    if len(inserts):
        MediaLib.logger.debug(f"Inserting final block of {len(inserts)} records")
        db_conn.execute("BEGIN TRANSACTION")
        db_conn.executemany(_lib_insert_sql, inserts)
        db_conn.execute("COMMIT")


def _save_mp3(file, params):
    # https://github.com/nex3/mdb
    # print(file)
    audio = ID3(file)
    for key in audio.keys():
        if key.startswith('COMM'):
            params[_param_comment] = audio.get(key).text[0]
    tag_data = mutagen.File(file, easy=True)
    for key in sorted(tag_data.tags):
        if _param_lookup.__contains__(key):
            params[key] = tag_data.tags[key][0]

    params[_param_channels] = tag_data.info.channels
    params[_param_length] = tag_data.info.length
    params[_param_sample_rate] = tag_data.info.sample_rate
    params[_param_bitrate] = tag_data.info.bitrate
    params[_param_encoder_info] = tag_data.info.encoder_info
    params[_param_encoder_settings] = tag_data.info.encoder_settings
    params[_param_bitrate_mode] = str(tag_data.info.bitrate_mode)

    return params


def _save_flac(file, params):
    tag_data = mutagen.File(file, easy=True)
    if tag_data.tags is not None:
        for kvp in sorted(tag_data.tags):
            key = kvp[0].lower()
            if _param_lookup.__contains__(key):
                params[key] = kvp[1]
    params[_param_channels] = tag_data.info.channels
    params[_param_length] = tag_data.info.length
    params[_param_sample_rate] = tag_data.info.sample_rate
    params[_param_bitrate] = tag_data.info.bitrate
    params[_param_encoder_info] = "Free Lossless Audio Codec (FLAC)"
    params[_param_bits_per_sample] = str(tag_data.info.bits_per_sample)
    params[_param_total_samples] = str(tag_data.info.total_samples)
    return params


def _save_ogg(file, params):
    tag_data = mutagen.File(file, easy=True)
    if tag_data.tags is not None:
        for kvp in sorted(tag_data.tags):
            key = kvp[0].replace(' ', '').lower()
            if _param_lookup.__contains__(key):
                params[key] = kvp[1]
    params[_param_channels] = tag_data.info.channels
    params[_param_length] = tag_data.info.length
    params[_param_sample_rate] = tag_data.info.sample_rate
    params[_param_bitrate] = tag_data.info.bitrate
    params[_param_encoder_info] = ""
    return params


def _save_mp4(file, params):
    tag_data = mutagen.File(file, easy=True)
    if tag_data.tags is not None:
        for key in sorted(tag_data.tags):
            if _param_lookup.__contains__(key):
                params[key] = tag_data.tags[key][0]

    params[_param_channels] = tag_data.info.channels
    params[_param_length] = tag_data.info.length
    params[_param_sample_rate] = tag_data.info.sample_rate
    params[_param_bitrate] = tag_data.info.bitrate
    params[_param_encoder_info] = tag_data.info.codec
    params[_param_encoder_settings] = tag_data.info.codec_description
    params[_param_bits_per_sample] = str(tag_data.info.bits_per_sample)
    return params


def _save_wma(file, params):
    tag_data = mutagen.File(file, easy=True)
    if tag_data.tags is not None:
        tags = tag_data.tags.as_dict()
        if tags["IsVBR"][0].value:
            params[_param_bitrate_mode] = "VBR"
        else:
            params[_param_bitrate_mode] = "Non-VBR"

        for key in tags:
            if _asf_key_map.__contains__(key):
                value = tags[key][0].value
                if value:
                    params[_asf_key_map[key]] = value
    params[_param_channels] = tag_data.info.channels
    params[_param_length] = tag_data.info.length
    params[_param_sample_rate] = tag_data.info.sample_rate
    params[_param_bitrate] = tag_data.info.bitrate
    params[_param_encoder_info] = tag_data.info.codec_name
    params[_param_encoder_settings] = tag_data.info.codec_description

    return params


_supported_types_readers = {
    ".flac": _save_flac,
    ".mp3": _save_mp3,
    ".mp4": _save_mp4,
    ".m4a": _save_mp4,
    ".ogg": _save_ogg,
    ".wma": _save_wma,
}

_asf_key_map = {
    "WM/AlbumTitle": "album",
    "Title": "title",
    "Author": "artist",
    "WM/AlbumArtist": "albumartist",
    "WM/TrackNumber": "tracknumber",
    "Description": "comment",
    "WM/Year": "date",
    "WM/Genre": "genre"
}

_param_album = 'album'
_param_albumartist = 'albumartist'
_param_artist = 'artist'
_param_date = 'date'
_param_genre = 'genre'
_param_title = 'title'
_param_tracknumber = 'tracknumber'
_param_comment = 'comment'
_param_channels = 'channels'
_param_length = 'length'
_param_sample_rate = 'sample_rate'
_param_bitrate = 'bitrate'
_param_bits_per_sample = 'bits_per_sample'
_param_encoder_info = 'encoder_info'
_param_encoder_settings = 'encoder_settings'
_param_bitrate_mode = 'bitrate_mode'
_param_total_samples = 'total_samples'
_param_library_name = 'library'
_param_file_name = 'file_name'
_param_file_path = 'file_path'
_param_file_size = 'file_size'
_param_checksum = 'checksum'
_param_created = 'created'
_param_accessed = 'accessed'

_param_group_keys = {
    "Album": _param_album,
    "Album Artist": _param_albumartist,
    "Artist": _param_artist,
    "Genre": _param_genre,
    "Year": _param_date
}

_param_lookup = [
    _param_library_name,
    _param_file_name,
    _param_file_path,
    _param_file_size,
    _param_checksum,
    _param_created,
    _param_accessed,
    _param_album,
    _param_albumartist,
    _param_artist,
    _param_date,
    _param_genre,
    _param_title,
    _param_tracknumber,
    _param_comment,
    _param_channels,
    _param_length,
    _param_sample_rate,
    _param_bitrate,
    _param_encoder_info,
    _param_encoder_settings,
    _param_bitrate_mode,
    _param_bits_per_sample,
    _param_total_samples,
]

_lib_insert_sql = f"INSERT INTO audio VALUES(:{', :'.join(_param_lookup)})"
_lib_batch_size = 100
