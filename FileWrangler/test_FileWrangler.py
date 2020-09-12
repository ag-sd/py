from FileWrangler.FileWranglerCore import ConfigKeys, _DEFAULT_REGEX, _create_key, _DEFAULT_SPLITTER, _UNKNOWN_KEY


def test__create_key_simple_regex():
    file = "123 - 345 - 123.jpg"
    config = {
        ConfigKeys.append_date: False,
        ConfigKeys.key_token_string: _DEFAULT_REGEX,
        ConfigKeys.key_token_count: 1,
        ConfigKeys.key_is_regex: True
    }
    key = _create_key(file, config)
    assert key == "123"


def test__create_key_repeating_regex():
    file = "aaa - aaa - 123.jpg"
    config = {
        ConfigKeys.append_date: False,
        ConfigKeys.key_token_string: "(aaa)",
        ConfigKeys.key_token_count: 2,
        ConfigKeys.key_is_regex: True
    }
    key = _create_key(file, config)
    assert key == "aaa - aaa"


def test__create_key_unknown_regex():
    file = "aaa - aaa - 123.jpg"
    config = {
        ConfigKeys.append_date: False,
        ConfigKeys.key_token_string: "(ccc)",
        ConfigKeys.key_token_count: 2,
        ConfigKeys.key_is_regex: True
    }
    key = _create_key(file, config)
    assert key == _UNKNOWN_KEY


def test__create_key_simple_splitter():
    file = "123 - 345 - 123.jpg"
    config = {
        ConfigKeys.append_date: False,
        ConfigKeys.key_token_string: _DEFAULT_SPLITTER,
        ConfigKeys.key_token_count: 1,
        ConfigKeys.key_is_regex: False
    }
    key = _create_key(file, config)
    assert key == "123"


def test__create_key_simple_splitter_unknown():
    file = "123 - 345 - 123.jpg"
    config = {
        ConfigKeys.append_date: False,
        ConfigKeys.key_token_string: "+",
        ConfigKeys.key_token_count: 1,
        ConfigKeys.key_is_regex: False
    }
    key = _create_key(file, config)
    assert key == file


def test__create_key_repeating_splitter():
    file = "123 - 345 - 123.jpg"
    config = {
        ConfigKeys.append_date: False,
        ConfigKeys.key_token_string: _DEFAULT_SPLITTER,
        ConfigKeys.key_token_count: 2,
        ConfigKeys.key_is_regex: False
    }
    key = _create_key(file, config)
    assert key == "123 - 345"
