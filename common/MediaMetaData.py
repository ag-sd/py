import json
import mimetypes
import os.path
import shlex
import subprocess
from collections import defaultdict
from datetime import datetime
from enum import Enum
from shutil import which

from common import CommonUtils

_MISSING_DATA = "Not Available"
# http://www.imagemagick.org/script/identify.php
# https://www.imagemagick.org/script/identify.php
# ffprobe -hide_banner -v info -show_streams -show_format file_example_MP4_480_1_5MG.mp4 -of json -of json
_IMAGE_COMMAND_ARGS = "magick identify -verbose "
_MEDIA_COMMAND_ARGS = "ffprobe -v error -select_streams a:0 -show_entries " \
                "'stream=codec_name,codec_long_name,codec_type,channels,channel_layout," \
                "sample_rate,bits_per_sample,avg_frame_rate : format=bit_rate,duration,format_long_name,size : " \
                "format_tags : stream_tags' -of json "
_CHUNK_SIZE = 8192

if which("ffprobe") is None:
    raise Exception("This package requires ffprobe which was not found on this system")

if which("magick") is None:
    raise Exception("This package requires imagemagick which was not found on this system")

mimetypes.init()


def get_metadata(file, include_checksum=False):
    def _add_checksum(_metadata):
        if include_checksum:
            _metadata[MetaDataFields.checksum] = CommonUtils.calculate_sha256_hash(file)
        return _metadata

    if not os.path.exists(file):
        return None

    try:
        mime_type = mimetypes.guess_type(file)[0].upper()
    except AttributeError:
        return None

    metadata = defaultdict(lambda: None)
    if mime_type.startswith("IMAGE"):
        metadata = _get_image_metadata(_execute(_IMAGE_COMMAND_ARGS + f"\"{file}\""))
    elif mime_type.startswith("AUDIO") or mime_type.startswith("VIDEO"):
        m_metadata = _execute(_MEDIA_COMMAND_ARGS + f"\"{file}\"")
        if m_metadata:
            metadata = _get_media_metadata(json.loads(m_metadata))
    _add_file_details(file, metadata)
    _add_checksum(metadata)
    return metadata


def _get_image_metadata(metadata):
    params = defaultdict(lambda: None)
    for line in metadata.split("\n"):
        line = line.strip()
        for metadata_field in MetaDataFields:
            if metadata_field.magick_key and line.startswith(metadata_field.magick_key):
                value = line.split(metadata_field.magick_key)[1].strip()
                if metadata_field == MetaDataFields.exif_tags:
                    key, exif_value = value.split(":", 1)
                    if metadata_field in params:
                        params[metadata_field][key.strip()] = exif_value.strip()
                    else:
                        params[metadata_field] = {key.strip(): exif_value.strip()}
                else:
                    params[metadata_field] = line.split(metadata_field.magick_key)[1].strip()
    return params


def _get_media_metadata(metadata):
    def _merge_fields(source, dest, fields):
        for field in fields:
            if field.name in source:
                dest[field] = source[field.name]
        return dest

    params = defaultdict(lambda: None)
    if "streams" in metadata:
        if len(metadata["streams"]) > 0:
            stream_info = metadata["streams"][0]
            params = _merge_fields(stream_info, params, MetaDataFields.__lookup__["streams"])
            if "format" in metadata:
                format_info = metadata["format"]
                params = _merge_fields(format_info, params, MetaDataFields.__lookup__["format"])
                if "tags" in format_info:
                    tag_info = {k.lower(): v for k, v in format_info["tags"].items()}
                    params = _merge_fields(tag_info, params, MetaDataFields.__lookup__["tags"])
        else:
            return None

    return params


def _add_file_details(file, metadata):
    _, ext = os.path.splitext(file)
    file_path, file_name = os.path.split(file)
    stats = os.stat(file)
    metadata[MetaDataFields.filename] = file_name
    metadata[MetaDataFields.filepath] = file_path
    metadata[MetaDataFields.filesize] = stats.st_size
    metadata[MetaDataFields.created] = stats.st_ctime
    metadata[MetaDataFields.accessed] = stats.st_atime
    metadata[MetaDataFields.extension] = ext
    metadata[MetaDataFields.mimetype] = mimetypes.guess_type(file)[0]


def _execute(command):
    process = subprocess.Popen(
        shlex.split(command),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    output, _ = process.communicate()
    return output


class MetaDataFields(Enum):
    __lookup__ = {}

    codec_name = "codec_name", "streams", "Format:"
    codec_long_name = "codec_long_name", "streams", "Format:"
    codec_type = "codec_type", "streams"
    sample_rate = "sample_rate", "streams"
    channels = "channels", "streams"
    channel_layout = "channel_layout", "streams"
    bits_per_sample = "bits_per_sample", "streams"
    avg_frame_rate = "avg_frame_rate", "streams"
    bit_rate = "bit_rate", "format"
    duration = "duration", "format"
    format_long_name = "format_long_name", "format"
    size = "size", "format", "Filesize"
    album_artist = "album_artist", "tags"
    title = "title", "tags"
    artist = "artist", "tags"
    album = "album", "tags"
    track = "track", "tags"
    genre = "genre", "tags"
    comment = "comment", "tags"
    date = "date", "tags"
    creation_time = "creation_time", "tags", "date:create:"
    modification_time = "modification_time", None, "date:modify:"
    exif_tags = "exif_tags", None, "exif:"
    color_depth = "color_depth", None, "Depth:"
    geometry = "geometry", None, "Geometry:"
    units = "units", None, "Units:"
    colorspace = "colorspace", None, "Colorspace:"
    type = "type", None, "Type:"
    compression = "compression", None, "Compression:"
    quality = "quality", None, "Quality:"
    signature = "signature", None, "signature:"
    number_pixels = "number_pixels", None, "Number pixels:"
    checksum = "checksum", None
    filename = "filename", None
    filepath = "filepath", None
    filesize = "filesize", None
    created = "created", None
    accessed = "accessed", None
    extension = "extension", None
    mimetype = "mimetype", None

    def __init__(self, _, field_type=None, magick_key=None):
        if field_type:
            if field_type not in self.__class__.__lookup__:
                self.__class__.__lookup__[field_type] = []
            self.__class__.__lookup__[field_type].append(self)
        self.magick_key = magick_key

    def __str__(self):
        return self.name


if __name__ == '__main__':
    files = [

    ]

    repeats = 1
    start_time = datetime.now()
    for i in range(0, repeats):
        if i % 10 == 0:
            print(f"Currently processing {i}")

        for _file in files:
            print("dispatching " + _file)
            meta = get_metadata(_file, include_checksum=True)
            if meta:
                for field in MetaDataFields.__iter__():
                    print(f"{field}\t\t\t -> {meta[field]}")
    end_time = datetime.now()
    print(f"Completed {repeats * len(files)} requests in {(end_time - start_time).total_seconds()} seconds")



