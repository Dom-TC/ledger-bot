"""Convenience validation functions for quick boolean checks.

This module provides simple boolean validation functions for common use cases
where you just need a yes/no answer. For detailed error messages or value
transformation, use the corresponding Validator classes instead.

Convenience functions:
- is_valid_date: Check if string matches DD-MM-YYYY format
- is_valid_time: Check if string matches HH:MM format
- is_valid_timezone: Check if string is a valid IANA timezone

Validator classes:
- DateStringValidator: Validates date strings with error messages
- TimeStringValidator: Validates time strings with error messages
- TimezoneValidator: Validates timezone strings with error messages

When to use which:
- Use is_valid_*() for simple if/else checks
- Use *Validator classes when you need detailed error messages
"""

import logging
import re
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from ledger_bot.validators.base import ValidationResult, Validator

log = logging.getLogger(__name__)


# ============================================================================
# Convenience boolean validation functions
# ============================================================================
# These are simple wrappers around the Validator classes for quick checks.
# Use these when you just need a yes/no answer.
# Use the Validator classes when you need error messages or transformed values.


def is_valid_date(value: str) -> bool:
    """Check if a string is a valid date.

    A valid date is in the format DD-MM-(YY)YY, using `-`, `/`, or `.` as divider.

    This is a convenience function for simple boolean checks.
    For detailed error messages, use DateStringValidator instead.

    Parameters
    ----------
    value : str
        The date string to validate

    Returns
    -------
    bool
        True if the string matches the date format

    Examples
    --------
    >>> is_valid_date("15-01-2025")
    True
    >>> is_valid_date("01/12/25")
    True
    >>> is_valid_date("invalid")
    False
    """
    return bool(
        re.match(
            r"^(0?[1-9]|[12][0-9]|3[01])[-/.](0?[1-9]|1[0-2])[-/.](\d{2}|\d{4})$",
            value,
        )
    )


def is_valid_time(value: str) -> bool:
    """Check if a string is a valid time.

    A valid time is in the format HH:MM, using `:` or `.` as divider.

    This is a convenience function for simple boolean checks.
    For detailed error messages, use TimeStringValidator instead.

    Parameters
    ----------
    value : str
        The time string to validate

    Returns
    -------
    bool
        True if the string matches the time format

    Examples
    --------
    >>> is_valid_time("14:30")
    True
    >>> is_valid_time("9:05")
    True
    >>> is_valid_time("25:00")
    False
    """
    return bool(re.match(r"^([01]?[0-9]|2[0-3])[:.]([0-5][0-9])$", value))


def is_valid_timezone(tz: str) -> bool:
    """Check if a string is a valid timezone.

    Either a valid IANA timezone, one of our specified shortenings, or as a UTC offset.

    This is a convenience function for simple boolean checks.
    For detailed error messages, use TimezoneValidator instead.

    Parameters
    ----------
    tz : str
        The timezone string to validate

    Returns
    -------
    bool
        True if the string is a valid timezone

    Examples
    --------
    >>> is_valid_timezone("Europe/London")
    True
    >>> is_valid_timezone("UTC")
    True
    >>> is_valid_timezone("UTC+1")
    True
    >>> is_valid_timezone("invalid")
    False
    """
    if not tz:
        return False
    try:
        ZoneInfo(tz)
        return True
    except ZoneInfoNotFoundError:
        # Check if valid shortening (import here to avoid circular import)
        from ledger_bot.utils.time_utils import resolve_timezone

        resolved = resolve_timezone(tz)
        if resolved:
            return True
        else:
            # Accept offsets like UTC+1, UTC-05, etc.
            return bool(re.match(r"^(?:UTC|GMT)[+-]\d{1,2}$", tz.upper()))


# ============================================================================
# New Validator classes wrapping legacy functions
# ============================================================================


