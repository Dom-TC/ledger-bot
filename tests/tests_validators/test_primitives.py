"""Tests for primitive type validators."""

import pytest

from ledger_bot.validators.primitives import (
    FloatValidator,
    IntegerValidator,
    StringValidator,
    non_empty_string_validator,
    non_negative_float_validator,
    non_negative_integer_validator,
    positive_integer_validator,
)


class TestStringValidator:
    """Test StringValidator class."""

    def test_valid_string(self):
        """Test validation of a valid string."""
        validator = StringValidator()
        result = validator.validate("hello")

        assert result.is_valid is True
        assert result.value == "hello"

    def test_strips_whitespace_by_default(self):
        """Test that whitespace is stripped by default."""
        validator = StringValidator()
        result = validator.validate("  hello  ")

        assert result.is_valid is True
        assert result.value == "hello"

    def test_no_strip_when_disabled(self):
        """Test that whitespace is preserved when strip=False."""
        validator = StringValidator(strip=False)
        result = validator.validate("  hello  ")

        assert result.is_valid is True
        assert result.value == "  hello  "

    def test_empty_string_fails_by_default(self):
        """Test that empty strings fail by default."""
        validator = StringValidator()
        result = validator.validate("")

        assert result.is_valid is False
        assert result.error_message is not None
        assert "cannot be empty" in result.error_message

    def test_empty_string_allowed(self):
        """Test that empty strings pass when allow_empty=True."""
        validator = StringValidator(allow_empty=True)
        result = validator.validate("")

        assert result.is_valid is True
        assert result.value == ""

    def test_min_length_constraint(self):
        """Test minimum length constraint."""
        validator = StringValidator(min_length=5)

        result = validator.validate("hi")
        assert result.is_valid is False
        assert result.error_message is not None
        assert "at least 5" in result.error_message

        result = validator.validate("hello")
        assert result.is_valid is True

    def test_max_length_constraint(self):
        """Test maximum length constraint."""
        validator = StringValidator(max_length=5)

        result = validator.validate("hello world")
        assert result.is_valid is False
        assert result.error_message is not None
        assert "at most 5" in result.error_message

        result = validator.validate("hello")
        assert result.is_valid is True

    def test_min_max_length_together(self):
        """Test min and max length constraints together."""
        validator = StringValidator(min_length=3, max_length=10)

        assert validator.validate("ab").is_valid is False
        assert validator.validate("abc").is_valid is True
        assert validator.validate("hello").is_valid is True
        assert validator.validate("hello world").is_valid is False

    def test_pattern_matching(self):
        """Test regex pattern matching."""
        validator = StringValidator(pattern=r"^[A-Z]+$")

        assert validator.validate("ABC").is_valid is True
        assert validator.validate("abc").is_valid is False
        assert validator.validate("ABC123").is_valid is False

    def test_pattern_with_numbers(self):
        """Test pattern matching with numbers."""
        validator = StringValidator(pattern=r"^\d{3}-\d{4}$")

        assert validator.validate("123-4567").is_valid is True
        assert validator.validate("12-345").is_valid is False

    def test_non_string_input_fails(self):
        """Test that non-string inputs fail."""
        validator = StringValidator()

        assert validator.validate(123).is_valid is False
        assert validator.validate(None).is_valid is False
        assert validator.validate([]).is_valid is False

    def test_whitespace_only_string(self):
        """Test that whitespace-only strings fail when stripped."""
        validator = StringValidator()
        result = validator.validate("   ")

        assert result.is_valid is False
        assert result.error_message is not None
        assert "cannot be empty" in result.error_message


