"""Validation framework for ledger-bot.

This package provides a comprehensive validation system with:
- Base classes for creating custom validators
- Primitive type validators (string, int, float)
- Specialized validators (currency, datetime)
- Convenience boolean helpers for quick validation

The validation system uses a Result Pattern where validators return
ValidationResult objects containing either a success value or error message.

Quick Start
-----------
>>> from ledger_bot.validators import positive_integer_validator
>>> validator = positive_integer_validator()
>>> result = validator.validate("42")
>>> if result.is_valid:
...     print(f"Valid: {result.value}")
... else:
...     print(f"Error: {result.error_message}")
Valid: 42

For simple boolean checks, use convenience functions:
>>> from ledger_bot.validators import is_valid_date
>>> is_valid_date("15-01-2025")
True

Organization
------------
- base: Core ValidationResult and Validator base class
- primitives: String, Integer, Float validators
- specialized: Currency, DateTime, Composite validators
- convenience: Quick boolean helpers (is_valid_date, etc.) and their Validator wrappers
"""

# Base classes
from ledger_bot.validators.base import ValidationResult, Validator

# Convenience validation functions
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

# Primitive validators
from ledger_bot.validators.primitives import (
    FloatValidator,
    IntegerValidator,
    StringValidator,
    non_empty_string_validator,
    non_negative_float_validator,
    non_negative_integer_validator,
    positive_integer_validator,
)

# Specialized validators
from ledger_bot.validators.specialised import (
    CompositeValidator,
    CurrencyValidator,
    DateTimeValidator,
    currency_validator,
)

__all__ = [
    # Base classes
    "Validator",
    "ValidationResult",
    # Primitive validators
    "StringValidator",
    "IntegerValidator",
    "FloatValidator",
    # Primitive factory functions
    "positive_integer_validator",
    "non_negative_integer_validator",
    "non_negative_float_validator",
    "non_empty_string_validator",
    # Specialized validators
    "CurrencyValidator",
    "DateTimeValidator",
    "CompositeValidator",
    # Specialized factory functions
    "currency_validator",
    # Convenience validators (wrapping boolean functions)
    "DateStringValidator",
    "TimeStringValidator",
    "TimezoneValidator",
    # Convenience factory functions
    "date_string_validator",
    "time_string_validator",
    "timezone_validator",
    # Convenience boolean functions (quick validation)
    "is_valid_date",
    "is_valid_time",
    "is_valid_timezone",
]
