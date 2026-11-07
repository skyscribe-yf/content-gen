import pytest

from parse_duration import parse_duration


def test_non_string_raises_type_error():
    for bad in (None, 42, 1.5, b"1h"):
        with pytest.raises(TypeError):
            parse_duration(bad)


def test_empty_input_raises():
    for text in ("", "   ", "\t\n"):
        with pytest.raises(ValueError, match="empty duration"):
            parse_duration(text)


def test_sign_raises():
    for text in ("-1h", "+1h", "- 1h", "+1h30m"):
        with pytest.raises(ValueError, match="sign not allowed"):
            parse_duration(text)


def test_single_unit_conversions():
    assert parse_duration("1d") == 86400
    assert parse_duration("1h") == 3600
    assert parse_duration("1m") == 60
    assert parse_duration("1s") == 1


def test_multiple_units_sum():
    assert parse_duration("1d2h3m4s") == 86400 + 2 * 3600 + 3 * 60 + 4


def test_uppercase_units():
    assert parse_duration("1D") == 86400
    assert parse_duration("1D2H3M4S") == 86400 + 2 * 3600 + 3 * 60 + 4


def test_mixed_case_units():
    assert parse_duration("1d2H3m4S") == 86400 + 2 * 3600 + 3 * 60 + 4


def test_whitespace_tolerated():
    assert parse_duration("1d 2h 3m 4s") == 86400 + 2 * 3600 + 3 * 60 + 4
    assert parse_duration("  1h  ") == 3600
    assert parse_duration("\t1h\n") == 3600


def test_no_valid_tokens_raises():
    for text in ("abc", "12", "1x", "h", "1 h"):
        with pytest.raises(ValueError, match="no valid tokens"):
            parse_duration(text)


def test_malformed_raises():
    for text in ("1h30", "1.5h", "1h-30m", "abc1h", "5m1x", "1h 30"):
        with pytest.raises(ValueError, match="malformed duration"):
            parse_duration(text)


def test_repeated_unit_raises():
    for text in ("1h2h", "1H2h", "1d 1D"):
        with pytest.raises(ValueError, match="repeated unit"):
            parse_duration(text)