class TestIntegerValidator:
    """Test IntegerValidator class."""

    def test_valid_integer_string(self):
        """Test validation of valid integer string."""
        validator = IntegerValidator()
        result = validator.validate("42")

        assert result.is_valid is True
        assert result.value == 42

    def test_valid_integer_number(self):
        """Test validation of actual integer."""
        validator = IntegerValidator()
        result = validator.validate(42)

        assert result.is_valid is True
        assert result.value == 42

    def test_negative_integer(self):
        """Test validation of negative integers."""
        validator = IntegerValidator()
        result = validator.validate("-10")

        assert result.is_valid is True
        assert result.value == -10

    def test_strips_whitespace(self):
        """Test that whitespace is stripped from string input."""
        validator = IntegerValidator()
        result = validator.validate("  42  ")

        assert result.is_valid is True
        assert result.value == 42

    def test_invalid_string_fails(self):
        """Test that non-numeric strings fail."""
        validator = IntegerValidator()

        assert validator.validate("abc").is_valid is False
        assert validator.validate("12.34").is_valid is False
        assert validator.validate("").is_valid is False

    def test_none_fails(self):
        """Test that None input fails."""
        validator = IntegerValidator()
        result = validator.validate(None)

        assert result.is_valid is False
        assert result.error_message is not None
        assert "valid integer" in result.error_message

    def test_positive_constraint(self):
        """Test positive integer constraint."""
        validator = IntegerValidator(positive=True)

        assert validator.validate("0").is_valid is False
        assert validator.validate("-1").is_valid is False
        assert validator.validate("1").is_valid is True
        assert validator.validate("100").is_valid is True

    def test_non_negative_constraint(self):
        """Test non-negative integer constraint."""
        validator = IntegerValidator(non_negative=True)

        assert validator.validate("-1").is_valid is False
        assert validator.validate("0").is_valid is True
        assert validator.validate("1").is_valid is True

    def test_min_value_constraint(self):
        """Test minimum value constraint."""
        validator = IntegerValidator(min_value=10)

        result = validator.validate("5")
        assert result.is_valid is False
        assert result.error_message is not None
        assert "at least 10" in result.error_message

        assert validator.validate("10").is_valid is True
        assert validator.validate("15").is_valid is True

    def test_max_value_constraint(self):
        """Test maximum value constraint."""
        validator = IntegerValidator(max_value=100)

        result = validator.validate("150")
        assert result.is_valid is False
        assert result.error_message is not None
        assert "at most 100" in result.error_message

        assert validator.validate("100").is_valid is True
        assert validator.validate("50").is_valid is True

    def test_min_max_together(self):
        """Test min and max constraints together."""
        validator = IntegerValidator(min_value=1, max_value=100)

        assert validator.validate("0").is_valid is False
        assert validator.validate("1").is_valid is True
        assert validator.validate("50").is_valid is True
        assert validator.validate("100").is_valid is True
        assert validator.validate("101").is_valid is False

    def test_positive_overrides_min_value(self):
        """Test that positive constraint is checked."""
        validator = IntegerValidator(positive=True, min_value=-10)

        # Even though min_value is -10, positive constraint requires > 0
        assert validator.validate("0").is_valid is False
        assert validator.validate("1").is_valid is True


