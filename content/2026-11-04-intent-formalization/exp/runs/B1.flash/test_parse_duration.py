import pytest

from parse_duration import parse_duration


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("1s", 1),
        ("1m", 60),
        ("1h", 3600),
        ("1d", 86400),
        ("10m", 600),
        ("100h", 360000),
        ("0s", 0),
        ("01h", 3600),
        ("0002m", 120),
    ],
)
def test_single_units(text, expected):
    assert parse_duration(text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("1h30m", 5400),
        ("5m30s", 330),
        ("1h1m1s", 3661),
        ("2m1h", 3720),
        ("30s1m", 90),
        ("1s1m1h1d", 90061),
        ("1d2h3m4s", 93784),
        ("2d3h4m5s", 183845),
        ("2d12h", 216000),
        ("0d0h0m0s", 0),
    ],
)
def test_combined_units(text, expected):
    assert parse_duration(text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("1D", 86400),
        ("2H", 7200),
        ("3M", 180),
        ("4S", 4),
        ("1D2H3M4S", 93784),
        ("1d1H1m1S", 90061),
    ],
)
def test_units_are_case_insensitive(text, expected):
    assert parse_duration(text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (" 1h ", 3600),
        ("\t1h 30m\n", 5400),
        ("1 h 30 m", 5400),
        ("  1d  2h  ", 93600),
    ],
)
def test_whitespace_is_allowed(text, expected):
    assert parse_duration(text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("-1h", 3600),
        (" -1h ", 3600),
        ("-1d2h", 93600),
        ("-0s", 0),
    ],
)
def test_leading_minus_is_ignored(text, expected):
    assert parse_duration(text) == expected


@pytest.mark.parametrize(
    "text",
    [
        "",
        " ",
        "   ",
        "\t",
        "\n",
        " \t\r\n ",
    ],
)
def test_empty_or_whitespace_only_input_raises(text):
    with pytest.raises(ValueError, match="empty duration"):
        parse_duration(text)


@pytest.mark.parametrize(
    "text",
    [
        "abc",
        "h",
        "10",
        "1w",
        "dhms",
        "-",
    ],
)
def test_input_without_valid_tokens_raises(text):
    with pytest.raises(ValueError, match="no valid tokens"):
        parse_duration(text)


@pytest.mark.parametrize(
    "text",
    [
        "+1h",
        " +1h",
        "-+1h",
        "+",
        "+\t1h",
    ],
)
def test_plus_sign_is_rejected(text):
    with pytest.raises(ValueError, match="sign not allowed"):
        parse_duration(text)


@pytest.mark.parametrize(
    "text",
    [
        "1h2",
        "1h!",
        "1h 2",
        "1h-2m",
        "1x2s",
        "1w2s",
        "--1h",
        "1h+2m",
        "1h2m3",
        "1h 2m 3",
    ],
)
def test_malformed_durations_raise(text):
    with pytest.raises(ValueError, match="malformed duration"):
        parse_duration(text)


@pytest.mark.parametrize(
    "text",
    [
        "1h2h",
        "1H2h",
        "1D2d",
        "1d2h3d",
        "1m2m",
        "1s 2s",
    ],
)
def test_repeated_units_raise(text):
    with pytest.raises(ValueError, match="repeated unit"):
        parse_duration(text)


@pytest.mark.parametrize(
    "value",
    [
        None,
        1,
        1.0,
        True,
        b"1h",
        ["1h"],
        {"duration": "1h"},
        object(),
    ],
)
def test_non_string_input_raises_type_error(value):
    with pytest.raises(TypeError, match="text must be str"):
        parse_duration(value)


def test_return_value_is_int():
    result = parse_duration("2h30m")
    assert result == 9000
    assert type(result) is int
