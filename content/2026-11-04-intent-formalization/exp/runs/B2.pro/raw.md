```python
import pytest

from parse_duration import parse_duration


class TestValid:
    def test_seconds(self):
        assert parse_duration("1s") == 1

    def test_minutes(self):
        assert parse_duration("1m") == 60

    def test_hours(self):
        assert parse_duration("1h") == 3600

    def test_days(self):
        assert parse_duration("1d") == 86400

    def test_combined_units(self):
        assert parse_duration("1d2h3m4s") == 86400 + 7200 + 180 + 4

    def test_repeated_same_unit(self):
        assert parse_duration("1m30s") == 90

    def test_multi_digit_numbers(self):
        assert parse_duration("13h") == 13 * 3600

    def test_spaces_between_tokens(self):
        assert parse_duration("1d 2h 3m") == 86400 + 7200 + 180

    def test_space_inside_token(self):
        assert parse_duration("1 h") == 3600

    def test_case_insensitive(self):
        assert parse_duration("1D2H3M4S") == parse_duration("1d2h3m4s")

    def test_mixed_case(self):
        assert parse_duration("1D2h") == 86400 + 7200

    def test_zero(self):
        assert parse_duration("0s") == 0

    def test_zero_with_other_tokens(self):
        assert parse_duration("0d5m") == 300

    def test_leading_zero(self):
        assert parse_duration("01h") == 3600

    def test_large_number(self):
        assert parse_duration("1000000s") == 1000000

    def test_strips_whitespace(self):
        assert parse_duration("  1h30m \n") == 5400


class TestTypeError:
    def test_none(self):
        with pytest.raises(TypeError):
            parse_duration(None)

    def test_int(self):
        with pytest.raises(TypeError):
            parse_duration(3600)

    def test_bytes(self):
        with pytest.raises(TypeError):
            parse_duration(b"1h")

    def test_list(self):
        with pytest.raises(TypeError):
            parse_duration(["1h"])


class TestValueError:
    def test_empty_string(self):
        with pytest.raises(ValueError):
            parse_duration("")

    def test_whitespace_only(self):
        with pytest.raises(ValueError):
            parse_duration(" \t\n ")

    def test_negative_sign(self):
        with pytest.raises(ValueError):
            parse_duration("-1h")

    def test_positive_sign(self):
        with pytest.raises(ValueError):
            parse_duration("+1h")

    def test_sign_after_leading_space(self):
        with pytest.raises(ValueError):
            parse_duration(" -1h")

    def test_sign_only_between_tokens(self):
        with pytest.raises(ValueError):
            parse_duration("1h-30m")

    def test_plain_letters(self):
        with pytest.raises(ValueError):
            parse_duration("h")

    def test_plain_digits(self):
        with pytest.raises(ValueError):
            parse_duration("123")

    def test_unit_first(self):
        with pytest.raises(ValueError):
            parse_duration("h1")

    def test_unknown_unit(self):
        with pytest.raises(ValueError):
            parse_duration("1x")

    def test_trailing_digits(self):
        with pytest.raises(ValueError):
            parse_duration("1h2")

    def test_extra_junk_after_valid(self):
        with pytest.raises(ValueError):
            parse_duration("1h foo")

    def test_extra_junk_before_valid(self):
        with pytest.raises(ValueError):
            parse_duration("foo1h")

    def test_junk_between_tokens(self):
        with pytest.raises(ValueError):
            parse_duration("1h-30m")

    def test_decimal_number(self):
        with pytest.raises(ValueError):
            parse_duration("1.5h")
```
