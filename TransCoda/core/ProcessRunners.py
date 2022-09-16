import datetime
import os
import random
import re
import shlex
import shutil
import subprocess
from shutil import which

from PyQt5.QtCore import QObject, pyqtSignal


class ProcessRunner(QObject):
    status_event = pyqtSignal(str, int, int)
    message_event = pyqtSignal(str, 'PyQt_PyObject', str)

    def __init__(self, **kwargs):
        super().__init__()
        self.__dict__.update(kwargs)
        self.status_throttle = 0

    def update_status(self, input_file, total, completed):
        if self.status_throttle == 0:
            self.status_event.emit(input_file, total, completed)
            self.status_throttle = random.randint(3, 9)
        else:
            self.status_throttle = self.status_throttle - 1


class FileCopyProcessRunner(ProcessRunner):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def run(self):
        shutil.copy2(src=self.input_file, dst=self.output_file, follow_symlinks=True)
        self.update_status(self.input_file, 100, 100)


class YoutubeDlProcessRunner(ProcessRunner):
    _split_token = "{-}"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.progress = 0
        if which("youtube-dl") is None:
            raise EncoderNotFoundException

    def run(self):
        command = f"youtube-dl {self.input_url} {self.base_command} \'{self._get_file_name()}\'"
        self.message_event.emit(self.input_file, datetime.datetime.now(), command)
        process = subprocess.Popen(
            shlex.split(command),
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )

        for line in process.stderr:
            self.message_event.emit(self.input_file, datetime.datetime.now(), line)
            self.progress = self.progress + 1
            if self.progress >= 100:
                self.progress = 0
            self.update_status(self.input_file, 100, self.progress)

    def _get_file_name(self):
        file_name_command = f"youtube-dl --get-filename --output-na-placeholder '' " \
                            f"-o '%(artist)s{self._split_token}%(title)s.%(ext)s' {self.input_url}"
        file_name_hint = subprocess.check_output(shlex.split(file_name_command)).decode("utf-8").strip()
        file_tokens = file_name_hint.split("{-}")
        final_tokens = filter(lambda x: x != "", file_tokens)
        file_name = " - ".join(final_tokens)
        return os.path.join(self.output_file, file_name)


class YoutubeDlFfmpegProcessRunner(YoutubeDlProcessRunner):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if which("ffmpeg") is None:
            raise EncoderNotFoundException

    def run(self):
        commands = self.base_command.split("|")
        output_file = self._get_file_name()
        file, _ = os.path.splitext(output_file)
        output_file = file + ".mp3"
        youtube_dl_pipe = f"youtube-dl {self.input_url} " + commands[0].strip()
        ffmpeg_pipe = commands[1].strip() + f" \"{output_file}\""
        self.message_event.emit(self.input_file, datetime.datetime.now(), f"yt-dl : {youtube_dl_pipe}")
        self.message_event.emit(self.input_file, datetime.datetime.now(), f"ffmpeg: {ffmpeg_pipe}")

        p1 = subprocess.Popen(shlex.split(youtube_dl_pipe),
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              universal_newlines=True)
        subprocess.Popen(shlex.split(ffmpeg_pipe), stdin=p1.stdout)

        for line in p1.stderr:
            self.message_event.emit(self.input_file, datetime.datetime.now(), line)
            dur_line = re.search("\\[download].* of.*", line.lower())
            if dur_line:
                line = line.replace("[download]", "")
                tokens = line.split("%")
                if len(tokens):
                    self.update_status(self.input_file, 100, float(tokens[0]))


class FFMPEGProcessRunner(ProcessRunner):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if which("ffmpeg") is None:
            raise EncoderNotFoundException

    def run(self):
        command = self.generate_command()
        self.message_event.emit(self.input_file, datetime.datetime.now(), command)
        process = subprocess.Popen(
            shlex.split(command),
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )

        duration_found = False
        time_seeking = False
        total_secs = 0
        for line in process.stderr:
            self.message_event.emit(self.input_file, datetime.datetime.now(), line)
            if not duration_found:
                dur = re.search("duration: [0-9:]+", line.lower())
                if dur:
                    total_secs = self.get_seconds(dur.group(0)[10:])
                    duration_found = True
                    time_seeking = True
            elif time_seeking:
                time = re.search("time=[0-9:]+", line.lower())
                if time:
                    completed = self.get_seconds(time.group(0)[5:])
                    self.update_status(self.input_file, total_secs, completed)

    @staticmethod
    def get_seconds(string):
        h, m, s = string.split(':')
        return int(datetime.timedelta(hours=int(h), minutes=int(m), seconds=int(s)).total_seconds())

    def generate_command(self):
        return f"ffmpeg" \
               f" -hide_banner -loglevel repeat+verbose -y" \
               f" {'-map_metadata -1' if self.delete_metadata else ''}" \
               f" -i \"{self.input_file}\" {self.base_command} \"{self.output_file}\""


class HandbrakeProcessRunner(ProcessRunner):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if which("HandBrakeCLI") is None:
            raise EncoderNotFoundException

    def run(self):
        command = self.generate_command()
        self.message_event.emit(self.input_file, datetime.datetime.now(), command)
        process = subprocess.Popen(
            shlex.split(command),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )

        for line in process.stdout:
            self.message_event.emit(self.input_file, datetime.datetime.now(), line)
            progress = re.search("Encoding: task 1 of 1", line)
            if progress:
                txt = line.replace("Encoding: task 1 of 1, ", "")
                tokens = txt.split("%")
                self.update_status(self.input_file, 100, float(tokens[0]))
            elif line.startswith("Encode done!"):
                self.update_status(self.input_file, 100, 100)

    def generate_command(self):
        return f"HandBrakeCLI"\
               f" -i \"{self.input_file}\" {self.base_command} -o \"{self.output_file}\""


class EncoderNotFoundException(Exception):
    """Thrown when FFMPEG was not found in the system"""


runners_registry = {
    "ffmpeg": FFMPEGProcessRunner,
    "HandBrakeCLI": HandbrakeProcessRunner,
    "copy": FileCopyProcessRunner,
    "youtube-dl-ffmpeg": YoutubeDlFfmpegProcessRunner,
    "youtube-dl": YoutubeDlProcessRunner,
}
