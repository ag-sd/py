import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '../common/'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))

from common import CommonUtils

__VERSION__ = "0.0.0"
__NAME__ = "MediaLib"
__APP_NAME__ = str.format(f"{__NAME__} {__VERSION__}")

logger = CommonUtils.get_logger(__APP_NAME__)


__DB_PATH__ = os.path.join(os.path.dirname(__file__), "resource/db")
__DB_NAME__ = "media_lib.sqlite"
__DB_TEMPLATE__ = "media_lib_template.sqlite"

db_path = os.path.join(__DB_PATH__, __DB_NAME__)
db_template_path = os.path.join(__DB_PATH__, __DB_TEMPLATE__)
