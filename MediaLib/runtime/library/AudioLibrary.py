import os

from mutagen.id3 import ID3

import CommonUtils
import MediaLib
import mutagen

from mutagen.easyid3 import EasyID3
from CommonUtils import FileScanner

EasyID3.RegisterTextKey('comment', 'COMM::eng')

def supported_types():
    """
        List out all the types supported by this Library
    """
    return _supported_types.copy()


def scan_files(library_name, dirs_in_library, db_conn):
    """
        Scans the files into the connection and associates with the library
    """
    MediaLib.logger.info(f"Scanning audio library {library_name}")
    files = FileScanner(dirs_in_library, recurse=True, supported_extensions=supported_types(), is_qfiles=False).files
    MediaLib.logger.info(f"Found {len(files)} files to add to {library_name}")
    # Step 3: Extract all tags from the file into the database
    _extract_tags_and_save(library_name, files, db_conn)


def _extract_tags_and_save(library_name, files, db_conn):
    for file in files:
        _, ext = os.path.splitext(file)
        file_path, file_name = os.path.split(file)
        stats = os.stat(file)
        params = (
            library_name,
            file_name,
            file_path,
            stats.st_size,
            CommonUtils.calculate_sha256_hash(file),
            stats.st_ctime,
            stats.st_atime,
        ) + _supported_types_readers[ext.lower()](file)
        db_conn.execute("INSERT INTO audio VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", params)


def _save_flac(file):
    tag_data = mutagen.File(file, easy=True)
    params = (
        _read_or_default(tag_data.tags, 'album'),
        _read_or_default(tag_data.tags, 'albumartist'),
        _read_or_default(tag_data.tags, 'artist'),
        _read_or_default(tag_data.tags, 'date'),
        _read_or_default(tag_data.tags, 'genre'),
        _read_or_default(tag_data.tags, 'title'),
        _read_or_default(tag_data.tags, 'tracknumber'),
        _read_or_default(tag_data.tags, 'comment'),
        tag_data.info.channels,
        tag_data.info.length,
        tag_data.info.sample_rate,
        tag_data.info.bitrate,
        "Free Lossless Audio Codec (FLAC)",
        None,
        None,
        tag_data.info.bits_per_sample,
        tag_data.info.total_samples,
    )
    return params


def _save_mp3(file):
    #https://github.com/nex3/mdb
    audio = ID3(file)
    comment = None
    for key in audio.keys():
        if key.startswith('COMM'):
            comment = audio.get(key, None)
    tag_data = mutagen.File(file, easy=True)
    params = (
        _read_or_default(tag_data.tags, 'album'),
        _read_or_default(tag_data.tags, 'albumartist'),
        _read_or_default(tag_data.tags, 'artist'),
        _read_or_default(tag_data.tags, 'date'),
        _read_or_default(tag_data.tags, 'genre'),
        _read_or_default(tag_data.tags, 'title'),
        _read_or_default(tag_data.tags, 'tracknumber'),
        comment,
        tag_data.info.channels,
        tag_data.info.length,
        tag_data.info.sample_rate,
        tag_data.info.bitrate,
        tag_data.info.encoder_info,
        tag_data.info.encoder_settings,
        str(tag_data.info.bitrate_mode),
        None,
        None,
    )
    return params



def _save_mp4(file):
    tag_data = mutagen.File(file, easy=True)
    params = (
        _read_or_default(tag_data.tags, 'album'),
        _read_or_default(tag_data.tags, 'albumartist'),
        _read_or_default(tag_data.tags, 'artist'),
        _read_or_default(tag_data.tags, 'date'),
        _read_or_default(tag_data.tags, 'genre'),
        _read_or_default(tag_data.tags, 'title'),
        _read_or_default(tag_data.tags, 'tracknumber'),
        _read_or_default(tag_data.tags, 'comment'),
        tag_data.info.channels,
        tag_data.info.length,
        tag_data.info.sample_rate,
        tag_data.info.bitrate,
        tag_data.info.codec,
        tag_data.info.codec_description,
        None,
        tag_data.info.bits_per_sample,
        None,
    )
    return params


def _read_or_default(tag, field):
    if tag[field] is None:
        print(field + "is null!!")
        return None
    print(f"value for {field} is {tag[field]} of type {type(tag[field])}")
    return tag[field][0]



_supported_types = [".mp3",".flac",".mp4"]
_supported_types_readers = {
    ".flac": _save_flac,
    ".mp3": _save_mp3,
    ".mp4": _save_mp4
}