class DateStringValidator(Validator[str]):
    """Validates date strings in DD-MM-YYYY format.

    This validator checks if a string matches the expected date format
    but does not parse it into a datetime object. Use DateTimeValidator
    for parsing and validation together.

    Format: DD-MM-YYYY with `-`, `/`, or `.` as separator
    - DD: 01-31 (day)
    - MM: 01-12 (month)
    - YYYY: 2 or 4 digit year

    Examples
    --------
    >>> validator = DateStringValidator()
    >>> result = validator.validate("15-01-2025")
    >>> result.is_valid
    True
    >>> result.value
    '15-01-2025'

    >>> result = validator.validate("32-13-2025")
    >>> result.is_valid
    False
    """

    def validate(self, value: Any) -> ValidationResult[str]:
        """Validate a date string."""
        if not isinstance(value, str):
            return ValidationResult.failure("Date must be a string")

        if not is_valid_date(value):
            return ValidationResult.failure(
                "Invalid date format. Expected DD-MM-YYYY (e.g., 15-01-2025)"
            )

        return ValidationResult.success(value)


class TimeStringValidator(Validator[str]):
    """Validates time strings in HH:MM format.

    This validator checks if a string matches the expected time format
    but does not parse it into a time object.

    Format: HH:MM with `:` or `.` as separator
    - HH: 00-23 (hour)
    - MM: 00-59 (minute)

    Examples
    --------
    >>> validator = TimeStringValidator()
    >>> result = validator.validate("14:30")
    >>> result.is_valid
    True
    >>> result.value
    '14:30'

    >>> result = validator.validate("25:00")
    >>> result.is_valid
    False
    """

    def validate(self, value: Any) -> ValidationResult[str]:
        """Validate a time string."""
        if not isinstance(value, str):
            return ValidationResult.failure("Time must be a string")

        if not is_valid_time(value):
            return ValidationResult.failure(
                "Invalid time format. Expected HH:MM (e.g., 14:30)"
            )

        return ValidationResult.success(value)


class TimezoneValidator(Validator[str]):
    """Validates timezone strings.

    Accepts:
    - IANA timezone names (e.g., "Europe/London", "America/New_York")
    - Shorthand names defined in the application (resolved via resolve_timezone)
    - UTC offsets (e.g., "UTC+1", "GMT-5")

    Examples
    --------
    >>> validator = TimezoneValidator()
    >>> result = validator.validate("Europe/London")
    >>> result.is_valid
    True
    >>> result.value
    'Europe/London'

    >>> result = validator.validate("UTC+1")
    >>> result.is_valid
    True

    >>> result = validator.validate("InvalidTimezone")
    >>> result.is_valid
    False
    """

    def validate(self, value: Any) -> ValidationResult[str]:
        """Validate a timezone string."""
        if not isinstance(value, str):
            return ValidationResult.failure("Timezone must be a string")

        if not is_valid_timezone(value):
            return ValidationResult.failure(
                "Invalid timezone. Expected IANA timezone (e.g., 'Europe/London') "
                "or UTC offset (e.g., 'UTC+1')"
            )

        return ValidationResult.success(value)


# ============================================================================
# Convenience factory functions
# ============================================================================


def date_string_validator() -> DateStringValidator:
    """Create a validator for date strings (DD-MM-YYYY format).

    Returns
    -------
    DateStringValidator
        Validator that checks date string format

    Examples
    --------
    >>> validator = date_string_validator()
    >>> validator.validate("15-01-2025").is_valid
    True
    """
    return DateStringValidator()


def time_string_validator() -> TimeStringValidator:
    """Create a validator for time strings (HH:MM format).

    Returns
    -------
    TimeStringValidator
        Validator that checks time string format

    Examples
    --------
    >>> validator = time_string_validator()
    >>> validator.validate("14:30").is_valid
    True
    """
    return TimeStringValidator()


def timezone_validator() -> TimezoneValidator:
    """Create a validator for timezone strings.

    Returns
    -------
    TimezoneValidator
        Validator that checks timezone validity

    Examples
    --------
    >>> validator = timezone_validator()
    >>> validator.validate("Europe/London").is_valid
    True
    """
    return TimezoneValidator()
