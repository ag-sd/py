import os

from PyQt5.QtCore import QUrl

import CommonUtils
import MediaMetaData
import TransCoda
from MediaMetaData import MetaDataFields
from TransCoda.core import TransCodaHistory
from TransCoda.core.Encoda import EncoderStatus
from TransCoda.ui.File import FileItem, Header


class FileMetaDataExtractor(CommonUtils.Command):
    def __init__(self, input_files, batch_size=15):
        super().__init__()
        self.files = self._create_work_files(input_files)
        self.batch_size = batch_size

    def work_size(self):
        return self.batch_size

    def do_work(self):
        batch = []
        for item in self.files:
            if item.url is not None:
                item.status = EncoderStatus.READY
            elif item.status != EncoderStatus.REMOVE and item.is_supported():
                metadata = MediaMetaData.get_metadata(item.file)
                if not metadata:
                    item.status = EncoderStatus.UNSUPPORTED
                    item.update_output_file()
                else:
                    item.status = EncoderStatus.READY
                    if MetaDataFields.bit_rate not in metadata:
                        TransCoda.logger.error(f"Did not find bitrate in {item.file}!")
                    item_meta_data = {
                        Header.input_bitrate: metadata[MetaDataFields.bit_rate],
                        Header.input_duration: metadata[MetaDataFields.duration],
                        Header.input_encoder: metadata[MetaDataFields.codec_long_name],
                        Header.sample_rate: metadata[MetaDataFields.sample_rate],
                        Header.channels: metadata[MetaDataFields.channels],
                    }
                    self._add_optional_field(item_meta_data, Header.artist, metadata, MetaDataFields.artist)
                    self._add_optional_field(item_meta_data, Header.album_artist, metadata, MetaDataFields.album_artist)
                    self._add_optional_field(item_meta_data, Header.title, metadata, MetaDataFields.title)
                    self._add_optional_field(item_meta_data, Header.album, metadata, MetaDataFields.album)
                    self._add_optional_field(item_meta_data, Header.track, metadata, MetaDataFields.track)
                    self._add_optional_field(item_meta_data, Header.genre, metadata, MetaDataFields.genre)
                    item.add_metadata(item_meta_data)

            history = TransCodaHistory.get_history(item.display_name())
            if history:
                item.history_result = history

            batch.append(item)
            if len(batch) >= self.batch_size:
                self.signals.result.emit(batch)
                batch = []
        if len(batch):
            self.signals.result.emit(batch)

    @staticmethod
    def _add_optional_field(_dict, item_key, metadata, meta_key):
        if meta_key in metadata:
            _dict[item_key] = metadata[meta_key]

    @staticmethod
    def _create_work_files(input_files):
        work_file_list = []
        for file in input_files:
            _, extension = os.path.splitext(file)
            if extension.upper() == ".URLS":
                # Expand URLs
                work_file_list = work_file_list + FileMetaDataExtractor._read_m3u_or_similar(file)
            elif extension.upper() == ".M3U":
                # Expand M3U
                work_file_list = work_file_list + FileMetaDataExtractor._read_m3u_or_similar(file)
            elif extension.upper() == ".CUE":
                # Expand CUE
                pass
            else:
                work_file_list.append(FileItem(file))
        return work_file_list

    @staticmethod
    def _read_m3u_or_similar(file):
        item_to_remove = FileItem(file)
        item_list = [item_to_remove]
        # Try to read the file:
        try:
            item_to_remove.status = EncoderStatus.REMOVE
            with open(file, "r") as reader:
                for line in reader:
                    line = line.strip()
                    if not line.startswith("#"):
                        url = QUrl(line)
                        if url.isLocalFile() and os.path.exists(line):
                            # TODO: check with file_dir + line
                            item_list.append(FileItem(line))
                        elif url.authority() != "":
                            item_list.append(FileItem(file=file, url=line))
        except (UnicodeDecodeError, OSError):
            TransCoda.logger.warn(f"Could not open/read file:{file}. Transcoda will skip this file")
            item_to_remove.status = EncoderStatus.ERROR
            item_list = [item_to_remove]
            return item_list

        return item_list





