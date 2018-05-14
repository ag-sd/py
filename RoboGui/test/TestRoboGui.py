import unittest
import RoboGui
import CustomUI
from PyQt5.QtWidgets import (QApplication, QCheckBox, QLineEdit)


class TestRoboGui(unittest.TestCase):

    def setUp(self):
        self.app = QApplication([])
        self.testWidget = RoboGui.RoboGUI()

    def tearDown(self):
        self.app.quit()

    def testAllChecksSelected(self):
        src = self.testWidget.findChild(CustomUI.FileChooser, name="Source Directory")
        src.selection = "FOOO"
        tgt = self.testWidget.findChild(CustomUI.FileChooser, name="Target Directory")
        tgt.selection = "BARR"
        children = self.testWidget.findChildren(QCheckBox)
        for checkBox in children:
            checkBox.setChecked(True)

        params = self.testWidget.get_parameters(self.testWidget)

        self.assertEqual(params,
                         'robocopy  FOOO BARR /XO /XC /XN /XL /XX /L /NP /FP /NS /NFL /NDL /TEE /L /MOV /sl /Z /B /J '
                         '/ZB /FAT /CREATE /DST /PURGE /MIR /S /E /NOCOPY /A /M /256')

    def testAllLineEditsSelected(self):
        src = self.testWidget.findChild(CustomUI.FileChooser, name="Source Directory")
        src.selection = "FOOO"
        tgt = self.testWidget.findChild(CustomUI.FileChooser, name="Target Directory")
        tgt.selection = "BARR"
        children = self.testWidget.findChildren(QLineEdit)
        i = 0
        for lineEdit in children:
            lineEdit.setText(str("Test %d" % i))
            i += 1

        params = self.testWidget.get_parameters(self.testWidget)
        # 0 for the source
        # 1 for the target
        # 3,4,5,6 for the log dirs
        # everything else gets a number below
        self.assertEqual(params,
                         'robocopy  FOOO BARR /MT:Test 2 /R:Test 7 /W:Test 8 /LEV:Test 9 '
                         '/MAXAGE:Test 10 /MINAGE:Test 11')