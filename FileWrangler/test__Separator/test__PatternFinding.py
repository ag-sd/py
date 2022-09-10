from FileWrangler.fileops import PatternFinding


def test__UC1():
    """
    UC: File "oh/this/is/A very Long/File-name.jpg"
    components 2
    src_template "{0}/{del}/{del}-{1}"
    Change Mode = Template
    dir_exclude = False
    ext_exclude = False
    tgt_template "{1}<->{0}
    Returns: name.jpg<->oh/this/is // Because ext_exclude=False and the algorithm is greedy
    """
    config = PatternFinding.create_context(src_template="{0}/{del}/{del}-{1}",
                                           change_mode=PatternFinding.ChangeStrategy.use_template,
                                           dir_exclude=False, ext_exclude=False,
                                           tgt_template="{1}<->{0}",
                                           splitter="--")
    key = PatternFinding.get_key("oh/this/is/A very Long/File-name.jpg", config)
    assert key == "name.jpg<->oh/this/is"


def test__UC2():
    """
    UC: File "oh/this/is/A very Long/File-name.jpg"
    components 2
    src_template "{0}/{del}/{del}-{1}"
    Change Mode = Template
    dir_exclude = False
    ext_exclude = True
    tgt_template "{1}<->{0}
    Returns: name<->oh/this/is // Because ext_exclude=True and the algorithm is greedy
    """
    config = PatternFinding.create_context(src_template="{0}/{del}/{del}-{1}",
                                           change_mode=PatternFinding.ChangeStrategy.use_template,
                                           dir_exclude=False, ext_exclude=True,
                                           tgt_template="{1}<->{0}",
                                           splitter="--")
    key = PatternFinding.get_key("oh/this/is/A very Long/File-name.jpg", config)
    assert key == "name<->oh/this/is"


def test__UC3():
    """
    UC: File "oh/this/is/A very Long/File-name.jpg"
    components 2
    src_template "{0}-{del}"
    Change Mode = Template
    dir_exclude = True
    ext_exclude = True
    tgt_template "{0}
    Returns: name<->oh/this/is // Because ext_exclude=True and the algorithm is greedy
    """
    config = PatternFinding.create_context(src_template="{0}-{del}",
                                           change_mode=PatternFinding.ChangeStrategy.use_template,
                                           dir_exclude=True, ext_exclude=True,
                                           tgt_template="{0}",
                                           splitter="--")
    key = PatternFinding.get_key("oh/this/is/A very Long/File-name.jpg", config)
    assert key == "File"


def test__UC4():
    """
    UC: File "oh/this/is/A very Long/File-name.jpg"
    components 2
    src_template "{0}-{del}"
    Change Mode = Template
    dir_exclude = True
    ext_exclude = True
    tgt_template "{0}{1}
    Returns: ERROR as {1} wasnt filled
    """
    config = PatternFinding.create_context(src_template="{0}-{del}",
                                           change_mode=PatternFinding.ChangeStrategy.use_template,
                                           dir_exclude=True, ext_exclude=True,
                                           tgt_template="{0}{1}",
                                           splitter="--")
    try:
        PatternFinding.get_key("oh/this/is/A very Long/File-name.jpg", config)
        assert False, "This is expected to fail as {1} wastn filled"
    except ValueError:
        assert True


def test__UC5():
    """
    UC: File "oh/this/is/A very Long/File-name.jpg"
    components 2
    src_template "{0}/-{del}"
    Change Mode = Template
    dir_exclude = True
    ext_exclude = True
    tgt_template "{0}{1}
    Returns: ERROR as {1} wasnt filled
    """
    config = PatternFinding.create_context(src_template="{0}/-{del}",
                                           change_mode=PatternFinding.ChangeStrategy.use_template,
                                           dir_exclude=True, ext_exclude=True,
                                           tgt_template="{0}{1}",
                                           splitter="--")
    try:
        PatternFinding.get_key("oh/this/is/A very Long/File-name.jpg", config)
        assert False, "This is expected to fail as {1} wastn filled"
    except KeyError:
        assert True
        

def test__UC6():
    """
    UC: File "oh/this/is/A very Long/File-name.jpg"
    components 2
    src_template "{0}-{del}"
    Change Mode = Splitter
    dir_exclude = True
    ext_exclude = True
    splitter =  "--"
    Returns: File
    """
    config = PatternFinding.create_context(src_template="{0}-{del}",
                                           change_mode=PatternFinding.ChangeStrategy.use_splitter,
                                           dir_exclude=True, ext_exclude=True,
                                           tgt_template="{0}{1}",
                                           splitter="--")

    key = PatternFinding.get_key("oh/this/is/A very Long/File-name.jpg", config)
    assert key == "File"


def test__UC7():
    """
    UC: File "oh/this/is/A very Long/File-name-tool.jpg"
    components 2
    src_template "{1}-{del}-{0}"
    Change Mode = Splitter
    dir_exclude = True
    ext_exclude = True
    splitter =  "--"
    Returns: tool--File
    """
    config = PatternFinding.create_context(src_template="{1}-{del}-{0}",
                                           change_mode=PatternFinding.ChangeStrategy.use_splitter,
                                           dir_exclude=True, ext_exclude=True,
                                           tgt_template="{0}{1}",
                                           splitter="--")

    key = PatternFinding.get_key("oh/this/is/A very Long/File-name-tool.jpg", config)
    assert key == "tool--File"