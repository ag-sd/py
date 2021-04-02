import json
import mimetypes
import shlex
import subprocess
from enum import Enum
from shutil import which

_MISSING_DATA = "Not Available"
# http://www.imagemagick.org/script/identify.php
# https://www.imagemagick.org/script/identify.php
# ffprobe -hide_banner -v info -show_streams -show_format file_example_MP4_480_1_5MG.mp4 -of json -of json
_IMAGE_COMMAND_ARGS = "magick identify -verbose "
_MEDIA_COMMAND_ARGS = "ffprobe -v error -select_streams a:0 -show_entries " \
                "'stream=codec_name,codec_long_name,codec_type,channels,channel_layout," \
                "sample_rate,bits_per_sample,avg_frame_rate : format=bit_rate,duration,format_long_name,size : " \
                "format_tags : stream_tags' -of json "

if which("ffprobe") is None:
    raise Exception("This package requires ffprobe which was not found on this system")

if which("magick") is None:
    raise Exception("This package requires imagemagick which was not found on this system")


def get_metadata(file):
    mime_type = mimetypes.guess_type(file)[0].upper()
    if mime_type.startswith("IMAGE"):
        return _get_image_metadata(_execute(_IMAGE_COMMAND_ARGS + f"\"{file}\""))
    elif mime_type.startswith("AUDIO") or mime_type.startswith("VIDEO"):
        metadata = _execute(_MEDIA_COMMAND_ARGS + f"\"{file}\"")
        if metadata:
            return _get_media_metadata(json.loads(metadata))
    else:
        return None


def _get_image_metadata(metadata):
    params = {}
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

    params = {}
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
    filesize = "filesize", None, "Filesize:"
    number_pixels = "number_pixels", None, "Number pixels:"

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
        "/mnt/Stuff/testing/audio/1_XdqiA-pdkeFuX5W2-NSaNg.jpeg",
    ]
    for _file in files:
        print("dispatching " + _file)
        meta = get_metadata(_file)
        print(meta)
