"""Time utilities."""

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


def resolve_timezone(tz: str) -> str | None:
    """Resolve common shortened timezones into valid IANA timezones."""
    log.debug(f"Resolving timezone: {tz}")

    tz = tz.strip()
    if tz.upper() in COMMON_TZ_ALIASES:
        return COMMON_TZ_ALIASES[tz.upper()]
    try:
        ZoneInfo(tz)
        return tz
    except ZoneInfoNotFoundError:
        if bool(re.match(r"^(?:UTC|GMT)[+-]\d{1,2}$", tz.upper())):
            return tz.upper()
        else:
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

    # Normalise and parse timezone
    tz_str = tz_str.strip().upper()
    resolved_tz = resolve_timezone(tz_str)

    if resolved_tz:
        tz_str = resolved_tz
    else:
        log.info(f"Invalid timezone: {tz_str.strip().upper()}, setting to UTC")
        tz_str = "Etc/UTC"

    # Handle explicit UTC offset timezones
    offset_match = re.fullmatch(r"^(?:UTC|GMT)?([+-])(\d{1,2})(?::?(\d{2}))?$", tz_str)
    if offset_match:
        sign, hours, minutes = offset_match.groups()
        hours = int(hours)
        minutes = int(minutes or 0)
        delta = timedelta(hours=hours, minutes=minutes)
        if sign == "-":
            delta = -delta
        tz = timezone(delta)
    else:
        # Fallback to IANA
        try:
            tz = ZoneInfo(tz_str)
        except ZoneInfoNotFoundError:
            raise ValueError(f"Invalid timezone: {tz_str!r}")

    # --- Attach timezone ---
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

    tz_str = tz_str.strip().upper()
    resolved_tz = resolve_timezone(tz_str)

    if resolved_tz:
        tz_str = resolved_tz
    else:
        log.info(f"Invalid timezone: {tz_str.strip().upper()}, setting to UTC")
        tz_str = "Etc/UTC"

    # Handle explicit UTC offset timezones
    offset_match = re.fullmatch(r"^(?:UTC|GMT)?([+-])(\d{1,2})(?::?(\d{2}))?$", tz_str)
    if offset_match:
        offset_sign, offset_hours, offset_mins = offset_match.groups()
        offset_hours = int(offset_hours)
        offset_mins = int(offset_mins or 0)
        delta = timedelta(hours=offset_hours, minutes=offset_mins)
        if offset_sign == "-":
            delta = -delta
        tz = timezone(delta)
    else:
        # Fallback to IANA
        try:
            tz = ZoneInfo(tz_str)
        except ZoneInfoNotFoundError:
            raise ValueError(f"Invalid timezone: {tz_str!r}")

    return offset_dt.astimezone(tz)
