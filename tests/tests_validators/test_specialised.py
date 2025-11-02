"""Tests for specialized validators."""

from datetime import datetime

import pytest

from ledger_bot.validators.primitives import IntegerValidator, StringValidator
from ledger_bot.validators.specialised import (
    CompositeValidator,
    CurrencyValidator,
    DateTimeValidator,
    currency_validator,
)


class TestCurrencyValidator:
    """Test CurrencyValidator class."""

    def test_valid_currency(self):
        """Test validation of valid currency tuple."""
        validator = CurrencyValidator()
        result = validator.validate(("10.50", "GBP"))

        assert result.is_valid is True
        assert result.value == (10.50, "GBP")

    def test_uppercase_currency_code(self):
        """Test that currency codes are converted to uppercase."""
        validator = CurrencyValidator()
        result = validator.validate(("10.00", "gbp"))

        assert result.is_valid is True
        assert result.value == (10.00, "GBP")

    def test_strips_currency_code_whitespace(self):
        """Test that whitespace is stripped from currency code."""
        validator = CurrencyValidator()
        result = validator.validate(("10.00", "  USD  "))

        assert result.is_valid is True
        assert result.value == (10.00, "USD")

    def test_non_negative_by_default(self):
        """Test that negative amounts fail by default."""
        validator = CurrencyValidator()
        result = validator.validate(("-10.00", "GBP"))

        assert result.is_valid is False
        assert result.error_message is not None
        assert "non-negative" in result.error_message

    def test_allow_negative(self):
        """Test allowing negative amounts."""
        validator = CurrencyValidator(non_negative=False)
        result = validator.validate(("-10.00", "GBP"))

        assert result.is_valid is True
        assert result.value == (-10.00, "GBP")

    def test_min_value_constraint(self):
        """Test minimum value constraint."""
        validator = CurrencyValidator(min_value=10.0)

        result = validator.validate(("5.00", "USD"))
        assert result.is_valid is False

        result = validator.validate(("10.00", "USD"))
        assert result.is_valid is True

    def test_max_value_constraint(self):
        """Test maximum value constraint."""
        validator = CurrencyValidator(max_value=100.0)

        result = validator.validate(("150.00", "USD"))
        assert result.is_valid is False

        result = validator.validate(("100.00", "USD"))
        assert result.is_valid is True

    def test_allowed_currencies(self):
        """Test allowed currencies constraint."""
        validator = CurrencyValidator(allowed_currencies=["GBP", "USD", "EUR"])

        assert validator.validate(("10.00", "GBP")).is_valid is True
        assert validator.validate(("10.00", "USD")).is_valid is True
        assert validator.validate(("10.00", "EUR")).is_valid is True

        result = validator.validate(("10.00", "JPY"))
        assert result.is_valid is False
        assert result.error_message is not None
        assert "GBP, USD, EUR" in result.error_message

    def test_invalid_currency_code_format(self):
        """Test that invalid currency code formats fail."""
        validator = CurrencyValidator()

        # Too short
        result = validator.validate(("10.00", "US"))
        assert result.is_valid is False
        assert result.error_message is not None
        assert "3 uppercase letters" in result.error_message

        # Too long
        result = validator.validate(("10.00", "USDD"))
        assert result.is_valid is False

        # Contains numbers
        result = validator.validate(("10.00", "US1"))
        assert result.is_valid is False

    def test_empty_currency_code(self):
        """Test that empty currency code fails."""
        validator = CurrencyValidator()
        result = validator.validate(("10.00", ""))

        assert result.is_valid is False
        assert result.error_message is not None
        assert "cannot be empty" in result.error_message

    def test_non_string_currency_code(self):
        """Test that non-string currency codes fail."""
        validator = CurrencyValidator()
        result = validator.validate(("10.00", 123))  # type: ignore[arg-type]

        assert result.is_valid is False
        assert result.error_message is not None
        assert "must be a string" in result.error_message

    def test_invalid_amount(self):
        """Test that invalid amounts fail."""
        validator = CurrencyValidator()

        result = validator.validate(("abc", "GBP"))
        assert result.is_valid is False

        result = validator.validate(("", "GBP"))
        assert result.is_valid is False

    def test_wrong_tuple_structure(self):
        """Test that wrong tuple structures fail."""
        validator = CurrencyValidator()

        # Not a tuple
        result = validator.validate("10.00")  # type: ignore[arg-type]
        assert result.is_valid is False
        assert result.error_message is not None
        assert "must be a tuple" in result.error_message

        # Wrong length
        result = validator.validate(("10.00",))  # type: ignore[arg-type]
        assert result.is_valid is False

        result = validator.validate(("10.00", "GBP", "extra"))  # type: ignore[arg-type]
        assert result.is_valid is False

    def test_integer_amount(self):
        """Test that integer amounts are accepted."""
        validator = CurrencyValidator()
        result = validator.validate((10, "GBP"))

        assert result.is_valid is True
        assert result.value == (10.00, "GBP")

    def test_long_float_amount(self):
        """Test that integer amounts are accepted."""
        validator = CurrencyValidator()
        result = validator.validate((10.123, "GBP"))

        assert result.is_valid is True
        assert result.value == (10.123, "GBP")