class TestFloatValidator:
    """Test FloatValidator class."""

    def test_valid_float_string(self):
        """Test validation of valid float string."""
        validator = FloatValidator()
        result = validator.validate("42.5")

        assert result.is_valid is True
        assert result.value == 42.5

    def test_valid_float_number(self):
        """Test validation of actual float."""
        validator = FloatValidator()
        result = validator.validate(42.5)

        assert result.is_valid is True
        assert result.value == 42.5

    def test_integer_as_float(self):
        """Test that integers are accepted and converted to float."""
        validator = FloatValidator()
        result = validator.validate("42")

        assert result.is_valid is True
        assert result.value == 42.0

    def test_negative_float(self):
        """Test validation of negative floats."""
        validator = FloatValidator()
        result = validator.validate("-10.5")

        assert result.is_valid is True
        assert result.value == -10.5

    def test_strips_whitespace(self):
        """Test that whitespace is stripped from string input."""
        validator = FloatValidator()
        result = validator.validate("  42.5  ")

        assert result.is_valid is True
        assert result.value == 42.5

    def test_invalid_string_fails(self):
        """Test that non-numeric strings fail."""
        validator = FloatValidator()

        assert validator.validate("abc").is_valid is False
        assert validator.validate("").is_valid is False

    def test_none_fails(self):
        """Test that None input fails."""
        validator = FloatValidator()
        result = validator.validate(None)

        assert result.is_valid is False
        assert result.error_message is not None
        assert "valid number" in result.error_message

    def test_positive_constraint(self):
        """Test positive float constraint."""
        validator = FloatValidator(positive=True)

        assert validator.validate("0.0").is_valid is False
        assert validator.validate("-1.5").is_valid is False
        assert validator.validate("0.1").is_valid is True
        assert validator.validate("100.5").is_valid is True

    def test_non_negative_constraint(self):
        """Test non-negative float constraint."""
        validator = FloatValidator(non_negative=True)

        assert validator.validate("-1.5").is_valid is False
        assert validator.validate("0.0").is_valid is True
        assert validator.validate("1.5").is_valid is True

    def test_min_value_constraint(self):
        """Test minimum value constraint."""
        validator = FloatValidator(min_value=10.0)

        result = validator.validate("5.5")
        assert result.is_valid is False
        assert result.error_message is not None
        assert "at least 10.0" in result.error_message

        assert validator.validate("10.0").is_valid is True
        assert validator.validate("15.5").is_valid is True

    def test_max_value_constraint(self):
        """Test maximum value constraint."""
        validator = FloatValidator(max_value=100.0)

        result = validator.validate("150.5")
        assert result.is_valid is False
        assert result.error_message is not None
        assert "at most 100.0" in result.error_message

        assert validator.validate("100.0").is_valid is True
        assert validator.validate("50.5").is_valid is True

    def test_min_max_together(self):
        """Test min and max constraints together."""
        validator = FloatValidator(min_value=1.0, max_value=100.0)

        assert validator.validate("0.5").is_valid is False
        assert validator.validate("1.0").is_valid is True
        assert validator.validate("50.5").is_valid is True
        assert validator.validate("100.0").is_valid is True
        assert validator.validate("100.1").is_valid is False

    def test_scientific_notation(self):
        """Test that scientific notation is accepted."""
        validator = FloatValidator()
        result = validator.validate("1.5e2")

        assert result.is_valid is True
        assert result.value == 150.0


class TestFactoryFunctions:
    """Test convenience factory functions."""

    def test_positive_integer_validator(self):
        """Test positive_integer_validator factory."""
        validator = positive_integer_validator()

        assert validator.validate("0").is_valid is False
        assert validator.validate("-1").is_valid is False
        assert validator.validate("1").is_valid is True
        assert validator.validate("100").is_valid is True

    def test_non_negative_integer_validator(self):
        """Test non_negative_integer_validator factory."""
        validator = non_negative_integer_validator()

        assert validator.validate("-1").is_valid is False
        assert validator.validate("0").is_valid is True
        assert validator.validate("1").is_valid is True

    def test_non_negative_float_validator(self):
        """Test non_negative_float_validator factory."""
        validator = non_negative_float_validator()

        assert validator.validate("-1.5").is_valid is False
        assert validator.validate("0.0").is_valid is True
        assert validator.validate("1.5").is_valid is True

    def test_non_empty_string_validator(self):
        """Test non_empty_string_validator factory."""
        validator = non_empty_string_validator()

        assert validator.validate("").is_valid is False
        assert validator.validate("   ").is_valid is False
        assert validator.validate("hello").is_valid is True

    def test_non_empty_string_validator_with_max_length(self):
        """Test non_empty_string_validator with max_length parameter."""
        validator = non_empty_string_validator(max_length=5)

        assert validator.validate("hello").is_valid is True
        assert validator.validate("hello world").is_valid is False
