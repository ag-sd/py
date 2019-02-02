import unittest
from datetime import datetime
from FileItem import FileItem


class UTFileItem(unittest.TestCase):

    def testCreateNew(self):
        item = FileItem("NAME", "PATH", 123)
        self.assertEqual(item.file_name, "NAME")
        self.assertEqual(item.file_path, "PATH")
        self.assertEqual(item.file_size, 123)
        self.assertEqual(item.file_status, FileItem.FILE_STATUS_INIT)
        self.assertEqual(item.start_time, 0)
        self.assertEqual(item.end_time, 0)
        self.assertEqual(item.encoded_file_name, "")
        self.assertEqual(item.encoded_file_path, "")
        self.assertEqual(item.encoded_file_size, -1)
        self.assertEqual(item.codec, "")

    def testCreateFromDB(self):
        now = datetime.now()
        item = FileItem.from_db("NAME", "PATH", 123, FileItem.FILE_STATUS_INIT, now, now, "ENC-NAME", "ENC-PATH", 12,
                                "CODEC")
        self.assertEqual(item.file_name, "NAME")
        self.assertEqual(item.file_path, "PATH")
        self.assertEqual(item.file_size, 123)
        self.assertEqual(item.file_status, FileItem.FILE_STATUS_INIT)
        self.assertEqual(item.start_time, now)
        self.assertEqual(item.end_time, now)
        self.assertEqual(item.encoded_file_name, "ENC-NAME")
        self.assertEqual(item.encoded_file_path, "ENC-PATH")
        self.assertEqual(item.encoded_file_size, 12)
        self.assertEqual(item.codec, "CODEC")

    def testSetStarted(self):
        item = FileItem("NAME", "PATH", 123)
        self.assertEqual(item.file_name, "NAME")
        self.assertEqual(item.file_path, "PATH")
        self.assertEqual(item.file_size, 123)
        self.assertEqual(item.file_status, FileItem.FILE_STATUS_INIT)
        self.assertEqual(item.start_time, 0)
        self.assertEqual(item.end_time, 0)
        self.assertEqual(item.encoded_file_name, "")
        self.assertEqual(item.encoded_file_path, "")
        self.assertEqual(item.encoded_file_size, -1)
        self.assertEqual(item.codec, "")

        item.set_started("OP-FP", "OP-FN", "OP-CODEC")
        self.assertEqual(item.file_name, "NAME")
        self.assertEqual(item.file_path, "PATH")
        self.assertEqual(item.file_size, 123)
        self.assertEqual(item.file_status, FileItem.FILE_STATUS_STARTED)
        self.assertTrue(item.start_time.second > 0)
        self.assertEqual(item.end_time, 0)
        self.assertEqual(item.encoded_file_name, "OP-FN")
        self.assertEqual(item.encoded_file_path, "OP-FP")
        self.assertEqual(item.encoded_file_size, -1)
        self.assertEqual(item.codec, "OP-CODEC")

    def testSetComplete(self):
        item = FileItem("NAME", "PATH", 123)
        self.assertEqual(item.file_name, "NAME")
        self.assertEqual(item.file_path, "PATH")
        self.assertEqual(item.file_size, 123)
        self.assertEqual(item.file_status, FileItem.FILE_STATUS_INIT)
        self.assertEqual(item.start_time, 0)
        self.assertEqual(item.end_time, 0)
        self.assertEqual(item.encoded_file_name, "")
        self.assertEqual(item.encoded_file_path, "")
        self.assertEqual(item.encoded_file_size, -1)
        self.assertEqual(item.codec, "")

        item.set_complete()
        self.assertEqual(item.file_name, "NAME")
        self.assertEqual(item.file_path, "PATH")
        self.assertEqual(item.file_size, 123)
        self.assertEqual(item.file_status, FileItem.FILE_STATUS_COMPLETE)
        self.assertEqual(item.start_time, 0)
        self.assertTrue(item.end_time.second > 0)
        self.assertEqual(item.encoded_file_name, "")
        self.assertEqual(item.encoded_file_path, "")
        self.assertEqual(item.encoded_file_size, -1)
        self.assertEqual(item.codec, "")
