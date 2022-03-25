import os

from PyQt5.QtGui import QIcon


class Theme:
    __DEFAULT_PATH__ = os.path.join(os.path.dirname(__file__), "../resource/theme")

    def __init__(self, resource_dir):
        self.resource_dir = resource_dir

        self.ico_app_icon = self._get_icon("TSLogo")
        self.ico_progress_done = self._get_icon("progress_done")
        self.ico_progress_unknown = self._get_icon("progress_unknown")
        self.ico_terminal = self._get_icon("utilities-terminal")
        self.ico_add = self._get_icon("list-add")
        self.ico_add_item = self._get_icon("list-add-item")
        self.ico_clear = self._get_icon("edit-clear")
        self.ico_folder = self._get_icon("folder-new")
        self.ico_settings = self._get_icon("preferences-system")
        self.ico_start = self._get_icon("media-playback-start")
        self.ico_stop = self._get_icon("media-playback-stop")
        self.ico_refresh = self._get_icon("view-refresh")
        self.ico_help_about = self._get_icon("help-about")
        self.ico_help_contents = self._get_icon("help-contents")
        self.ico_edit = self._get_icon("accessories-text-editor")
        self.mime_cache = {}

    def get_mime_icon(self, mime_type_icon_name):
        if mime_type_icon_name not in self.mime_cache:
            mime_icon = QIcon.fromTheme(mime_type_icon_name)
            if mime_icon is None:
                self._get_icon("text-x-generic")
            self.mime_cache[mime_type_icon_name] = mime_icon
        return self.mime_cache[mime_type_icon_name]

    def _get_icon(self, ico_name):
        file_name = f"{ico_name}.svg"
        theme_location = os.path.join(self.resource_dir, file_name)
        default_location = os.path.join(self.__DEFAULT_PATH__, file_name)
        if os.path.exists(theme_location):
            return QIcon(theme_location)
        elif os.path.exists(default_location):
            return QIcon(default_location)
        else:
            return QIcon.fromTheme(ico_name)

