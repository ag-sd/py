import CommonUtils

__VERSION__ = "0.0.3"
__NAME__ = "ImagePlay"
__APP_NAME__ = str.format(f"{__NAME__} {__VERSION__}")

logger = CommonUtils.get_logger(__APP_NAME__)

settings = CommonUtils.AppSettings(
    __APP_NAME__,
    {
        "image_delay": 3000,
        "gif_delay": 1000,
        "recurse_subdirs": False,
        "shuffle": False,
        "loop": True,
    }
)
