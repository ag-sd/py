from PyQt5.QtGui import QImageReader

from common import CommonUtils

__VERSION__ = "0.0.3"
__NAME__ = "ImagePlay"
__APP_NAME__ = str.format(f"{__NAME__} {__VERSION__}")

logger = CommonUtils.get_logger(__APP_NAME__)

settings = CommonUtils.AppSettings(
    __APP_NAME__,
    {
        "image_delay": 3000,
        "gif_delay": 1000,
        "gif_by_frame": False,
        "recurse_subdirs": False,
        "shuffle": False,
        "loop": True,
    }
)

supported_formats = []
for _format in QImageReader.supportedImageFormats():
    supported_formats.append(f".{str(_format, encoding='ascii').upper()}")
