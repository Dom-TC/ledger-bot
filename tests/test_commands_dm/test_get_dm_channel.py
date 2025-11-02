"""Tests for get_dm_channel."""

from unittest.mock import AsyncMock, Mock

import pytest

from ledger_bot.commands_dm.get_dm_channel import get_dm_channel


@pytest.mark.asyncio
async def test_get_dm_channel_existing():
    """Test getting existing DM channel."""
    mock_dm_channel = Mock()
    mock_user = Mock()
    mock_user.dm_channel = mock_dm_channel
    mock_user.create_dm = AsyncMock()

    result = await get_dm_channel(mock_user)

    assert result == mock_dm_channel
    # Should not create new DM if one exists
    mock_user.create_dm.assert_not_called()


@pytest.mark.asyncio
async def test_get_dm_channel_create_new():
    """Test creating new DM channel when none exists."""
    mock_new_dm_channel = Mock()
    mock_user = Mock()
    mock_user.dm_channel = None
    mock_user.create_dm = AsyncMock(return_value=mock_new_dm_channel)

    result = await get_dm_channel(mock_user)

    assert result == mock_new_dm_channel
    mock_user.create_dm.assert_called_once()


@pytest.mark.asyncio
async def test_get_dm_channel_with_member():
    """Test getting DM channel works with discord.Member."""
    mock_dm_channel = Mock()
    mock_member = Mock()
    mock_member.dm_channel = mock_dm_channel

    result = await get_dm_channel(mock_member)

    assert result == mock_dm_channel
