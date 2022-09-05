from Imageplay.core.Playlist import Playlist


def test__previous_with_shuffle():
    playlist = Playlist(shuffle=True)
    playlist.enqueue([1, 2, 3, 4, 5])
    # No history
    assert playlist.previous() is None
    item1 = playlist.next()
    # Still No history
    assert playlist.previous() is None
    item2 = playlist.next()
    # First queried item is now history
    assert playlist.previous() == item1
    # Playlist has moved back
    playlist.next()
    # So previous will still go back to first item
    assert playlist.previous() == item1
    playlist.next()
    playlist.next()
    assert playlist.previous() == item2


def test__previous_without_shuffle():
    playlist = Playlist(shuffle=False)
    playlist.enqueue([1, 2, 3, 4, 5, 6])
    # No history
    assert playlist.previous() is None
    playlist.next()
    # Still No history
    assert playlist.previous() is None
    playlist.next()
    # First queried item is now history
    assert playlist.previous() == 1
    # Playlist has moved back
    playlist.next()
    # So previous will still go back to first item
    assert playlist.previous() == 1
    assert playlist.next() == 2
    assert playlist.next() == 3
    assert playlist.next() == 4
    assert playlist.next() == 5

    assert playlist.previous() == 4
    assert playlist.previous() == 3
    assert playlist.previous() == 2
    assert playlist.previous() == 1


# noinspection PyBroadException
def test__next_with_shuffle():
    playlist = Playlist(shuffle=True)
    playlist.enqueue([1, 2, 3, 4, 5])
    assert playlist.next() == playlist._playlist[0]
    assert playlist.next() == playlist._playlist[1]
    assert playlist.next() == playlist._playlist[2]
    assert playlist.next() == playlist._playlist[3]
    assert playlist.next() == playlist._playlist[4]
    try:
        playlist.next()
        assert False
    except Exception as inst:
        assert str(inst) == "Playlist Completed"


def test__next_without_shuffle():
    playlist = Playlist(shuffle=False)
    playlist.enqueue([1, 2, 3, 4, 5])
    assert playlist.next() == 1
    assert playlist.next() == 2
    assert playlist.next() == 3
    assert playlist.next() == 4
    assert playlist.next() == 5
    try:
        playlist.next()
        assert False
    except Exception as inst:
        assert str(inst) == "Playlist Completed"


def test__reset():
    playlist = Playlist(shuffle=False)
    playlist.enqueue([1, 2, 3, 4, 5])
    assert playlist.next() == 1
    assert playlist.next() == 2
    assert playlist.items_left() == 3
    playlist.reset()
    assert playlist.items_left() == 5
    assert playlist.next() == 1
    assert playlist.next() == 2


def test__clear():
    playlist = Playlist(shuffle=True)
    playlist.enqueue([1, 2, 3, 4, 5])
    playlist.clear()
    assert playlist.items_left() == 0
    assert playlist.length() == 0


def test__enqueue():
    playlist = Playlist(shuffle=True)
    playlist.enqueue([1, 2, 3, 4, 5])
    assert playlist.items_left() == 5

    playlist.enqueue([5, 4, 7])
    assert playlist.items_left() == 8


def test__items_left():
    playlist = Playlist(shuffle=True)
    playlist.enqueue([1, 2, 3, 4, 5])
    assert playlist.items_left() == 5

    playlist.enqueue([5, 4, 7])
    assert playlist.items_left() == 8

    # Removes first instance
    playlist.remove(5)
    assert playlist.items_left() == 7

    # Remove next instance
    playlist.remove(5)
    assert playlist.items_left() == 6


def test_remove_history():
    playlist = Playlist(shuffle=False)
    playlist.enqueue([1, 2, 3, 4, 5])
    assert playlist.next() == 1
    assert playlist.next() == 2
    assert playlist.next() == 3
    playlist.remove(2)
    assert playlist.previous() == 1
    assert playlist.previous() is None


def test_remove_future():
    playlist = Playlist(shuffle=False)
    playlist.enqueue([1, 2, 3, 4, 5])
    assert playlist.next() == 1
    assert playlist.next() == 2
    assert playlist.next() == 3
    playlist.remove(4)
    assert playlist.next() == 5
    assert playlist.previous() == 3
    assert playlist.next() == 5
    try:
        playlist.next()
        assert False
    except Exception as inst:
        assert str(inst) == "Playlist Completed"


