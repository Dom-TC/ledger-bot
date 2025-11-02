"""Primitive type validators for basic data types.

This module provides validators for fundamental types:
- StringValidator: String validation with length and pattern constraints
- IntegerValidator: Integer validation with range constraints
- FloatValidator: Float validation with range constraints
"""

import re
from typing import Any, Optional

from ledger_bot.validators.base import ValidationResult, Validator


class StringValidator(Validator[str]):
    """Validates string inputs with optional constraints.

    Parameters
    ----------
    min_length : Optional[int]
        Minimum allowed string length
    max_length : Optional[int]
        Maximum allowed string length
    pattern : Optional[str]
        Regex pattern that the string must match
    strip : bool
        Whether to strip whitespace (default: True)
    allow_empty : bool
        Whether to allow empty strings after stripping (default: False)

    Examples
    --------
    >>> validator = StringValidator(min_length=3, max_length=50)
    >>> result = validator.validate("Hello")
    >>> result.is_valid
    True
    >>> result.value
    'Hello'

    >>> validator = StringValidator(pattern=r"^[A-Z]+$")
    >>> result = validator.validate("ABC")
    >>> result.is_valid
    True
    """

    def __init__(
        self,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        pattern: Optional[str] = None,
        strip: bool = True,
        allow_empty: bool = False,
    ):
        self.min_length = min_length
        self.max_length = max_length
        self.pattern = re.compile(pattern) if pattern else None
        self.strip = strip
        self.allow_empty = allow_empty

    def validate(self, value: Any) -> ValidationResult[str]:
        """Validate a string value."""
        if not isinstance(value, str):
            return ValidationResult.failure("Value must be a string")

        # Strip whitespace if requested
        if self.strip:
            value = value.strip()

        # Check empty
        if not value and not self.allow_empty:
            return ValidationResult.failure("Value cannot be empty")

        # Check length constraints
        if self.min_length is not None and len(value) < self.min_length:
            return ValidationResult.failure(
                f"Value must be at least {self.min_length} characters"
            )

        if self.max_length is not None and len(value) > self.max_length:
            return ValidationResult.failure(
                f"Value must be at most {self.max_length} characters"
            )

        # Check pattern
        if self.pattern and not self.pattern.match(value):
            return ValidationResult.failure("Value does not match required format")

        return ValidationResult.success(value)


class IntegerValidator(Validator[int]):
    """Validates integer inputs with optional constraints.

    Parameters
    ----------
    min_value : Optional[int]
        Minimum allowed value (inclusive)
    max_value : Optional[int]
        Maximum allowed value (inclusive)
    positive : bool
        Require value to be positive (> 0)
    non_negative : bool
        Require value to be non-negative (>= 0)

    Examples
    --------
    >>> validator = IntegerValidator(min_value=1, max_value=100)
    >>> result = validator.validate("50")
    >>> result.is_valid
    True
    >>> result.value
    50

    >>> validator = IntegerValidator(positive=True)
    >>> result = validator.validate("-5")
    >>> result.is_valid
    False
    """

    def __init__(
        self,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None,
        positive: bool = False,
        non_negative: bool = False,
    ):
        self.min_value = min_value
        self.max_value = max_value
        self.positive = positive
        self.non_negative = non_negative

    def validate(self, value: Any) -> ValidationResult[int]:
        """Validate an integer value."""
        # Try to convert to int
        try:
            if isinstance(value, str):
                value = value.strip()
            int_value = int(value)
        except (ValueError, TypeError):
            return ValidationResult.failure("Value must be a valid integer")

        # Check positive constraint
        if self.positive and int_value <= 0:
            return ValidationResult.failure("Value must be positive (greater than 0)")

        # Check non-negative constraint
        if self.non_negative and int_value < 0:
            return ValidationResult.failure("Value must be non-negative (0 or greater)")

        # Check min/max constraints
        if self.min_value is not None and int_value < self.min_value:
            return ValidationResult.failure(f"Value must be at least {self.min_value}")

        if self.max_value is not None and int_value > self.max_value:
            return ValidationResult.failure(f"Value must be at most {self.max_value}")

        return ValidationResult.success(int_value)


class FloatValidator(Validator[float]):
    """Validates float inputs with optional constraints.

    Parameters
    ----------
    min_value : Optional[float]
        Minimum allowed value (inclusive)
    max_value : Optional[float]
        Maximum allowed value (inclusive)
    positive : bool
        Require value to be positive (> 0)
    non_negative : bool
        Require value to be non-negative (>= 0)

    Examples
    --------
    >>> validator = FloatValidator(min_value=0.0, max_value=100.0)
    >>> result = validator.validate("42.5")
    >>> result.is_valid
    True
    >>> result.value
    42.5

    >>> validator = FloatValidator(non_negative=True)
    >>> result = validator.validate("-1.5")
    >>> result.is_valid
    False
    """

    def __init__(
        self,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        positive: bool = False,
        non_negative: bool = False,
    ):
        self.min_value = min_value
        self.max_value = max_value
        self.positive = positive
        self.non_negative = non_negative

    def validate(self, value: Any) -> ValidationResult[float]:
        """Validate a float value."""
        # Try to convert to float
        try:
            if isinstance(value, str):
                value = value.strip()
            float_value = float(value)
        except (ValueError, TypeError):
            return ValidationResult.failure("Value must be a valid number")

        # Check positive constraint
        if self.positive and float_value <= 0:
            return ValidationResult.failure("Value must be positive (greater than 0)")

        # Check non-negative constraint
        if self.non_negative and float_value < 0:
            return ValidationResult.failure("Value must be non-negative (0 or greater)")

        # Check min/max constraints
        if self.min_value is not None and float_value < self.min_value:
            return ValidationResult.failure(f"Value must be at least {self.min_value}")

        if self.max_value is not None and float_value > self.max_value:
            return ValidationResult.failure(f"Value must be at most {self.max_value}")

        return ValidationResult.success(float_value)


# Convenience factory functions


def positive_integer_validator() -> IntegerValidator:
    """Create a validator for positive integers (> 0).

    Returns
    -------
    IntegerValidator
        Validator that only accepts positive integers

    Examples
    --------
    >>> validator = positive_integer_validator()
    >>> validator.validate("10").is_valid
    True
    >>> validator.validate("0").is_valid
    False
    """
    return IntegerValidator(positive=True)


def non_negative_integer_validator() -> IntegerValidator:
    """Create a validator for non-negative integers (>= 0).

    Returns
    -------
    IntegerValidator
        Validator that accepts zero and positive integers
    """
    return IntegerValidator(non_negative=True)


def non_negative_float_validator() -> FloatValidator:
    """Create a validator for non-negative floats (>= 0).

    Returns
    -------
    FloatValidator
        Validator that accepts zero and positive floats

    Examples
    --------
    >>> validator = non_negative_float_validator()
    >>> validator.validate("10.5").is_valid
    True
    >>> validator.validate("-1.0").is_valid
    False
    """
    return FloatValidator(non_negative=True)


def non_empty_string_validator(max_length: Optional[int] = None) -> StringValidator:
    """Create a validator for non-empty strings.

    Parameters
    ----------
    max_length : Optional[int]
        Maximum allowed string length

    Returns
    -------
    StringValidator
        Validator that rejects empty strings

    Examples
    --------
    >>> validator = non_empty_string_validator(max_length=100)
    >>> validator.validate("Hello").is_valid
    True
    >>> validator.validate("").is_valid
    False
    """
    return StringValidator(min_length=1, max_length=max_length, allow_empty=False)
