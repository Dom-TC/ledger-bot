"""Tests for LedgerBot main class."""

import logging
from unittest.mock import AsyncMock, Mock, patch

import discord
import pytest

from ledger_bot.LedgerBot import LedgerBot


@pytest.fixture
def mock_ledger_bot(mock_config, session_factory):
    """Create a mock LedgerBot instance."""
    from apscheduler.schedulers.asyncio import AsyncIOScheduler

    from ledger_bot.services import Service

    scheduler = AsyncIOScheduler()

    service = Mock(spec=Service)
    service.currency = Mock()
    service.currency.get_or_add_currency = AsyncMock()

    reminders = Mock()

    bot = LedgerBot(
        config=mock_config,
        service=service,
        scheduler=scheduler,
        reminders=reminders,
        session_factory=session_factory,
    )

    # Mock Discord API methods
    bot.change_presence = AsyncMock()
    bot.get_guild = Mock()
    bot.tree = Mock()
    bot.tree.sync = AsyncMock()

    return bot


@pytest.mark.asyncio
async def test_ledger_bot_initialization(mock_ledger_bot, mock_config):
    """Test LedgerBot initialization."""
    assert mock_ledger_bot.config == mock_config
    assert mock_ledger_bot.guild is not None
    assert mock_ledger_bot.guild.id == mock_config.guild


@pytest.mark.asyncio
@patch("ledger_bot.LedgerBot.LedgerBot.get_version_number")
async def test_on_ready(mock_get_version, mock_ledger_bot, mock_config):
    """Test on_ready event handler."""
    mock_get_version.return_value = "v1.0.0-db123"

    mock_guild = Mock(spec=discord.Guild)
    mock_guild.id = mock_config.guild

    mock_ledger_bot.get_guild = Mock(return_value=mock_guild)
    mock_ledger_bot.scheduler = Mock()
    mock_ledger_bot.scheduler.start = Mock()
    mock_ledger_bot.scheduler.running = True

    await mock_ledger_bot.on_ready()

    # Verify version was retrieved
    mock_get_version.assert_called_once()
    assert mock_ledger_bot.version == "v1.0.0-db123"

    # Verify presence was changed
    mock_ledger_bot.change_presence.assert_called_once()

    # Verify guild was set
    assert mock_ledger_bot.guild == mock_guild

    # Verify slash commands synced
    mock_ledger_bot.tree.sync.assert_called_once_with(guild=mock_guild)

    # Verify scheduler started
    mock_ledger_bot.scheduler.start.assert_called_once()

    # Verify currencies were initialized
    assert mock_ledger_bot.service.currency.get_or_add_currency.call_count == 3


@pytest.mark.asyncio
async def test_on_message_dm(mock_ledger_bot):
    """Test on_message handling DMs."""
    mock_message = Mock(spec=discord.Message)
    mock_message.channel = Mock(spec=discord.DMChannel)

    with patch("ledger_bot.LedgerBot.is_dm", return_value=True):
        with patch(
            "ledger_bot.LedgerBot.process_dm", new_callable=AsyncMock
        ) as mock_process_dm:
            await mock_ledger_bot.on_message(mock_message)

            mock_process_dm.assert_called_once_with(mock_ledger_bot, mock_message)


@pytest.mark.asyncio
async def test_on_message_included_channel(mock_ledger_bot, mock_config):
    """Test on_message handling messages in included channels."""
    mock_message = Mock(spec=discord.Message)
    mock_message.channel = Mock(spec=discord.TextChannel)
    mock_message.channel.name = "wine-sales"

    mock_config.channels.include = ["wine-sales"]
    mock_config.channels.exclude = []

    with patch("ledger_bot.LedgerBot.is_dm", return_value=False):
        with patch(
            "ledger_bot.LedgerBot.process_message", new_callable=AsyncMock
        ) as mock_process:
            await mock_ledger_bot.on_message(mock_message)

            mock_process.assert_called_once_with(mock_ledger_bot, mock_message)


@pytest.mark.asyncio
async def test_on_message_excluded_channel(mock_ledger_bot, mock_config):
    """Test on_message ignoring messages in excluded channels."""
    mock_message = Mock(spec=discord.Message)
    mock_message.channel = Mock(spec=discord.TextChannel)
    mock_message.channel.name = "general"

    mock_config.channels.include = ["wine-sales", "general"]
    mock_config.channels.exclude = ["general"]

    with patch("ledger_bot.LedgerBot.is_dm", return_value=False):
        with patch(
            "ledger_bot.LedgerBot.process_message", new_callable=AsyncMock
        ) as mock_process:
            await mock_ledger_bot.on_message(mock_message)

            # Should not process since channel is excluded
            mock_process.assert_not_called()


