import unittest

from PlayList import CircularLRUQueue


class TestCircularLRUQueue(unittest.TestCase):

    def setUp(self):
        self.queue = CircularLRUQueue(5)

    def testCreateNewOrderedNoLoop(self):
        for i in range(0, 5):
            _next = self.queue.next(False)
            self.assertEqual(i, _next)

    def testCreateNewOrderedLoop(self):
        for i in range(0, 5):
            for j in range(0, 5):
                _next = self.queue.next(False)
                self.assertEqual(j, _next)

    def testCreateNewRandomNoLoop(self):
        prev = []
        for i in range(0, 5):
            _next = self.queue.next(True)
            self.assertTrue(not prev.__contains__(_next))
            prev.append(_next)

    def testCreateNewRandomLoop(self):
        for j in range(0, 5):
            prev = []
            self.queue.reset()
            for i in range(0, 5):
                _next = self.queue.next(True)
                self.assertTrue(not prev.__contains__(_next))
                prev.append(_next)
