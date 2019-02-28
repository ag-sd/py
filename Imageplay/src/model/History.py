import random
from collections import deque




class InfiniteHistoryStack:
    def __init__(self, size):
        self.size = size
        self.stack = []
        self.tail = 0

    def prev(self):
        print(self.stack, self.tail)
        if self.tail > 0:
            self.tail -= 1
        if len(self.stack) > 0:
            return self.stack.pop()
        else:
            return 0

    def next(self, is_random):
        if is_random:
            rand = random.randint(0, self.size - 1)
            for i in range(0, self.size):
                # Best effort to not repeat
                if not self.stack[self.tail:].__contains__(rand):
                    return self.enqueue(rand)
                else:
                    rand = random.randint(0, self.size - 1)
            return self.enqueue(rand)
        else:
            if len(self.stack) == 0:
                return self.enqueue(0)
            else:
                return self.enqueue((self.stack[-1] + 1) % self.size)

    def resize(self, new_size):
        # if new size > current size set max size
        if new_size > self.size:
            self.size = new_size
        # if new size < current size remove all numbers > new size
        elif new_size < self.size:
            for i in range(new_size, self.size):
                if self.stack.__contains__(i):
                    self.stack.remove(i)
                    if self.tail > 0:
                        self.tail -= 1

    def reset(self):
        self.stack.clear()
        self.tail = 0

    def enqueue(self, item):
        print(self.stack, self.tail)
        self.stack.append(item)
        if len(self.stack) >= self.size:
            self.tail += 1
        return item


class BoundedLRUQueue:
    def __init__(self, size):
        self.size = size
        self.queue = deque([], size)

    def enqueue(self, item):
        self.queue.append(item)
        print(self.queue)
        return item

    def prev(self):
        print(self.queue)
        if len(self.queue) > 0:
            return self.queue.pop()
        return 0

    def next(self, is_random):
        if not is_random:
            if len(self.queue) == 0:
                return self.enqueue(0)
            else:
                next_ = self.queue[-1] + 1
                if next_ == self.queue.maxlen:
                    return self.enqueue(0)
                else:
                    return self.enqueue(next_)
        else:
            # Find a random number between 0 and size not present in the queue
            rand = random.randint(0, self.queue.maxlen - 1)
            while self.queue.__contains__(rand):
                rand = random.randint(0, self.queue.maxlen - 1)
            return self.enqueue(rand)

    def resize(self, new_size):
        # if new size > current size set max size
        if new_size > self.queue.maxlen:
            self.queue = deque(self.queue, new_size)
        # if new size < current size remove all numbers > new size
        elif new_size < self.queue.maxlen:
            for i in range(new_size, self.queue.maxlen):
                if self.queue.__contains__(i):
                    self.queue.remove(i)
        self.reset()

    def reset(self):
        self.queue.clear()


class InfiniteHistoryVariableStack(InfiniteHistoryStack):
    def __init__(self, size):
        super().__init__(size)
