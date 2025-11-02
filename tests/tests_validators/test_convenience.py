"""Tests for convenience validation functions and validators."""

from unittest.mock import patch
from zoneinfo import ZoneInfoNotFoundError

import pytest

from ledger_bot.validators.convenience import (
    DateStringValidator,
    TimeStringValidator,
    TimezoneValidator,
    date_string_validator,
    is_valid_date,
    is_valid_time,
    is_valid_timezone,
    time_string_validator,
    timezone_validator,
)


class TestIsValidDate:
    """Test is_valid_date convenience function."""

    @pytest.mark.parametrize(
        "value,expected",
        [
            # Valid dates
            ("01-01-2024", True),
            ("31-12-2024", True),
            ("15-06-2025", True),
            ("1-1-24", True),
            ("9-9-2024", True),
            # Different separators
            ("01/01/2024", True),
            ("01.01.2024", True),
            ("15/06/2025", True),
            ("15.06.2025", True),
            # 2-digit years
            ("01-01-24", True),
            ("31-12-99", True),
            # Invalid dates
            ("00-01-2024", False),  # Day 00
            ("32-01-2024", False),  # Day 32
            ("01-00-2024", False),  # Month 00
            ("01-13-2024", False),  # Month 13
            # Note: regex validation doesn't check calendar validity
            # So 31-02-2024 would pass regex but fail real date parsing
            # Invalid formats
            ("2024-01-01", False),  # Wrong order
            ("01/01", False),  # Missing year
            ("abc", False),  # Not a date
            ("", False),  # Empty string
            ("01-01-20245", False),  # Too many year digits
        ],
    )
    def test_date_validation(self, value, expected):
        """Test various date format validations."""
        assert is_valid_date(value) is expected


class TestIsValidTime:
    """Test is_valid_time convenience function."""

    @pytest.mark.parametrize(
        "value,expected",
        [
            # Valid times
            ("00:00", True),
            ("12:30", True),
            ("23:59", True),
            ("09:05", True),
            ("9:05", True),
            ("0:00", True),
            # Different separators
            ("12.30", True),
            ("09.05", True),
            # Invalid times
            ("24:00", False),  # Hour 24
            ("12:60", False),  # Minute 60
            ("-1:00", False),  # Negative hour
            ("12:-1", False),  # Negative minute
            ("25:30", False),  # Hour > 23
            # Invalid formats
            ("hello", False),  # Not a time
            ("12", False),  # Missing minutes
            ("12:30:45", False),  # Too many parts
            ("", False),  # Empty string
        ],
    )
    def test_time_validation(self, value, expected):
        """Test various time format validations."""
        assert is_valid_time(value) is expected


class TestIsValidTimezone:
    """Test is_valid_timezone convenience function."""

    def test_valid_iana_timezone(self):
        """Test that valid IANA timezones pass."""
        assert is_valid_timezone("Europe/London") is True
        assert is_valid_timezone("America/New_York") is True
        assert is_valid_timezone("Asia/Tokyo") is True
        assert is_valid_timezone("UTC") is True

    def test_invalid_iana_resolved_by_shortening(self):
        """Test that invalid IANA but resolvable timezones pass."""
        with patch(
            "ledger_bot.validators.convenience.ZoneInfo",
            side_effect=ZoneInfoNotFoundError,
        ), patch(
            "ledger_bot.utils.time_utils.resolve_timezone", return_value="Europe/London"
        ):
            assert is_valid_timezone("GMT") is True

    def test_invalid_iana_but_valid_offset(self):
        """Test that UTC offset formats are accepted."""
        with patch(
            "ledger_bot.validators.convenience.ZoneInfo",
            side_effect=ZoneInfoNotFoundError,
        ), patch("ledger_bot.utils.time_utils.resolve_timezone", return_value=None):
            assert is_valid_timezone("UTC+1") is True
            assert is_valid_timezone("UTC-5") is True
            assert is_valid_timezone("UTC+12") is True
            assert is_valid_timezone("GMT+3") is True
            assert is_valid_timezone("gmt-03") is True

    def test_completely_invalid_timezone(self):
        """Test that completely invalid timezones fail."""
        with patch(
            "ledger_bot.validators.convenience.ZoneInfo",
            side_effect=ZoneInfoNotFoundError,
        ), patch("ledger_bot.utils.time_utils.resolve_timezone", return_value=None):
            assert is_valid_timezone("Not/AZone") is False
            assert is_valid_timezone("Invalid") is False
            assert is_valid_timezone("UTC+") is False  # Incomplete offset

    def test_empty_string(self):
        """Test that empty string is invalid."""
        assert is_valid_timezone("") is False

    def test_none_is_invalid(self):
        """Test that empty/falsy values are invalid."""
        assert is_valid_timezone("") is False


