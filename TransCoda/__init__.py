import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '../common/'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))
import CommonUtils

__VERSION__ = "0.0.3"
__NAME__ = "Trans:Coda"
__APP_NAME__ = str.format(f"{__NAME__}")


logger = CommonUtils.get_logger(__APP_NAME__)
