from common import CommonUtils
from TransCoda.ui.Theme import Theme

__VERSION__ = "0.1.0"
__NAME__ = "Trans:Coda"
__APP_NAME__ = str.format(f"{__NAME__}")


logger = CommonUtils.get_logger(__APP_NAME__)

theme = Theme("")
