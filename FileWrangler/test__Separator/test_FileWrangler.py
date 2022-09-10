# def test__create_key_simple_regex():
#     file = "123 - 345 - 123.jpg"
#     config = {
#         ConfigKeys.append_date: False,
#         ConfigKeys.key_token_string: _DEFAULT_REGEX,
#         ConfigKeys.key_token_count: 1,
#         ConfigKeys.key_type: KeyType.regular_expression
#     }
#     key = _create_key(file, config)
#     assert key == "123"


# def test__create_key_repeating_regex():
#     file = "aaa - aaa - 123.jpg"
#     config = {
#         ConfigKeys.append_date: False,
#         ConfigKeys.key_token_string: "(aaa)",
#         ConfigKeys.key_token_count: 2,
#         ConfigKeys.key_type: KeyType.regular_expression
#     }
#     key = _create_key(file, config)
#     assert key == "aaa - aaa"


# def test__create_key_unknown_regex():
#     file = "aaa - aaa - 123.jpg"
#     config = {
#         ConfigKeys.append_date: False,
#         ConfigKeys.key_token_string: "(ccc)",
#         ConfigKeys.key_token_count: 2,
#         ConfigKeys.key_type: KeyType.regular_expression
#     }
#     key = _create_key(file, config)
#     assert key == UNKNOWN_KEY


# def test__create_key_simple_splitter():
#     file = "123 - 345 - 123.jpg"
#     config = {
#         ConfigKeys.append_date: False,
#         ConfigKeys.key_token_string: DEFAULT_SPLITTER,
#         ConfigKeys.key_token_count: 1,
#         ConfigKeys.key_type: KeyType.separator
#     }
#     key = _create_key(file, config)
#     assert key == "123"
#
#
# def test__create_key_simple_splitter_unknown():
#     file = "123 - 345 - 123.jpg"
#     config = {
#         ConfigKeys.append_date: False,
#         ConfigKeys.key_token_string: "+",
#         ConfigKeys.key_token_count: 1,
#         ConfigKeys.key_type: KeyType.separator
#     }
#     key = _create_key(file, config)
#     assert key == file
#
#
# def test__create_key_repeating_splitter():
#     file = "123 - 345 - 123.jpg"
#     config = {
#         ConfigKeys.append_date: False,
#         ConfigKeys.key_token_string: DEFAULT_SPLITTER,
#         ConfigKeys.key_token_count: 2,
#         ConfigKeys.key_type: KeyType.separator
#     }
#     key = _create_key(file, config)
#     assert key == "123 - 345"
#
#
# def test__create_replacement_key():
#     file = "foo1edfd"
#     config = {
#         ConfigKeys.append_date: False,
#         ConfigKeys.key_token_string: "Token",
#         ConfigKeys.key_token_count: 2,
#         ConfigKeys.key_type: KeyType.replacement
#     }
#     key = _create_key(file, config)
#     assert key == "Token"