class TestDateTimeValidator:
    """Test DateTimeValidator class."""

    @pytest.fixture
    def simple_parser(self):
        """Simple datetime parser for testing."""

        def parser(date_str, time_str, tz_str):
            from datetime import datetime
            from zoneinfo import ZoneInfo

            dt_str = f"{date_str} {time_str}"
            dt = datetime.strptime(dt_str, "%d-%m-%Y %H:%M")
            return dt.replace(tzinfo=ZoneInfo(tz_str))

        return parser

    def test_valid_datetime(self, simple_parser):
        """Test validation of valid datetime tuple."""
        validator = DateTimeValidator(parser=simple_parser)
        result = validator.validate(("15-01-2025", "14:30", "UTC"))

        assert result.is_valid is True
        assert isinstance(result.value, datetime)

    def test_parser_called_with_correct_arguments(self):
        """Test that parser is called with correct arguments."""
        called_with = []

        def tracking_parser(date_str, time_str, tz_str):
            called_with.append((date_str, time_str, tz_str))
            return datetime(2025, 1, 15, 14, 30)

        validator = DateTimeValidator(parser=tracking_parser)
        validator.validate(("15-01-2025", "14:30", "UTC"))

        assert called_with == [("15-01-2025", "14:30", "UTC")]

    def test_parser_error_returns_failure(self, simple_parser):
        """Test that parser errors are caught and returned as failures."""
        validator = DateTimeValidator(parser=simple_parser)
        result = validator.validate(("invalid", "14:30", "UTC"))

        assert result.is_valid is False
        assert result.error_message is not None
        assert "Invalid date or time format" in result.error_message

    def test_wrong_tuple_structure(self, simple_parser):
        """Test that wrong tuple structures fail."""
        validator = DateTimeValidator(parser=simple_parser)

        # Not a tuple
        result = validator.validate("15-01-2025")  # type: ignore[arg-type]
        assert result.is_valid is False
        assert result.error_message is not None
        assert "must be a tuple" in result.error_message

        # Wrong length
        result = validator.validate(("15-01-2025", "14:30"))  # type: ignore[arg-type]
        assert result.is_valid is False

    def test_allow_past_default(self, simple_parser):
        """Test that past dates are allowed by default."""
        validator = DateTimeValidator(parser=simple_parser)

        # Create a date in the past
        def past_parser(date_str, time_str, tz_str):
            from datetime import datetime
            from zoneinfo import ZoneInfo

            return datetime(2020, 1, 1, 12, 0, tzinfo=ZoneInfo(tz_str))

        validator = DateTimeValidator(parser=past_parser)
        result = validator.validate(("01-01-2020", "12:00", "UTC"))

        assert result.is_valid is True

    def test_disallow_past(self):
        """Test that past dates can be disallowed."""

        def past_parser(date_str, time_str, tz_str):
            from datetime import datetime
            from zoneinfo import ZoneInfo

            return datetime(2020, 1, 1, 12, 0, tzinfo=ZoneInfo(tz_str))

        validator = DateTimeValidator(parser=past_parser, allow_past=False)
        result = validator.validate(("01-01-2020", "12:00", "UTC"))

        assert result.is_valid is False
        assert result.error_message is not None
        assert "cannot be in the past" in result.error_message

    def test_allow_future_default(self, simple_parser):
        """Test that future dates are allowed by default."""

        def future_parser(date_str, time_str, tz_str):
            from datetime import datetime
            from zoneinfo import ZoneInfo

            return datetime(2099, 12, 31, 23, 59, tzinfo=ZoneInfo(tz_str))

        validator = DateTimeValidator(parser=future_parser)
        result = validator.validate(("31-12-2099", "23:59", "UTC"))

        assert result.is_valid is True

    def test_disallow_future(self):
        """Test that future dates can be disallowed."""

        def future_parser(date_str, time_str, tz_str):
            from datetime import datetime
            from zoneinfo import ZoneInfo

            return datetime(2099, 12, 31, 23, 59, tzinfo=ZoneInfo(tz_str))

        validator = DateTimeValidator(parser=future_parser, allow_future=False)
        result = validator.validate(("31-12-2099", "23:59", "UTC"))

        assert result.is_valid is False
        assert result.error_message is not None
        assert "cannot be in the future" in result.error_message


