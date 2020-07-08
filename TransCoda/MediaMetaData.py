import json
import shlex
import subprocess
from enum import Enum
from shutil import which

_MISSING_DATA = "Not Available"
# http://www.imagemagick.org/script/identify.php
# ffprobe -hide_banner -v info -show_streams -show_format file_example_MP4_480_1_5MG.mp4 -of json -of json
_COMMAND_ARGS = "ffprobe -v error -select_streams a:0 -show_entries " \
                "'stream=codec_name,codec_long_name,codec_type,channels,channel_layout," \
                "sample_rate,bits_per_sample,avg_frame_rate : format=bit_rate,duration,format_long_name,size : " \
                "format_tags : stream_tags' -of json "

if which("ffprobe") is None:
    raise Exception("This package requires ffprobe which was not found on this system")


def _probe(file):
    cmd = _COMMAND_ARGS + f"\"{file}\""
    process = subprocess.Popen(
        shlex.split(cmd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    output, _ = process.communicate()
    return json.loads(output)


def get_metadata(file):
    metadata = _probe(file)
    if metadata:
        return _get_metadata(metadata)
    return None


def _get_metadata(metadata):
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


def _merge_fields(source, dest, fields):
    for field in fields:
        if field.name in source:
            dest[field] = source[field.name]
    return dest


class MetaDataFields(Enum):
    __lookup__ = {}

    codec_name = "codec_name", "streams"
    codec_long_name = "codec_long_name", "streams"
    codec_type = "codec_type", "streams"
    sample_rate = "sample_rate", "streams"
    channels = "channels", "streams"
    channel_layout = "channel_layout", "streams"
    bits_per_sample = "bits_per_sample", "streams"
    avg_frame_rate = "avg_frame_rate", "streams"
    bit_rate = "bit_rate", "format"
    duration = "duration", "format"
    format_long_name = "format_long_name", "format"
    size = "size", "format"
    album_artist = "album_artist", "tags"
    title = "title", "tags"
    artist = "artist", "tags"
    album = "album", "tags"
    track = "track", "tags"
    genre = "genre", "tags"
    comment = "comment", "tags"
    date = "date", "tags"
    creation_time = "creation_time", "tags"

    def __init__(self, _, field_type=None):
        if field_type:
            if field_type not in self.__class__.__lookup__:
                self.__class__.__lookup__[field_type] = []
            self.__class__.__lookup__[field_type].append(self)

    def __str__(self):
        return self.name


if __name__ == '__main__':
    files = [
        "/mnt/Stuff/testing/audio/(02) Winter Wonderland - Eurythmics.flac",
        "/mnt/Stuff/testing/audio/1_XdqiA-pdkeFuX5W2-NSaNg.jpeg",
        "/mnt/Stuff/testing/audio/AAC Album -  02 - AAC Title.aac",
        "/mnt/Stuff/testing/audio/Dir1",
        "/mnt/Stuff/testing/audio/Dir1/ff-16b-1c-8000hz.amr",
        "/mnt/Stuff/testing/audio/Dir1/ff-16b-2c-44100hz.aac",
        "/mnt/Stuff/testing/audio/Dir1/ff-16b-2c-44100hz.aiff",
        "/mnt/Stuff/testing/audio/Dir1/ff-16b-2c-44100hz.opus",
        "/mnt/Stuff/testing/audio/Dir1/file_example_MP3_2MG.mp3",
        "/mnt/Stuff/testing/audio/Dir1/file_example_OOG_1MG.ogg",
        "/mnt/Stuff/testing/audio/Dir1/TradIrish_BelfastHornpipe.wma",
        "/mnt/Stuff/testing/audio/dir1",
        "/mnt/Stuff/testing/audio/dir1/test1.flac",
        "/mnt/Stuff/testing/audio/dir1/test1.m4a",
        "/mnt/Stuff/testing/audio/Dir2",
        "/mnt/Stuff/testing/audio/Dir2/(01) Santa Claus Is Coming To Town - The Pointer Sisters.flac",
        "/mnt/Stuff/testing/audio/Dir2/(03) Do You Hear What I Hear  - Whitney Houston.flac",
        "/mnt/Stuff/testing/audio/Dir2/(04) Merry Christmas, Baby - Bruce Springsteen & The E Street Band.flac",
        "/mnt/Stuff/testing/audio/Dir2/BachCPE_SonataAmin_1.wma",
        "/mnt/Stuff/testing/audio/Dir2/Sample_BeeMoved_96kHz24bit.flac",
        "/mnt/Stuff/testing/audio/Dir2/stereo.flac",
        "/mnt/Stuff/testing/audio/Dir2/surround71.flac",
        "/mnt/Stuff/testing/audio/Donjon_Etude_1.wma",
        "/mnt/Stuff/testing/audio/Dream Theater - Black Clouds & Silver Linings - 2009 - 06 - The Count of Tuscany.mp3",
        "/mnt/Stuff/testing/audio/empty.txt",
        "/mnt/Stuff/testing/audio/example.ogg",
        "/mnt/Stuff/testing/audio/ff-16b-1c-8000hz.amr",
        "/mnt/Stuff/testing/audio/ff-16b-2c-44100hz (copy).wav",
        "/mnt/Stuff/testing/audio/ff-16b-2c-44100hz.ac3",
        "/mnt/Stuff/testing/audio/ff-16b-2c-44100hz.aiff",
        "/mnt/Stuff/testing/audio/ff-16b-2c-44100hz.opus",
        "/mnt/Stuff/testing/audio/ff-16b-2c-44100hz.ts",
        "/mnt/Stuff/testing/audio/ff-16b-2c-44100hz.wav",
        "/mnt/Stuff/testing/audio/file_example_MP3_1MG.mp3",
        "/mnt/Stuff/testing/audio/file_example_MP3_700KB.mp3",
        "/mnt/Stuff/testing/audio/file_example_MP4_480_1_5MG.mp4",
        "/mnt/Stuff/testing/audio/sample.aac",
        "/mnt/Stuff/testing/audio/sample4.aac",
        "/mnt/Stuff/testing/audio/Sample_BeeMoved_48kHz16bit.m4a",
        "/mnt/Stuff/testing/audio/Sub",
        "/mnt/Stuff/testing/audio/test1.mp3",
        "/mnt/Stuff/testing/audio/test1.mp4",
        "/mnt/Stuff/testing/audio/touch1",
    ]
    for _file in files:
        print("dispatching " + _file)
        meta = get_metadata(_file)
        print(meta)


class FFPROBEMetadataFetch(object):

    def __init__(self):
        super().__init__()
        self._command_args = "ffprobe -hide_banner -v info -show_format -show_streams -of json "

    def get_metadata(self, file):
        cmd = self._command_args + f"\"{file}\""
        process = subprocess.Popen(
            shlex.split(cmd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        output, stderr = process.communicate()

        return json.loads(output)