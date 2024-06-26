import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '../common/'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))

__VERSION__ = "0.0.1"
__NAME__ = "FileWrangler"
__APP_NAME__ = str.format(f"{__NAME__}")

import common.CommonUtils
from common.Theme import Theme

logger = common.CommonUtils.get_logger(__APP_NAME__)
theme = Theme(default_theme_dir=os.path.join(os.path.dirname(__file__), "resources/theme"))
std_separator = " - "