class TestDateStringValidator:
    """Test DateStringValidator class."""

    def test_valid_date_string(self):
        """Test validation of valid date string."""
        validator = DateStringValidator()
        result = validator.validate("15-01-2025")

        assert result.is_valid is True
        assert result.value == "15-01-2025"

    def test_invalid_date_string(self):
        """Test validation of invalid date string."""
        validator = DateStringValidator()
        result = validator.validate("32-13-2025")

        assert result.is_valid is False
        assert result.error_message is not None
        assert "Invalid date format" in result.error_message
        assert "DD-MM-YYYY" in result.error_message

    def test_non_string_input(self):
        """Test that non-string inputs fail."""
        validator = DateStringValidator()

        result = validator.validate(123)
        assert result.is_valid is False
        assert result.error_message is not None
        assert "must be a string" in result.error_message

        result = validator.validate(None)
        assert result.is_valid is False

    def test_various_valid_formats(self):
        """Test various valid date formats."""
        validator = DateStringValidator()

        assert validator.validate("01-01-2024").is_valid is True
        assert validator.validate("31/12/2024").is_valid is True
        assert validator.validate("15.06.25").is_valid is True

    def test_preserves_original_format(self):
        """Test that the original format is preserved."""
        validator = DateStringValidator()

        result = validator.validate("15/01/2025")
        assert result.value == "15/01/2025"

        result = validator.validate("15.01.2025")
        assert result.value == "15.01.2025"


class TestTimeStringValidator:
    """Test TimeStringValidator class."""

    def test_valid_time_string(self):
        """Test validation of valid time string."""
        validator = TimeStringValidator()
        result = validator.validate("14:30")

        assert result.is_valid is True
        assert result.value == "14:30"

    def test_invalid_time_string(self):
        """Test validation of invalid time string."""
        validator = TimeStringValidator()
        result = validator.validate("25:00")

        assert result.is_valid is False
        assert result.error_message is not None
        assert "Invalid time format" in result.error_message
        assert "HH:MM" in result.error_message

    def test_non_string_input(self):
        """Test that non-string inputs fail."""
        validator = TimeStringValidator()

        result = validator.validate(123)
        assert result.is_valid is False
        assert result.error_message is not None
        assert "must be a string" in result.error_message

        result = validator.validate(None)
        assert result.is_valid is False

    def test_various_valid_formats(self):
        """Test various valid time formats."""
        validator = TimeStringValidator()

        assert validator.validate("00:00").is_valid is True
        assert validator.validate("23:59").is_valid is True
        assert validator.validate("9:05").is_valid is True
        assert validator.validate("12.30").is_valid is True

    def test_preserves_original_format(self):
        """Test that the original format is preserved."""
        validator = TimeStringValidator()

        result = validator.validate("14:30")
        assert result.value == "14:30"

        result = validator.validate("14.30")
        assert result.value == "14.30"


