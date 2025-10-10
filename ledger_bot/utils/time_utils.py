"""Time utilities."""

import contextlib
import logging
import re
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

log = logging.getLogger(__name__)

COMMON_TZ_ALIASES = {
    "EST": "America/New_York",
    "CST": "America/Chicago",
    "PST": "America/Los_Angeles",
    "CET": "Europe/Paris",
    "BST": "Europe/London",
    "AEST": "Australia/Sydney",
    "IST": "Asia/Kolkata",
    "GMT": "Etc/GMT",
    "UTC": "Etc/UTC",
}


def resolve_timezone(tz: str) -> timezone | ZoneInfo | None:
    """Resolve common shortened timezones into valid IANA timezones."""
    log.debug(f"Resolving timezone: {tz}")

    tz = tz.strip()

    # Check common aliases first
    if tz.upper() in COMMON_TZ_ALIASES:
        try:
            return ZoneInfo(COMMON_TZ_ALIASES[tz.upper()])
        except ZoneInfoNotFoundError:
            log.warning(f"Alias {tz} could not be resolved, defaulting to UTC")
            return timezone.utc

    # Try IANA timezone
    with contextlib.suppress(ZoneInfoNotFoundError):
        return ZoneInfo(tz)

    # Try UTC/GMT offset
    offset_match = re.fullmatch(
        r"^(?:UTC|GMT)?([+-])(\d{1,2})(?::?(\d{2}))?$", tz.upper()
    )

    if offset_match:
        sign, hours, minutes = offset_match.groups()
        hours, minutes = int(hours), int(minutes or 0)
        delta = timedelta(hours=hours, minutes=minutes)
        if sign == "-":
            delta = -delta
        return timezone(delta)

    # Could not resolve
    log.warning(f"Invalid timezone: {tz}")
    return None


def build_datetime(date_str: str, time_str: str, tz_str: str) -> datetime:
    """Combine date, time, and timezone strings into a timezone-aware datetime.

    Supported formats:
      date_str: DD-MM-YYYY, DD/MM/YYYY, or DD.MM.YYYY (2- or 4-digit year)
      time_str: HH:MM or HH.MM
      tz_str:   IANA name (e.g. "Europe/London") or UTC offset (e.g. "UTC+5", "UTC-03:30", "GMT+2")

    Returns:
        datetime object (timezone-aware)
    """
    # Normalise date / time separators
    clean_date = date_str.replace("/", "-").replace(".", "-")
    clean_time = time_str.replace(".", ":")

    # Parse date / time
    try:
        dt = datetime.strptime(f"{clean_date} {clean_time}", "%d-%m-%Y %H:%M")
    except ValueError:
        dt = datetime.strptime(f"{clean_date} {clean_time}", "%d-%m-%y %H:%M")

    # Resolve timezone
    tz = resolve_timezone(tz_str)
    if not tz:
        log.info(f"Invalid timezone: {tz_str.strip()}, defaulting to UTC")
        tz = timezone.utc

    # Attach timezone
    return dt.replace(tzinfo=tz)


def build_relative_datetime(days: int, hours: int, tz_str: str | None) -> datetime:
    """Build a datetime offset from now by a given number of days and hours.

    Optionally adjusting to specified timezone. Supports IANA timezones and UTC offsets.

    Parameters
    ----------
    days : int
        Number of days to offset from now.
    hours : int
        Number of hours to offset from now.
    tz : str | None
        Timezone string, e.g. "Europe/London" or "UTC+5".

    Returns
    -------
    datetime
        Datetime object representing now + offset, with timezone applied.
    """
    # Get current time in UTC
    now = datetime.now(timezone.utc)

    # Apply the offset
    offset_dt = now + timedelta(days=days, hours=hours)

    # Normalise and parse timezone
    if not tz_str:
        # No timezone info provided, therefore leave in utc
        return offset_dt

    tz = resolve_timezone(tz_str)
    if not tz:
        log.info(f"Invalid timezone: {tz_str.strip()}, defaulting to UTC")
        tz = timezone.utc

    return offset_dt.astimezone(tz)
