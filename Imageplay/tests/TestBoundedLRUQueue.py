import unittest

from model.History import BoundedLRUQueue, InfiniteHistoryStack


class TestBoundedLRUQueue(unittest.TestCase):

    def setUp(self):
        self.queue = BoundedLRUQueue(5)

    def testCreateNewOrderedNoLoop(self):
        for i in range(0, 5):
            _next = self.queue.next(False)
            self.assertEqual(i, _next)

    def testCreateNewOrderedLoop(self):
        for i in range(0, 5):
            for j in range(0, 5):
                _next = self.queue.next(False)
                self.assertEqual(j, _next)

    def testCreateNewOrderedPrev(self):
        for i in range(0, 5):
            _next = self.queue.next(False)
            self.assertEqual(i, _next)

        for j in range(4, -1, -1):
            self.assertEqual(j, self.queue.prev())

        for i in range(0, 5):
            _next = self.queue.next(False)
            self.assertEqual(i, _next)

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
