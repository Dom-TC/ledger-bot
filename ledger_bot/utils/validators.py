"""Various data validation functions."""

import logging
import re
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .time_utils import resolve_timezone

log = logging.getLogger(__name__)


def is_valid_date(value: str) -> bool:
    """Check if a string is a valid date.

    A valid date is in the format DD-MM-(YY)YY, using `-`, `/`, or `.` as divider.
    """
    return bool(
        re.match(
            r"^(0?[1-9]|[12][0-9]|3[01])[-/.](0?[1-9]|1[0-2])[-/.](\d{2}|\d{4})$", value
        )
    )


def is_valid_time(value: str) -> bool:
    """Check if a string is a valid time.

    A valid time is in the format HH:MM, using `:`, or `.` as divider.
    """
    return bool(re.match(r"^([01]?[0-9]|2[0-3])[:.]([0-5][0-9])$", value))


def is_valid_timezone(tz: str) -> bool:
    """Check if a string is a valid timezone.

    Either a valid IANA timezone, one of our specified shortenings, or as a UTC offset.
    """
    if not tz:
        return False
    try:
        ZoneInfo(tz)
        return True
    except ZoneInfoNotFoundError:
        # Check if valid shortening
        resolved = resolve_timezone(tz)
        if resolved:
            return True
        else:
            # Accept offsets like UTC+1, UTC-05, etc.
            return bool(re.match(r"^(?:UTC|GMT)[+-]\d{1,2}$", tz.upper()))
