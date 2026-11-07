```python
import pytest

from parse_duration import parse_duration


class TestTypeErrors:
    @pytest.mark.parametrize(
        "value",
        [None, 42, 3.14, b"1h", [], {}, object()],
        ids=["none", "int", "float", "bytes", "list", "dict", "object"],
    )
    def test_non_string_raises_type_error(self, value):
        with pytest.raises(TypeError, match="text must be str"):
            parse_duration(value)

    def test_str_subclass_is_accepted(self):
        class MyStr(str):
            pass

        assert parse_duration(MyStr("1h")) == 3600


class TestEmptyInput:
    @pytest.mark.parametrize(
        "text",
        ["", " ", "   ", "\t", "\n", "\t \n"],
        ids=["empty", "one-space", "spaces", "tab", "newline", "whitespace-mix"],
    )
    def test_empty_or_whitespace_raises_value_error(self, text):
        with pytest.raises(ValueError, match="empty duration"):
            parse_duration(text)


class TestSignValidation:
    @pytest.mark.parametrize(
        "text",
        ["-1d", "+1d", " -1d", "\t+1h", "- 1d", "+ 1h"],
        ids=["leading-minus", "leading-plus", "space-minus", "tab-plus", "minus-space", "plus-space"],
    )
    def test_leading_sign_raises_value_error(self, text):
        with pytest.raises(ValueError, match="sign not allowed"):
            parse_duration(text)


class TestNoValidTokens:
    @pytest.mark.parametrize(
        "text",
        ["abc", "12", "d", "1w", "1hour", "one hour", "--", "+", "1.5h"],
        ids=["letters", "number-only", "unit-only", "unknown-unit", "word-with-digit", "words", "punct", "plus-only", "decimal"],
    )
    def test_no_valid_tokens_raises_value_error(self, text):
        with pytest.raises(ValueError, match="no valid tokens"):
            parse_duration(text)


class TestMalformedDuration:
    @pytest.mark.parametrize(
        "text",
        [
            "1h30",
            "1h2mx",
            "1h\t2m",
            "1h\n2m",
            "1 h garbage",
            "1d-2h",
            "1d 2h 3m 4s extra",
            "1h2m3",
            "x1h",
            "1h.",
        ],
        ids=[
            "trailing-number",
            "trailing-letter",
            "internal-tab",
            "internal-newline",
            "trailing-garbage",
            "internal-minus",
            "extra-word",
            "mixed-invalid",
            "prefix-letter",
            "trailing-dot",
        ],
    )
    def test_partial_match_with_extra_chars_raises_value_error(self, text):
        with pytest.raises(ValueError, match="malformed duration"):
            parse_duration(text)


class TestRepeatedUnits:
    @pytest.mark.parametrize(
        "text",
        ["1d2d", "1d 2D", "1s1h1s", "1h 30m 1H", "0m0m"],
        ids=["same-unit", "case-insensitive", "non-adjacent", "spaced-case", "zero-repeat"],
    )
    def test_repeated_unit_raises_value_error(self, text):
        with pytest.raises(ValueError, match="repeated unit"):
            parse_duration(text)


class TestValidDurations:
    @pytest.mark.parametrize(
        "text, expected",
        [
            ("0s", 0),
            ("1s", 1),
            ("1m", 60),
            ("1h", 3600),
            ("1d", 86400),
            ("60s", 60),
            ("90m", 5400),
            ("23h", 82800),
            ("7d", 604800),
            ("1000000s", 1000000),
        ],
        ids=["zero-s", "one-s", "one-m", "one-h", "one-d", "sixty-s", "ninety-m", "twenty-three-h", "seven-d", "large-s"],
    )
    def test_single_unit(self, text, expected):
        assert parse_duration(text) == expected

    @pytest.mark.parametrize(
        "text, expected",
        [
            ("1d1h", 90000),
            ("1d1h1m1s", 90061),
            ("1d2h3m4s", 93784),
            ("2d10h30m15s", 210615),
            ("1h30m", 5400),
            ("5m30s", 330),
            ("10d10h10m10s", 900610),
        ],
        ids=["d-h", "all-units", "mixed-1", "mixed-2", "h-m", "m-s", "all-large"],
    )
    def test_multiple_units(self, text, expected):
        assert parse_duration(text) == expected

    def test_order_does_not_matter(self):
        assert parse_duration("1s1h") == parse_duration("1h1s") == 3601

    @pytest.mark.parametrize(
        "text, expected",
        [
            ("1D", 86400),
            ("1D2H3M4S", 93784),
            ("1d2H3m4S", 93784),
            ("1D 2h 3M 4s", 93784),
        ],
        ids=["uppercase-single", "uppercase-all", "mixed-case", "mixed-case-spaced"],
    )
    def test_case_insensitive_units(self, text, expected):
        assert parse_duration(text) == expected

    @pytest.mark.parametrize(
        "text, expected",
        [
            (" 1h ", 3600),
            ("\t1h\n", 3600),
            ("1h 30m", 5400),
            ("  1d  2h  ", 93600),
            ("1 h 30 m", 5400),
        ],
        ids=["space-around", "tab-newline-around", "space-between", "multi-spaces", "space-number-unit"],
    )
    def test_spacing(self, text, expected):
        assert parse_duration(text) == expected

    def test_leading_zeros(self):
        assert parse_duration("01d002h003m004s") == 93784

    def test_returns_int(self):
        assert isinstance(parse_duration("1h"), int)
```
