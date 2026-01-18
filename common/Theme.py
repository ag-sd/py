import os
from enum import Enum

from PyQt5.QtGui import QIcon

from common.CommonUtils import FileScanner


class _IconExtensions(Enum):
    svg = 0
    png = 1
    jpg = 2


class Theme:

    APP_ICON_KEY = "app_icon"

    def __init__(self, default_theme_dir, theme_dir=None):
        self.default_theme_dir = default_theme_dir
        self.theme_dir = theme_dir
        self._mime_cache = {}
        self._build_mime_cache()

    def _build_mime_cache(self):
        # Files to scan for
        extensions = [f".{x.name}" for x in _IconExtensions]
        # Scan the default theme dir and build the mime cache
        default_icons = FileScanner([self.default_theme_dir], recurse=True,
                                    supported_extensions=extensions, is_qfiles=False)
        self._add_files_to_cache(default_icons.files)
        # Then scan the theme dir and override the matches
        if self.theme_dir is not None:
            theme_icons = FileScanner(self.theme_dir, recurse=True,
                                      supported_extensions=extensions, is_qfiles=False)
            self._add_files_to_cache(theme_icons.files)

    def _add_files_to_cache(self, files):
        for file in files:
            _, file_name = os.path.split(file)
            file_name, _ = os.path.splitext(file_name)
            self._mime_cache[file_name] = QIcon(file)

    def fromTheme(self, mime_type_icon_name, use_system_fallback=True):
        if mime_type_icon_name not in self._mime_cache:
            if use_system_fallback:
                mime_icon = QIcon.fromTheme(mime_type_icon_name)
                self._mime_cache[mime_type_icon_name] = mime_icon
        return self._mime_cache[mime_type_icon_name]

    def app_icon(self):
        """
        Returns: An icon named app_icon from the them folder. If not found, a generic application icon is returned
        """
        if self.APP_ICON_KEY not in self._mime_cache:
            self._mime_cache[self.APP_ICON_KEY] = QIcon.fromTheme("application-x-executable")
        return self._mime_cache[self.APP_ICON_KEY]


if __name__ == "__main__":
    theme = Theme(os.path.join(os.path.dirname(__file__), "../TransCoda/resource/theme"), theme_dir=None)
