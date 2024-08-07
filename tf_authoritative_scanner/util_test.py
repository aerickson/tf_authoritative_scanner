import tf_authoritative_scanner.util as util


def test_remove_leading_trailing_newline():
    assert util.remove_leading_trailing_newline("") == ""
    assert util.remove_leading_trailing_newline("a") == "a"
    assert util.remove_leading_trailing_newline("a\n") == "a"
    assert util.remove_leading_trailing_newline("\na") == "a"
    assert util.remove_leading_trailing_newline("a\nb") == "a\nb"
