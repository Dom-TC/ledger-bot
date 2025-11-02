"""Tests for Member model."""

import datetime
from unittest.mock import patch

import pytest

from ledger_bot.models.member import Member


class TestMember:
    """Test Member model."""

    def test_member_display_name_with_nickname(self):
        """Test display_name property returns nickname when set."""
        member = Member()
        member.username = "john_doe"
        member.nickname = "Johnny"
        member.discord_id = 123456

        assert member.display_name == "Johnny"

    def test_member_display_name_without_nickname(self):
        """Test display_name property returns username when nickname is None."""
        member = Member()
        member.username = "jane_doe"
        member.nickname = None
        member.discord_id = 789012

        assert member.display_name == "jane_doe"

    def test_member_display_name_with_empty_nickname(self):
        """Test display_name property returns username when nickname is empty string."""
        member = Member()
        member.username = "bob_smith"
        member.nickname = ""
        member.discord_id = 345678

        # Empty string is falsy, so should return username
        assert member.display_name == "bob_smith"

    def test_member_resolve_timezone_with_valid_timezone(self):
        """Test resolve_timezone property with valid timezone."""
        member = Member()
        member.username = "test_user"
        member.discord_id = 123
        member.timezone = "Europe/London"

        tz = member.resolve_timezone

        assert tz is not None
        # The resolve_timezone function should return a ZoneInfo object
        assert hasattr(tz, "key") or isinstance(tz, datetime.timezone)

    def test_member_resolve_timezone_with_none(self):
        """Test resolve_timezone property when timezone is None."""
        member = Member()
        member.username = "test_user"
        member.discord_id = 123
        member.timezone = None

        tz = member.resolve_timezone

        assert tz is None

    def test_member_resolve_timezone_with_utc_offset(self):
        """Test resolve_timezone property with UTC offset."""
        member = Member()
        member.username = "test_user"
        member.discord_id = 123
        member.timezone = "UTC+5"

        tz = member.resolve_timezone

        assert tz is not None
        assert isinstance(tz, datetime.timezone)