@pytest.mark.asyncio
async def test_on_message_not_included_channel(mock_ledger_bot, mock_config):
    """Test on_message ignoring messages in non-included channels."""
    mock_message = Mock(spec=discord.Message)
    mock_message.channel = Mock(spec=discord.TextChannel)
    mock_message.channel.name = "random"

    mock_config.channels.include = ["wine-sales"]
    mock_config.channels.exclude = []

    with patch("ledger_bot.LedgerBot.is_dm", return_value=False):
        with patch(
            "ledger_bot.LedgerBot.process_message", new_callable=AsyncMock
        ) as mock_process:
            await mock_ledger_bot.on_message(mock_message)

            # Should not process since channel not in include list
            mock_process.assert_not_called()


@pytest.mark.asyncio
async def test_on_raw_reaction_add_transaction(mock_ledger_bot):
    """Test on_raw_reaction_add handling transaction reactions."""
    payload = Mock(spec=discord.RawReactionActionEvent)
    payload.channel_id = 123456
    payload.member = Mock()
    payload.guild_id = 789012

    mock_channel = Mock(spec=discord.TextChannel)
    mock_guild = Mock(spec=discord.Guild)

    mock_ledger_bot.get_or_fetch_channel = AsyncMock(return_value=mock_channel)
    mock_ledger_bot.get_guild = Mock(return_value=mock_guild)
    mock_ledger_bot.handle_transaction_reaction = AsyncMock(return_value=True)

    await mock_ledger_bot.on_raw_reaction_add(payload)

    mock_ledger_bot.handle_transaction_reaction.assert_called_once_with(payload)


@pytest.mark.asyncio
async def test_on_raw_reaction_add_role_reaction(mock_ledger_bot):
    """Test on_raw_reaction_add handling role reactions."""
    payload = Mock(spec=discord.RawReactionActionEvent)
    payload.channel_id = 123456
    payload.member = Mock()
    payload.guild_id = 789012

    mock_channel = Mock(spec=discord.TextChannel)
    mock_guild = Mock(spec=discord.Guild)

    mock_ledger_bot.get_or_fetch_channel = AsyncMock(return_value=mock_channel)
    mock_ledger_bot.get_guild = Mock(return_value=mock_guild)
    mock_ledger_bot.handle_transaction_reaction = AsyncMock(return_value=False)
    mock_ledger_bot.handle_role_reaction = AsyncMock(return_value=True)

    await mock_ledger_bot.on_raw_reaction_add(payload)

    mock_ledger_bot.handle_transaction_reaction.assert_called_once()
    mock_ledger_bot.handle_role_reaction.assert_called_once_with(payload)


@pytest.mark.asyncio
async def test_on_raw_reaction_add_no_reactor(mock_ledger_bot, caplog):
    """Test on_raw_reaction_add with no reactor."""

    with caplog.at_level(logging.DEBUG):
        payload = Mock(spec=discord.RawReactionActionEvent)
        payload.channel_id = 123456
        payload.member = None
        payload.guild_id = 789012

        mock_channel = Mock(spec=discord.TextChannel)

        mock_ledger_bot.get_or_fetch_channel = AsyncMock(return_value=mock_channel)

        # Should return early, not calling handlers
        await mock_ledger_bot.on_raw_reaction_add(payload)
        assert "Payload contained no reactor. Ignoring payload." in caplog.text


@pytest.mark.asyncio
async def test_on_raw_reaction_remove(mock_ledger_bot):
    """Test on_raw_reaction_remove handling."""
    payload = Mock(spec=discord.RawReactionActionEvent)
    payload.channel_id = 123456
    payload.user_id = 999888777
    payload.guild_id = 789012

    mock_channel = Mock(spec=discord.TextChannel)
    mock_guild = Mock(spec=discord.Guild)

    mock_ledger_bot.get_or_fetch_channel = AsyncMock(return_value=mock_channel)
    mock_ledger_bot.get_guild = Mock(return_value=mock_guild)
    mock_ledger_bot.handled_role_reaction_removal = AsyncMock(return_value=True)

    await mock_ledger_bot.on_raw_reaction_remove(payload)

    mock_ledger_bot.handled_role_reaction_removal.assert_called_once_with(payload)


@pytest.mark.asyncio
async def test_on_raw_reaction_remove_no_guild(mock_ledger_bot):
    """Test on_raw_reaction_remove with no guild."""
    payload = Mock(spec=discord.RawReactionActionEvent)
    payload.channel_id = 123456
    payload.user_id = 999888777
    payload.guild_id = None  # No guild

    mock_channel = Mock(spec=discord.TextChannel)

    mock_ledger_bot.get_or_fetch_channel = AsyncMock(return_value=mock_channel)

    # Should return early
    await mock_ledger_bot.on_raw_reaction_remove(payload)


@pytest.mark.asyncio
async def test_on_disconnect(mock_ledger_bot):
    """Test on_disconnect logging."""
    # Just verify it doesn't raise an error
    await mock_ledger_bot.on_disconnect()
