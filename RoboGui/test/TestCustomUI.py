import unittest
import CustomUI
from PyQt5.QtWidgets import (QLineEdit, QLabel, QApplication)


class TestCustomUI(unittest.TestCase):

    def setUp(self):
        self.app = QApplication([])
        self.testWidget = CustomUI.FileChooser("Test Label", "Test Cue", True)

    def tearDown(self):
        self.app.quit()

    def testFileChooserDefaults(self):
        self.assertEqual(self.testWidget.getSelection(), "")
        self.assertEqual(self.testWidget.label, "Test Label")
        self.assertEqual(self.testWidget.cue, "Test Cue")
        self.assertEqual(self.testWidget.dir, True)
        self.assertEqual(self.testWidget.findChild(QLineEdit, "txtAddress").text(), "")
        self.assertEqual(self.testWidget.findChild(QLabel).text(), "Test Label")

    def testFileChooserSelectionChanged(self):
        """
            Test logic to simulate QFileDialog choice and assert selection
        :return:
        """
        pass


