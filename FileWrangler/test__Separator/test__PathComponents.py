from FileWrangler import FileWranglerCore
from FileWrangler.fileops import PathComponents


def test__UC1():
    """
    UC: File "a/b/c/d/1 - 2.jpg"
    components 2
    Separator " - "
    reversed False
    Returns: c - d
    """
    config = PathComponents.get_context(separator=" - ", component_count=2, reverse=False)
    key = PathComponents.get_key("a/b/c/d/1 - 2.jpg", config)
    assert key == "c - d"


def test__UC2():
    """
    UC: File "a/b/c/d/1 - 2.jpg"
    components 4
    Separator " - "
    reversed False
    Returns: a - b - c - d
    """
    config = PathComponents.get_context(separator=" - ", component_count=4, reverse=False)
    key = PathComponents.get_key("1/a/b/c/d/1 - 2.jpg", config)
    assert key == "a - b - c - d"


def test__UC3():
    """
    UC: File "a/b/c/d/1 - 2.jpg"
    components 5
    Separator " - "
    reversed False
    Returns: UNKNOWN KEY
    """
    config = PathComponents.get_context(separator=" - ", component_count=5, reverse=False)
    key = PathComponents.get_key("a/b/c/d/1 - 2.jpg", config)
    assert key == FileWranglerCore.UNKNOWN_KEY


def test__UC4():
    """
    UC: File "a/b/c/d/1 - 2.jpg"
    components 2
    Separator " - "
    reversed True
    Returns: d - c
    """
    config = PathComponents.get_context(separator=" - ", component_count=2, reverse=True)
    key = PathComponents.get_key("a/b/c/d/1 - 2.jpg", config)
    assert key == "d - c"