class TestCompositeValidator:
    """Test CompositeValidator class."""

    def test_single_validator(self):
        """Test composite with single validator."""
        validator = CompositeValidator(StringValidator(min_length=3))

        result = validator.validate("hello")
        assert result.is_valid is True
        assert result.value == "hello"

        result = validator.validate("hi")
        assert result.is_valid is False

    def test_multiple_validators_all_pass(self):
        """Test composite where all validators pass."""
        validator = CompositeValidator(
            StringValidator(min_length=1), IntegerValidator(positive=True)
        )

        result = validator.validate("42")
        assert result.is_valid is True
        assert result.value == 42

    def test_first_validator_fails(self):
        """Test composite where first validator fails."""
        validator = CompositeValidator(
            StringValidator(min_length=5), IntegerValidator()
        )

        result = validator.validate("42")
        assert result.is_valid is False
        assert result.error_message is not None
        assert "at least 5" in result.error_message

    def test_second_validator_fails(self):
        """Test composite where second validator fails."""
        validator = CompositeValidator(
            StringValidator(min_length=1), IntegerValidator(positive=True)
        )

        result = validator.validate("-5")
        assert result.is_valid is False
        assert result.error_message is not None
        assert "positive" in result.error_message

    def test_value_transformation_chain(self):
        """Test that values are transformed through the chain."""

        class UppercaseValidator(StringValidator):
            def validate(self, value):
                result = super().validate(value)
                if result.is_valid:
                    assert result.value is not None
                    from ledger_bot.validators.base import ValidationResult

                    return ValidationResult.success(result.value.upper())
                return result

        class AppendValidator(StringValidator):
            def validate(self, value):
                result = super().validate(value)
                if result.is_valid:
                    assert result.value is not None
                    from ledger_bot.validators.base import ValidationResult

                    return ValidationResult.success(result.value + "!")
                return result

        validator = CompositeValidator(UppercaseValidator(), AppendValidator())

        result = validator.validate("hello")
        assert result.is_valid is True
        assert result.value == "HELLO!"

    def test_three_validators(self):
        """Test composite with three validators."""
        validator = CompositeValidator(
            StringValidator(min_length=1, max_length=10),
            IntegerValidator(min_value=1),
            IntegerValidator(max_value=100),
        )

        assert validator.validate("50").is_valid is True
        assert validator.validate("0").is_valid is False
        assert validator.validate("150").is_valid is False

    def test_empty_composite(self):
        """Test composite with no validators."""
        validator = CompositeValidator()
        result = validator.validate("anything")

        # With no validators, should pass and return original value
        assert result.is_valid is True
        assert result.value == "anything"

    def test_error_message_from_failing_validator(self):
        """Test that error messages come from the failing validator."""
        validator = CompositeValidator(
            IntegerValidator(min_value=10), IntegerValidator(max_value=20)
        )

        result = validator.validate("5")
        assert result.is_valid is False
        assert result.error_message is not None
        assert "at least 10" in result.error_message

        result = validator.validate("25")
        assert result.is_valid is False
        assert result.error_message is not None
        assert "at most 20" in result.error_message


class TestFactoryFunctions:
    """Test convenience factory functions."""

    def test_currency_validator_factory(self):
        """Test currency_validator factory function."""
        validator = currency_validator()

        result = validator.validate(("10.50", "GBP"))
        assert result.is_valid is True
        assert result.value == (10.50, "GBP")

    def test_currency_validator_with_allowed_currencies(self):
        """Test currency_validator with allowed_currencies parameter."""
        validator = currency_validator(allowed_currencies=["GBP", "USD"])

        assert validator.validate(("10.00", "GBP")).is_valid is True
        assert validator.validate(("10.00", "EUR")).is_valid is False

    def test_currency_validator_is_non_negative(self):
        """Test that factory creates non-negative validator."""
        validator = currency_validator()
        result = validator.validate(("-10.00", "GBP"))

        assert result.is_valid is False