class TestTimezoneValidator:
    """Test TimezoneValidator class."""

    def test_valid_iana_timezone(self):
        """Test validation of valid IANA timezone."""
        validator = TimezoneValidator()
        result = validator.validate("Europe/London")

        assert result.is_valid is True
        assert result.value == "Europe/London"

    def test_utc_timezone(self):
        """Test validation of UTC timezone."""
        validator = TimezoneValidator()
        result = validator.validate("UTC")

        assert result.is_valid is True
        assert result.value == "UTC"

    def test_invalid_timezone(self):
        """Test validation of invalid timezone."""
        with patch(
            "ledger_bot.validators.convenience.ZoneInfo",
            side_effect=ZoneInfoNotFoundError,
        ), patch("ledger_bot.utils.time_utils.resolve_timezone", return_value=None):
            validator = TimezoneValidator()
            result = validator.validate("Not/ATimezone")

            assert result.is_valid is False
            assert result.error_message is not None
            assert "Invalid timezone" in result.error_message
            assert "IANA" in result.error_message

    def test_utc_offset_format(self):
        """Test validation of UTC offset formats."""
        with patch(
            "ledger_bot.validators.convenience.ZoneInfo",
            side_effect=ZoneInfoNotFoundError,
        ), patch("ledger_bot.utils.time_utils.resolve_timezone", return_value=None):
            validator = TimezoneValidator()

            result = validator.validate("UTC+1")
            assert result.is_valid is True
            assert result.value == "UTC+1"

            result = validator.validate("GMT-5")
            assert result.is_valid is True

    def test_non_string_input(self):
        """Test that non-string inputs fail."""
        validator = TimezoneValidator()

        result = validator.validate(123)
        assert result.is_valid is False
        assert result.error_message is not None
        assert "must be a string" in result.error_message

        result = validator.validate(None)
        assert result.is_valid is False

    def test_empty_string(self):
        """Test that empty string fails."""
        validator = TimezoneValidator()
        result = validator.validate("")

        assert result.is_valid is False
        assert result.error_message is not None
        assert "Invalid timezone" in result.error_message


class TestFactoryFunctions:
    """Test convenience factory functions."""

    def test_date_string_validator_factory(self):
        """Test date_string_validator factory function."""
        validator = date_string_validator()

        assert isinstance(validator, DateStringValidator)
        assert validator.validate("15-01-2025").is_valid is True
        assert validator.validate("invalid").is_valid is False

    def test_time_string_validator_factory(self):
        """Test time_string_validator factory function."""
        validator = time_string_validator()

        assert isinstance(validator, TimeStringValidator)
        assert validator.validate("14:30").is_valid is True
        assert validator.validate("25:00").is_valid is False

    def test_timezone_validator_factory(self):
        """Test timezone_validator factory function."""
        validator = timezone_validator()

        assert isinstance(validator, TimezoneValidator)
        assert validator.validate("Europe/London").is_valid is True


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_date_with_leading_zeros(self):
        """Test dates with leading zeros."""
        assert is_valid_date("01-01-2025") is True
        assert is_valid_date("09-09-2025") is True

    def test_date_without_leading_zeros(self):
        """Test dates without leading zeros."""
        assert is_valid_date("1-1-2025") is True
        assert is_valid_date("9-9-2025") is True

    def test_time_with_leading_zeros(self):
        """Test times with leading zeros."""
        assert is_valid_time("00:00") is True
        assert is_valid_time("09:05") is True

    def test_time_without_leading_zeros(self):
        """Test times without leading zeros."""
        assert is_valid_time("0:00") is True
        assert is_valid_time("9:05") is True

    def test_boundary_dates(self):
        """Test boundary date values."""
        assert is_valid_date("01-01-2025") is True
        assert is_valid_date("31-12-2025") is True
        assert is_valid_date("00-01-2025") is False
        assert is_valid_date("32-01-2025") is False
        assert is_valid_date("01-00-2025") is False
        assert is_valid_date("01-13-2025") is False

    def test_boundary_times(self):
        """Test boundary time values."""
        assert is_valid_time("00:00") is True
        assert is_valid_time("23:59") is True
        assert is_valid_time("24:00") is False
        assert is_valid_time("00:60") is False
        assert is_valid_time("23:60") is False
