from FileWrangler import FileWranglerCore
from FileWrangler.fileops import Separator


def test__SeparatorUC1():
    """
    UC: File "a - b"
    Repeat 2
    Separator " - "
    new Separator "--"
    Returns: a--b
    """
    config = Separator.get_context(file_sep=" - ", repeat=2, new_sep="--")
    key = Separator.get_key("a - b.jpg", config)
    assert key == "a--b"


def test__SeparatorUC2():
    """
    UC: File "a - b"
    Repeat 2
    Separator " - "
    new Separator "--"
    Returns: a--b
    """
    config = Separator.get_context(file_sep=" - ", repeat=1, new_sep="--")
    key = Separator.get_key("a - b.jpg", config)
    assert key == "a"


def test__SeparatorUC3():
    """
    UC: File "a - b"
    Repeat 3
    Separator " - "
    new Separator "--"
    Returns: UNKNOWN_KEY
    """
    config = Separator.get_context(file_sep=" - ", repeat=3, new_sep="--")
    key = Separator.get_key("a - b.jpg", config)
    assert key == FileWranglerCore.UNKNOWN_KEY


def test__SeparatorUC4():
    """
    UC: File "a-b"
    Repeat 1
    Separator " - "
    new Separator "--"
    Returns: a-b
    """
    config = Separator.get_context(file_sep=" - ", repeat=1, new_sep="--")
    key = Separator.get_key("a-b.jpg", config)
    assert key == "a-b"


def test__SeparatorUC5():
    """
    UC: File "a-b"
    Repeat 2
    Separator " - "
    new Separator "--"
    Returns: UNKNOWN_KEY
    """
    config = Separator.get_context(file_sep=" - ", repeat=2, new_sep="--")
    key = Separator.get_key("a-b.jpg", config)
    assert key == FileWranglerCore.UNKNOWN_KEY
