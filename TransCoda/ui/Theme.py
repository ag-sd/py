import os

from PyQt5.QtGui import QIcon, QBrush, QColor

from TransCoda.core.Encoda import EncoderStatus
from TransCoda.ui import TransCodaSettings


class StatusColor:
    def __init__(self, r, g, b, a, is_background_color):
        self.brush = QBrush(QColor(r, g, b, a))
        self.is_background_color = is_background_color
        self.is_foreground_color = not is_background_color


_status_color_map = {
    EncoderStatus.READY: StatusColor(255, 255, 255, 0, True),
    EncoderStatus.WAITING: StatusColor(255, 140, 0, 50, True),
    EncoderStatus.SUCCESS: StatusColor(152, 251, 152, 75, True),
    EncoderStatus.ERROR: StatusColor(220, 20, 60, 75, True),
    EncoderStatus.IN_PROGRESS: StatusColor(244, 164, 96, 75, True),
    EncoderStatus.READING_METADATA: StatusColor(192, 192, 192, 255, False),
    EncoderStatus.UNSUPPORTED: StatusColor(195, 195, 195, 125, True),
    EncoderStatus.SKIPPED: StatusColor(80, 90, 100, 125, True)
}


class Theme:

    __DEFAULT_PATH__ = os.path.join(os.path.dirname(__file__), "../resource/theme")

    def __init__(self, resource_dir):
        self.resource_dir = resource_dir

        self.ico_app_icon = self._get_icon("TSLogo", system_fallback=False)
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
        self.ico_doc = self._get_icon("document-open")
        self.mime_cache = {}

    def get_mime_icon(self, mime_type_icon_name):
        if mime_type_icon_name not in self.mime_cache:
            mime_icon = QIcon.fromTheme(mime_type_icon_name)
            if mime_icon is None:
                self._get_icon("text-x-generic")
            self.mime_cache[mime_type_icon_name] = mime_icon
        return self.mime_cache[mime_type_icon_name]

    @staticmethod
    def get_item_color(file_status, file_is_supported=True):
        if not file_is_supported:
            return _status_color_map[EncoderStatus.UNSUPPORTED]
        else:
            return _status_color_map[file_status]

    def _get_icon(self, ico_name, system_fallback=True):
        file_name = f"{ico_name}.svg"
        theme_location = os.path.join(self.resource_dir, file_name)
        default_location = os.path.join(self.__DEFAULT_PATH__, file_name)
        use_system_theme = TransCodaSettings.use_system_theme() and system_fallback
        if not use_system_theme:
            if os.path.exists(theme_location):
                return QIcon(theme_location)
            elif os.path.exists(default_location):
                return QIcon(default_location)
        #     Always fallback to system theme
        return QIcon.fromTheme(ico_name)

