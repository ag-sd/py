import os
from collections import defaultdict
from pprint import pprint

import mutagen
from mutagen.id3 import ID3

import CommonUtils
import MediaLib
from CommonUtils import FileScanner


def supported_types():
    """
        List out all the types supported by this Library
    """
    return _supported_types_readers.keys()


def scan_files(library_name, dirs_in_library, db_conn):
    """
        Scans the files into the connection and associates with the library
    """
    MediaLib.logger.info(f"Scanning audio library {library_name}")
    files = FileScanner(dirs_in_library, recurse=True, supported_extensions=supported_types(), is_qfiles=False).files
    MediaLib.logger.info(f"Found {len(files)} files to add to {library_name}")
    # Step 3: Extract all tags from the file into the database
    _extract_tags_and_save(library_name, files, db_conn)


def refresh_library(library_name, dirs_in_library, db_conn):
    """
        Scans and updates all files in a library.
    """
    MediaLib.logger.info(f"Scanning audio library {library_name}")
    # Step 1: Get the files of this library that are currently in the database
    db_files = {}
    results = db_conn.execute(f"SELECT file_path || {os.path.sep} || file_name, checksum from audio ORDER BY file_path")
    for row in results:
        db_files[row[0]]: row[1]

    MediaLib.logger.info(f"Found {len(db_files)} records in the database")

    # Step 2: Get the files of this library from the filesystem
    fs_files = FileScanner(dirs_in_library, recurse=True, supported_extensions=supported_types(), is_qfiles=False).files

    # Step 3: Compare the 2 data-sets and identify inserts, updates and deletes
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


def delete_files(library_name, files, db_conn):
    """
    Deletes the specified files from the database
    """
    pass


def insert_files(library_name, files, db_conn):
    """
    Inserts the specified files into the database
    """
    for file in files:
        _, ext = os.path.splitext(file)
        file_path, file_name = os.path.split(file)
        stats = os.stat(file)

        params = defaultdict(lambda: None)
        params[_param_library_name] = library_name
        params[_param_file_name] = file_name
        params[_param_file_path] = file_path
        params[_param_file_size] = stats.st_size
        params[_param_checksum] = CommonUtils.calculate_sha256_hash(file)
        params[_param_created] = stats.st_ctime
        params[_param_accessed] = stats.st_atime
        params = _supported_types_readers[ext.lower()](file, params)
        inserts.append(params)

        MediaLib.logger.debug(f"Extracted the following data for audio file {params}")

        if len(inserts) > _lib_insert_batch:
            MediaLib.logger.debug(f"Inserting block of {len(inserts)} records")
            db_conn.executemany(_lib_insert_sql, inserts)
            inserts = []

    if len(inserts):
        MediaLib.logger.debug(f"Inserting final block of {len(inserts)} records")
        db_conn.executemany(_lib_insert_sql, inserts)




def _extract_tags_and_save(library_name, files, db_conn):
    inserts = []
    for file in files:
        _, ext = os.path.splitext(file)
        file_path, file_name = os.path.split(file)
        stats = os.stat(file)

        params = defaultdict(lambda: None)
        params[_param_library_name] = library_name
        params[_param_file_name] = file_name
        params[_param_file_path] = file_path
        params[_param_file_size] = stats.st_size
        params[_param_checksum] = CommonUtils.calculate_sha256_hash(file)
        params[_param_created] = stats.st_ctime
        params[_param_accessed] = stats.st_atime
        params = _supported_types_readers[ext.lower()](file, params)
        inserts.append(params)

        MediaLib.logger.debug(f"Extracted the following data for audio file {params}")

        if len(inserts) > _lib_insert_batch:
            MediaLib.logger.debug(f"Inserting block of {len(inserts)} records")
            db_conn.executemany(_lib_insert_sql, inserts)
            inserts = []

    if len(inserts):
        MediaLib.logger.debug(f"Inserting final block of {len(inserts)} records")
        db_conn.executemany(_lib_insert_sql, inserts)


def _save_mp3(file, params):
    # https://github.com/nex3/mdb
    audio = ID3(file)
    for key in audio.keys():
        if key.startswith('COMM'):
            params[_param_comment] = audio.get(key).text[0]
            print(key)
            pprint(params)
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
_lib_insert_batch = 10
print(_lib_insert_sql)
