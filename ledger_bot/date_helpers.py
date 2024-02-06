"""Various helpers for dealing with dates and times."""

import logging
from datetime import datetime, timedelta, timezone

import arrow
import dateutil
import discord

from ledger_bot.errors import DatetimeParsingError, TimeTravelError

log = logging.getLogger(__name__)


def is_naive(time: datetime | arrow.Arrow) -> bool:
    """Check if the provided time object is in a naive timezone (lacks timezone information)."""
    return time.tzinfo is None or time.tzinfo.utcoffset(time) is None


def convert_24_hours(hours: int, is_pm: bool) -> int:
    """Convert the given 12-hour format time to 24-hour format."""
    hours_is_12 = hours == 12
    if is_pm and not hours_is_12:
        return hours + 12
    elif not is_pm and hours_is_12:
        return 0
    else:
        return hours


async def parse_datetime(datetime: str, requester: discord.Member) -> datetime:
    """Parse a string into a valid datetime, attempting to guess timezones if not provided."""
    try:
        parsed_date = dateutil.parser.parse(datetime, fuzzy=True, dayfirst=True)
        was_parsed_date_naive = is_naive(parsed_date)
        parsed_date = arrow.get(parsed_date)

        if was_parsed_date_naive:
            pass

        near_now = arrow.utcnow() + timedelta(minutes=1)
        if parsed_date.to(timezone.utc) < near_now:
            raise TimeTravelError(parsed_date.datetime, near_now.datetime)
        return parsed_date.datetime
    except (TypeError, dateutil.parser.ParserError) as error:
        raise DatetimeParsingError() from error


async def guess_timezone(member: discord.Member) -> None:
    """
    Attempt to predict the members timezone.

    Based on users role.
    """
    return None
