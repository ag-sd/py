from FileWrangler.fileops import CompletelyReplace


def test__CompletelyReplaceUC1():
    """
        Use Case: File name is completely replaced
    """
    file = "aabbccdd.jpg"

    context = CompletelyReplace.get_context("TEST")
    key = CompletelyReplace.get_key(file, context)
    assert key == "TEST"
