import unittest

from model.History import InfiniteHistoryStack


class TestInfiniteHistoryStack(unittest.TestCase):

    def setUp(self):
        self.playlist = InfiniteHistoryStack(5)

    def testCreateNewOrderedNoLoop(self):
        for i in range(0, 5):
            _next = self.playlist.next(False)
            self.assertEqual(i, _next)

    def testCreateNewOrderedLoop(self):
        for i in range(0, 5):
            for j in range(0, 5):
                _next = self.playlist.next(False)
                self.assertEqual(j, _next)

    def testCreateNewOrderedPrev(self):
        for i in range(0, 5):
            _next = self.playlist.next(False)
            self.assertEqual(i, _next)

        for j in range(4, -1, -1):
            self.assertEqual(j, self.playlist.prev())

        for i in range(0, 5):
            _next = self.playlist.next(False)
            self.assertEqual(i, _next)

    def testCreateNewRandomLoopExits(self):
        for j in range(0, 5):
            for i in range(0, 5):
                _next = self.playlist.next(True)
