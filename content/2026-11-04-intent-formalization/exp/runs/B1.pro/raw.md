```python
import pytest

from parse_duration import parse_duration


@pytest.mark.parametrize(
    "text,expected",
    [
        ("1s", 1),
        ("1m", 60),
        ("1h", 3600),
        ("1d", 86400),
        ("1d2h3m4s", 86400 + 2 * 3600 + 3 * 60 + 4),
        ("2m30s", 150),
        ("1d 2h 3m 4s", 86400 + 2 * 3600 + 3 * 60 + 4),
        ("0d0h0m0s", 0),
        ("007s", 7),
        ("999d", 999 * 86400),
    ],
)
def test_valid(text, expected):
    assert parse_duration(text) == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("1D", 86400),
        ("1H", 3600),
        ("1M", 60),
        ("1S", 1),
        ("1d2H3m4S", 86400 + 2 * 3600 + 3 * 60 + 4),
    ],
)
def test_units_case_insensitive(text, expected):
    assert parse_duration(text) == expected


def test_surrounding_whitespace_stripped():
    assert parse_duration("  1h  ") == 3600
    assert parse_duration("\t1h\n") == 3600


def test_internal_spaces_between_tokens_allowed():
    assert parse_duration("1h 2m") == 3720


def test_leading_minus_ignored():
    assert parse_duration("-1h") == 3600
    assert parse_duration("-1d2h") == 86400 + 7200
    assert parse_duration(" -1h") == 3600


@pytest.mark.parametrize("text", ["", "   ", "\t\n"])
def test_empty_raises_value_error(text):
    with pytest.raises(ValueError, match="empty duration"):
        parse_duration(text)


@pytest.mark.parametrize("text", [None, 123, 1.5, b"1h", ["1h"], object()])
def test_non_string_raises_type_error(text):
    with pytest.raises(TypeError, match="text must be str"):
        parse_duration(text)


@pytest.mark.parametrize("text", ["+1h", "+", "+ 1h"])
def test_plus_sign_rejected(text):
    with pytest.raises(ValueError, match="sign not allowed"):
        parse_duration(text)


@pytest.mark.parametrize("text", ["abc", "1x", "h", "-"])
def test_no_valid_tokens(text):
    with pytest.raises(ValueError, match="no valid tokens"):
        parse_duration(text)


@pytest.mark.parametrize(
    "text",
    [
        "1h2",    # trailing number without unit
        "1.5h",   # non-integer number
        "1h-2m",  # stray minus inside
        "abc1h",  # garbage around a valid token
        "1h m",   # lone unit without digits
        "--1h",   # double sign
    ],
)
def test_malformed_raises(text):
    with pytest.raises(ValueError, match="malformed duration"):
        parse_duration(text)


@pytest.mark.parametrize(
    "text",
    [
        "1h2h",
        "1H2h",
        "1h 2H",
        "1d1D",
        "1h2m3h",
    ],
)
def test_repeated_unit_rejected(text):
    with pytest.raises(ValueError, match="repeated unit"):
        parse_duration(text)
```
