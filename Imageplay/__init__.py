from PyQt5.QtGui import QImageReader

from Settings import SettingsKeys
from common import CommonUtils

__VERSION__ = "0.0.4"
__NAME__ = "ImagePlay"
__APP_NAME__ = str.format(f"{__NAME__} {__VERSION__}")

logger = CommonUtils.get_logger(__APP_NAME__)

settings = CommonUtils.AppSettings(
    __APP_NAME__,
    {
        SettingsKeys.image_delay: 3000,
        SettingsKeys.gif_delay: 1000,
        SettingsKeys.gif_by_frame: False,
        SettingsKeys.recurse_subdirs: False,
        SettingsKeys.shuffle: False,
        SettingsKeys.loop: True,
        SettingsKeys.image_scaled: True,
        SettingsKeys.dupe_image_view_zoom: 5
    }
)

supported_formats = []
for _format in QImageReader.supportedImageFormats():
    supported_formats.append(f".{str(_format, encoding='ascii').upper()}")
