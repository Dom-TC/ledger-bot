"""Tests for base validation classes."""

import pytest

from ledger_bot.validators.base import ValidationResult, Validator


class TestValidationResult:
    """Test ValidationResult class."""

    def test_success_creates_valid_result(self):
        """Test that success() creates a valid result with value."""
        result = ValidationResult.success(42)

        assert result.is_valid is True
        assert result.value == 42
        assert result.error_message is None

    def test_success_with_string_value(self):
        """Test success with string value."""
        result = ValidationResult.success("hello")

        assert result.is_valid is True
        assert result.value == "hello"
        assert result.error_message is None

    def test_success_with_complex_value(self):
        """Test success with complex object."""
        value = {"key": "value", "list": [1, 2, 3]}
        result = ValidationResult.success(value)

        assert result.is_valid is True
        assert result.value == value
        assert result.error_message is None

    def test_failure_creates_invalid_result(self):
        """Test that failure() creates an invalid result with error message."""
        result = ValidationResult.failure("Something went wrong")

        assert result.is_valid is False
        assert result.value is None
        assert result.error_message == "Something went wrong"

    def test_failure_with_empty_message(self):
        """Test failure with empty error message."""
        result = ValidationResult.failure("")

        assert result.is_valid is False
        assert result.value is None
        assert result.error_message == ""

    def test_direct_instantiation_success(self):
        """Test direct instantiation of success result."""
        result = ValidationResult(is_valid=True, value=100, error_message=None)

        assert result.is_valid is True
        assert result.value == 100
        assert result.error_message is None

    def test_direct_instantiation_failure(self):
        """Test direct instantiation of failure result."""
        result = ValidationResult(is_valid=False, value=None, error_message="Error")

        assert result.is_valid is False
        assert result.value is None
        assert result.error_message == "Error"


class TestValidator:
    """Test Validator abstract base class."""

    def test_validator_is_abstract(self):
        """Test that Validator cannot be instantiated directly."""
        with pytest.raises(TypeError):
            Validator()  # type: ignore[abstract]

    def test_validator_requires_validate_method(self):
        """Test that subclasses must implement validate method."""

        class IncompleteValidator(Validator):
            pass

        with pytest.raises(TypeError):
            IncompleteValidator()  # type: ignore[abstract]

    def test_validator_subclass_with_validate(self):
        """Test that proper subclass can be instantiated."""

        class SimpleValidator(Validator):
            def validate(self, value):
                if value == "valid":
                    return ValidationResult.success(value)
                return ValidationResult.failure("Invalid")

        validator = SimpleValidator()
        assert validator is not None

    def test_validator_callable_interface(self):
        """Test that validators can be called directly."""

        class SimpleValidator(Validator):
            def validate(self, value):
                return ValidationResult.success(value.upper())

        validator = SimpleValidator()
        result = validator("hello")

        assert result.is_valid is True
        assert result.value == "HELLO"

    def test_validator_callable_returns_validation_result(self):
        """Test that calling validator returns ValidationResult."""

        class FailingValidator(Validator):
            def validate(self, value):
                return ValidationResult.failure("Always fails")

        validator = FailingValidator()
        result = validator("anything")

        assert isinstance(result, ValidationResult)
        assert result.is_valid is False
        assert result.error_message == "Always fails"

    def test_validator_chaining_through_callable(self):
        """Test that validators can be chained using callable interface."""

        class DoubleValidator(Validator):
            def validate(self, value):
                return ValidationResult.success(value * 2)

        class AddTenValidator(Validator):
            def validate(self, value):
                return ValidationResult.success(value + 10)

        v1 = DoubleValidator()
        v2 = AddTenValidator()

        result1 = v1(5)
        result2 = v2(result1.value)

        assert result2.value == 20  # (5 * 2) + 10

    def test_validator_abstract_validate_method(self):
        """Test that abstract validate method can be called via super()."""

        class TestValidator(Validator):
            def validate(self, value):
                result = super().validate(value)
                return ValidationResult.success(value)

        validator = TestValidator()
        result = validator("test")

        assert result.is_valid is True
        assert result.value == "test"
