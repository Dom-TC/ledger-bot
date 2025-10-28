from unittest.mock import patch
from zoneinfo import ZoneInfoNotFoundError

import pytest

from ledger_bot.utils import (
    is_valid_date,
    is_valid_time,
    is_valid_timezone,
)


@pytest.mark.parametrize(
    "value,expected",
    [
        ("01-01-2024", True),
        ("1/1/24", True),
        ("31.12.2024", True),
        ("00-01-2024", False),
        ("32-01-2024", False),
        ("01-13-2024", False),
        ("abc", False),
        ("2024-01-01", False),
    ],
)
def test_is_valid_date(value, expected):
    assert is_valid_date(value) is expected


@pytest.mark.parametrize(
    "value,expected",
    [
        ("00:00", True),
        ("23:59", True),
        ("7.30", True),
        ("24:00", False),
        ("12:60", False),
        ("-1:00", False),
        ("hello", False),
    ],
)
def test_is_valid_time(value, expected):
    assert is_valid_time(value) is expected


def test_is_valid_timezone_valid_iana(monkeypatch):
    """Valid IANA timezone passes via ZoneInfo."""
    from zoneinfo import ZoneInfo

    tz = "Europe/London"
    assert is_valid_timezone(tz) is True


def test_is_valid_timezone_invalid_then_resolved(monkeypatch):
    """ZoneInfo fails, but resolve_timezone returns a match."""
    with patch(
        "ledger_bot.utils.validators.ZoneInfo", side_effect=ZoneInfoNotFoundError
    ), patch("ledger_bot.utils.validators.resolve_timezone", return_value="UTC"):
        assert is_valid_timezone("GMT") is True


def test_is_valid_timezone_invalid_then_offset(monkeypatch):
    """ZoneInfo and resolve_timezone both fail, but format matches UTC offset."""
    with patch(
        "ledger_bot.utils.validators.ZoneInfo", side_effect=ZoneInfoNotFoundError
    ), patch("ledger_bot.utils.validators.resolve_timezone", return_value=None):
        assert is_valid_timezone("UTC+5") is True
        assert is_valid_timezone("gmt-03") is True


def test_is_valid_timezone_invalid(monkeypatch):
    """Neither valid IANA, nor resolvable, nor offset."""
    with patch(
        "ledger_bot.utils.validators.ZoneInfo", side_effect=ZoneInfoNotFoundError
    ), patch("ledger_bot.utils.validators.resolve_timezone", return_value=None):
        assert is_valid_timezone("Not/AZone") is False


def test_is_valid_timezone_empty_string():
    assert is_valid_timezone("") is False
