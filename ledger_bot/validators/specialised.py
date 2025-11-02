"""Specialized validators for complex domain types.

This module provides validators for application-specific data types:
- CurrencyValidator: Currency amount and code validation
- DateTimeValidator: Date and time parsing and validation
- CompositeValidator: Chain multiple validators together
"""

import re
from datetime import datetime
from typing import Any, Callable, Optional

from ledger_bot.validators.base import ValidationResult, Validator
from ledger_bot.validators.primitives import FloatValidator


class CurrencyValidator(Validator[tuple[float, str]]):
    """Validates currency amount and code.

    Validates amount and currency code.

    Parameters
    ----------
    min_value : Optional[float]
        Minimum allowed value in currency units (e.g., 0.01 for 1 cent)
    max_value : Optional[float]
        Maximum allowed value in currency units
    non_negative : bool
        Require value to be non-negative (default: True)
    allowed_currencies : Optional[list[str]]
        List of allowed currency codes (e.g., ['GBP', 'USD', 'EUR'])
        If None, accepts any 3-letter currency code

    Examples
    --------
    >>> validator = CurrencyValidator()
    >>> result = validator.validate(("10.50", "GBP"))
    >>> result.is_valid
    True
    >>> result.value
    (1050, 'GBP')

    >>> validator = CurrencyValidator(allowed_currencies=['GBP', 'USD'])
    >>> result = validator.validate(("5.00", "EUR"))
    >>> result.is_valid
    False
    """

    def __init__(
        self,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        non_negative: bool = True,
        allowed_currencies: Optional[list[str]] = None,
    ):
        self.min_value = min_value
        self.max_value = max_value
        self.non_negative = non_negative
        self.allowed_currencies = allowed_currencies

    def validate(self, value: tuple[Any, Any]) -> ValidationResult[tuple[float, str]]:
        """Validate a currency amount and code.

        Parameters
        ----------
        value : tuple[Any, Any]
            Tuple of (amount, currency_code)

        Returns
        -------
        ValidationResult[tuple[int, str]]
            Result containing (amount, currency_code) or error
        """
        if not isinstance(value, tuple) or len(value) != 2:
            return ValidationResult.failure(
                "Currency value must be a tuple of (amount, currency_code)"
            )

        amount, currency_code = value

        # Validate amount
        float_validator = FloatValidator(
            min_value=self.min_value,
            max_value=self.max_value,
            non_negative=self.non_negative,
        )
        amount_result = float_validator.validate(amount)

        if not amount_result.is_valid:
            return ValidationResult.failure(amount_result.error_message or "")

        # Validate currency code
        if not isinstance(currency_code, str):
            return ValidationResult.failure("Currency code must be a string")

        currency_code = currency_code.strip().upper()

        if not currency_code:
            return ValidationResult.failure("Currency code cannot be empty")

        # Check allowed currencies
        if self.allowed_currencies and currency_code not in self.allowed_currencies:
            return ValidationResult.failure(
                f"Currency code must be one of: {', '.join(self.allowed_currencies)}"
            )

        # Basic currency code format check (3 letters)
        if not re.match(r"^[A-Z]{3}$", currency_code):
            return ValidationResult.failure(
                "Currency code must be 3 uppercase letters (e.g., GBP, USD, EUR)"
            )

        return ValidationResult.success((amount_result.value, currency_code))


class DateTimeValidator(Validator[datetime]):
    """Validates and parses datetime strings.

    This validator uses a provided parser function to convert date/time strings
    into datetime objects, with optional constraints on past/future dates.

    Parameters
    ----------
    parser : Callable[[str, str, str], datetime]
        Function that takes (date_str, time_str, tz_str) and returns datetime
    allow_past : bool
        Whether to allow dates in the past (default: True)
    allow_future : bool
        Whether to allow dates in the future (default: True)

    Examples
    --------
    >>> def simple_parser(date_str, time_str, tz_str):
    ...     return datetime.strptime(f"{date_str} {time_str}", "%d-%m-%Y %H:%M")
    >>> validator = DateTimeValidator(parser=simple_parser)
    >>> result = validator.validate(("15-01-2025", "14:30", "UTC"))
    >>> result.is_valid
    True
    """

    def __init__(
        self,
        parser: Callable[[str, str, str], datetime],
        allow_past: bool = True,
        allow_future: bool = True,
    ):
        self.parser = parser
        self.allow_past = allow_past
        self.allow_future = allow_future

    def validate(self, value: tuple[str, str, str]) -> ValidationResult[datetime]:
        """Validate a datetime value.

        Parameters
        ----------
        value : tuple[str, str, str]
            Tuple of (date_str, time_str, timezone_str)

        Returns
        -------
        ValidationResult[datetime]
            Result containing parsed datetime or error
        """
        if not isinstance(value, tuple) or len(value) != 3:
            return ValidationResult.failure(
                "DateTime value must be a tuple of (date_str, time_str, timezone_str)"
            )

        date_str, time_str, tz_str = value

        # Try to parse the datetime
        try:
            dt = self.parser(date_str, time_str, tz_str)
        except ValueError as e:
            return ValidationResult.failure(f"Invalid date or time format: {str(e)}")

        # Check past/future constraints
        now = datetime.now(dt.tzinfo)

        if not self.allow_past and dt < now:
            return ValidationResult.failure("Date cannot be in the past")

        if not self.allow_future and dt > now:
            return ValidationResult.failure("Date cannot be in the future")

        return ValidationResult.success(dt)


class CompositeValidator(Validator[Any]):
    """Chains multiple validators together.

    All validators must pass for the composite to pass. The output of each
    validator becomes the input to the next validator in the chain.

    Parameters
    ----------
    *validators : Validator
        Variable number of validators to run in sequence

    Examples
    --------
    >>> from ledger_bot.validators.primitives import StringValidator, IntegerValidator
    >>> # First validate as string, then as integer
    >>> validator = CompositeValidator(
    ...     StringValidator(min_length=1),
    ...     IntegerValidator(positive=True)
    ... )
    >>> result = validator.validate("42")
    >>> result.is_valid
    True
    >>> result.value
    42
    """

    def __init__(self, *validators: Validator):
        self.validators = validators

    def validate(self, value: Any) -> ValidationResult[Any]:
        """Run all validators in sequence.

        The value is passed through each validator, with each validator's
        output becoming the input to the next validator.
        """
        for validator in self.validators:
            result = validator.validate(value)
            if not result.is_valid:
                return result
            # Pass the transformed value to the next validator
            value = result.value

        return ValidationResult.success(value)


# Convenience factory functions


def currency_validator(
    allowed_currencies: Optional[list[str]] = None,
) -> CurrencyValidator:
    """Create a validator for currency values.

    Parameters
    ----------
    allowed_currencies : Optional[list[str]]
        List of allowed currency codes

    Returns
    -------
    CurrencyValidator
        Validator that accepts currency amounts and codes

    Examples
    --------
    >>> validator = currency_validator(allowed_currencies=['GBP', 'USD'])
    >>> result = validator.validate(("10.50", "GBP"))
    >>> result.is_valid
    True
    """
    return CurrencyValidator(non_negative=True, allowed_currencies=allowed_currencies)
