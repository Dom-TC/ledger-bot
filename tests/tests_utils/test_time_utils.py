from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from freezegun import freeze_time

from ledger_bot.utils.time_utils import (
    build_datetime,
    build_relative_datetime,
    resolve_timezone,
)


class DummyZoneInfo(ZoneInfo):
    """Dummy subclass used for testing alias failure."""

    def __new__(cls, key):
        if key == "Europe/Paris":
            raise ZoneInfoNotFoundError
        return super().__new__(cls, key)


def test_resolve_timezone_common_alias_success(monkeypatch):
    """Should resolve a known alias to its proper IANA timezone."""
    tz = resolve_timezone("BST")
    assert isinstance(tz, ZoneInfo)
    assert tz.key == "Europe/London"


def test_resolve_timezone_common_alias_fallback_to_utc(monkeypatch):
    """If alias exists but ZoneInfo fails, fallback to UTC."""
    monkeypatch.setattr("ledger_bot.utils.time_utils.ZoneInfo", DummyZoneInfo)
    tz = resolve_timezone("CET")
    assert tz == timezone.utc


def test_resolve_timezone_valid_iana(monkeypatch):
    """Directly valid IANA timezone returns ZoneInfo."""
    tz = resolve_timezone("Europe/London")
    assert isinstance(tz, ZoneInfo)
    assert tz.key == "Europe/London"


def test_resolve_timezone_valid_offset():
    """Should resolve UTC or GMT offset strings correctly."""
    tz = resolve_timezone("UTC+2")
    assert isinstance(tz, timezone)
    assert tz.utcoffset(None) == timedelta(hours=2)

    tz = resolve_timezone("GMT-03:30")
    assert isinstance(tz, timezone)
    assert tz.utcoffset(None) == timedelta(hours=-3, minutes=-30)


def test_resolve_timezone_invalid(monkeypatch, caplog):
    """Unknown timezone string should log a warning and return None."""
    caplog.set_level("WARNING")
    tz = resolve_timezone("NotATimezone")
    assert tz is None
    assert any("Invalid timezone" in msg for msg in caplog.messages)


def test_build_datetime_valid_full_year(monkeypatch):
    """Should correctly parse and attach timezone."""
    dt = build_datetime("01-12-2023", "14:30", "UTC+2")
    assert isinstance(dt, datetime)
    assert dt.year == 2023
    assert dt.tzinfo
    assert dt.tzinfo.utcoffset(dt) == timedelta(hours=2)


def test_build_datetime_valid_short_year(monkeypatch):
    """Should handle 2-digit year format gracefully."""
    dt = build_datetime("01/12/23", "14.30", "UTC+0")
    assert dt.year == 2023
    assert dt.tzinfo == timezone.utc


def test_build_datetime_invalid_timezone(monkeypatch, caplog):
    """If timezone cannot be resolved, default to UTC and log info."""
    caplog.set_level("INFO")
    monkeypatch.setattr("ledger_bot.utils.time_utils.resolve_timezone", lambda _: None)
    dt = build_datetime("01-12-2023", "14:30", "BADZONE")
    assert dt.tzinfo == timezone.utc
    assert any("Invalid timezone" in msg for msg in caplog.messages)


@freeze_time("2025-01-01 12:00:00")
def test_build_relative_datetime_valid(monkeypatch):
    """Should offset current time and convert timezone."""
    fixed_now = datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc)
    monkeypatch.setattr("ledger_bot.utils.time_utils.datetime", datetime)

    dt = build_relative_datetime(days=1, hours=2, tz_str="UTC+3")
    assert dt.tzinfo
    assert dt.tzinfo.utcoffset(dt) == timedelta(hours=3)
    assert dt.day == 2


@freeze_time("2025-01-01 12:00:00")
def test_build_relative_datetime_no_tz(monkeypatch):
    """If tz_str is None, should stay in UTC."""
    fixed_now = datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc)
    monkeypatch.setattr("ledger_bot.utils.time_utils.datetime", datetime)

    dt = build_relative_datetime(days=0, hours=1, tz_str=None)
    assert dt.tzinfo == timezone.utc
    assert dt.hour == 13


@freeze_time("2025-01-01 12:00:00")
def test_build_relative_datetime_invalid_tz(monkeypatch, caplog):
    """If timezone cannot be resolved, fall back to UTC and log."""
    caplog.set_level("INFO")
    fixed_now = datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc)
    monkeypatch.setattr("ledger_bot.utils.time_utils.datetime", datetime)
    monkeypatch.setattr("ledger_bot.utils.time_utils.resolve_timezone", lambda _: None)

    dt = build_relative_datetime(days=1, hours=1, tz_str="BAD")
    assert dt.tzinfo == timezone.utc
    assert any("Invalid timezone" in msg for msg in caplog.messages)
