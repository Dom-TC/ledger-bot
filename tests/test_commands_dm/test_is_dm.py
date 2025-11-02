"""Tests for is_dm function."""

import pytest

from ledger_bot.commands_dm.is_dm import is_dm


class TestIsDm:
    """Test suite for is_dm function."""

    def test_is_dm_with_dm_channel(self, mock_dm_channel, message_factory):
        """Test that DM channel is correctly identified."""
        message = message_factory(channel=mock_dm_channel)

        assert is_dm(message) is True

    def test_is_dm_with_text_channel(self, mock_text_channel, message_factory):
        """Test that text channel is not identified as DM."""
        message = message_factory(channel=mock_text_channel)

        assert is_dm(message) is False

    def test_is_dm_with_guild_channel_has_guild_attr(
        self, mock_text_channel, message_factory
    ):
        """Test that text channel with guild attribute is not a DM."""
        # Text channels have a guild attribute
        message = message_factory(channel=mock_text_channel)
        assert hasattr(message.channel, "guild")
        assert is_dm(message) is False

    def test_is_dm_with_dm_channel_no_guild_attr(
        self, mock_dm_channel, message_factory
    ):
        """Test that DM channel has no guild (None) and is identified as DM."""
        # DM channels have guild=None
        message = message_factory(channel=mock_dm_channel)
        assert message.channel.guild is None
        assert is_dm(message) is True
