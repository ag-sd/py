import random


class Playlist:
    def __init__(self, shuffle=False, loop=False):
        super().__init__()
        self._items = []
        self._playlist = []
        self._shuffle = shuffle
        self._loop = loop
        self._current_index = -1

    def loop(self, loop):
        self._loop = loop

    def is_looped(self):
        return self._loop

    def shuffle(self, shuffle):
        self._shuffle = shuffle
        self._current_index = -1
        self._playlist = self._items
        if shuffle:
            random.shuffle(self._playlist)

    def is_shuffled(self):
        return self._shuffle

    def enqueue(self, items):
        self._items = self._items + items
        if self._shuffle:
            random.shuffle(items)
        self._playlist = self._playlist + items

    def clear(self):
        self._items.clear()
        # self._history.clear()
        self._current_index = -1
        self._playlist.clear()

    def previous(self):
        # if History is empty, return None
        if self._current_index <= 0:
            return None
        # go back one index
        self._current_index -= 1
        # Return item at index
        return self._playlist[self._current_index]

    def has_previous(self):
        return self._current_index > 0

    def next(self):
        if self._current_index + 1 == len(self._playlist):
            if self._loop:
                self.reset()
            else:
                raise PlaylistCompleteException("Playlist Completed")
        # go up one index
        self._current_index += 1
        # Return item
        return self._playlist[self._current_index]

    def has_next(self):
        return self._current_index + 1 < len(self._playlist) or (self._loop and len(self._playlist) > 0)

    # def has_items(self):
    #     return self._current_index < len(self._playlist)

    def remove(self, item):
        if item in self._playlist:
            item_index = self._playlist.index(item)
            if item_index < self._current_index:
                # If the item has been visited, remove it from the history
                self._current_index -= 1
            self._playlist.remove(item)
        if item in self._items:
            self._items.remove(item)

    def items_left(self):
        return len(self._items) - self._current_index - 1

    def length(self):
        return len(self._items)

    def reset(self):
        self.shuffle(self._shuffle)


class PlaylistCompleteException(Exception):
    """Thrown when the playlist completes and the next image is requested"""
