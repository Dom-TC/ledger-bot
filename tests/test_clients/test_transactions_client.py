"""Tests for TransactionsClient."""

from unittest.mock import AsyncMock, Mock, patch

import discord
import pytest


@pytest.fixture
def mock_transactions_client(
    mock_config,
    session_factory,
    member_service,
    transaction_service,
    bot_message_service,
):
    """Create a mock TransactionsClient for testing."""
    from apscheduler.schedulers.asyncio import AsyncIOScheduler

    from ledger_bot.clients.transactions_client import TransactionsClient
    from ledger_bot.services import Service

    scheduler = AsyncIOScheduler()

    service = Mock()
    service.member = member_service
    service.transaction = transaction_service
    service.bot_message = bot_message_service

    reminders = Mock()

    intents = discord.Intents.default()
    client = TransactionsClient(
        config=mock_config,
        scheduler=scheduler,
        service=service,
        reminders=reminders,
        session_factory=session_factory,
        intents=intents,
    )

    return client


@pytest.mark.asyncio
async def test_handle_transaction_reaction_invalid_emoji(mock_transactions_client):
    """Test that invalid emoji reactions are ignored."""
    payload = Mock()
    payload.emoji = Mock()
    payload.emoji.name = "❌"  # Not a valid transaction emoji
    payload.member = Mock()
    payload.channel_id = 123456

    mock_transactions_client.get_or_fetch_channel = AsyncMock(
        return_value=Mock(spec=discord.TextChannel)
    )

    result = await mock_transactions_client.handle_transaction_reaction(payload)

    assert result is False


@pytest.mark.asyncio
async def test_handle_transaction_reaction_wrong_channel(
    mock_transactions_client, mock_config
):
    """Test that reactions in excluded channels are ignored."""
    payload = Mock()
    payload.emoji = Mock()
    payload.emoji.name = mock_config.emojis.approval
    payload.member = Mock()
    payload.message_id = 123456
    payload.channel_id = 789012

    mock_channel = Mock(spec=discord.TextChannel)
    mock_channel.name = "excluded-channel"

    mock_transactions_client.get_or_fetch_channel = AsyncMock(return_value=mock_channel)
    mock_transactions_client.config.channels.include = ["wine-sales"]
    mock_transactions_client.service.member.get_or_add_member = AsyncMock(
        return_value=Mock()
    )

    result = await mock_transactions_client.handle_transaction_reaction(payload)

    assert result is False


@pytest.mark.asyncio
async def test_handle_transaction_reaction_no_transaction(
    mock_transactions_client, mock_config
):
    """Test that reactions on non-transaction messages are ignored."""
    payload = Mock()
    payload.emoji = Mock()
    payload.emoji.name = mock_config.emojis.approval
    payload.member = Mock()
    payload.member.username = "testuser"
    payload.message_id = 123456
    payload.channel_id = 789012

    mock_channel = Mock(spec=discord.TextChannel)
    mock_channel.name = "wine-sales"

    mock_transactions_client.get_or_fetch_channel = AsyncMock(return_value=mock_channel)
    mock_transactions_client.config.channels.include = ["wine-sales"]
    mock_transactions_client.service.member.get_or_add_member = AsyncMock(
        return_value=Mock()
    )
    mock_transactions_client.service.transaction.get_transaction_by_bot_message_id = (
        AsyncMock(return_value=None)
    )

    result = await mock_transactions_client.handle_transaction_reaction(payload)

    assert result is False


@pytest.mark.asyncio
@patch("ledger_bot.clients.transactions_client.add_reaction")
@patch("ledger_bot.clients.transactions_client.remove_reaction")
async def test_process_reaction_approval_success(
    mock_remove_reaction,
    mock_add_reaction,
    mock_transactions_client,
    sample_transaction,
    sample_buyer,
    sample_seller,
    mock_config,
):
    """Test successful approval reaction processing."""
    from ledger_bot.models import Member

    payload = Mock()
    payload.emoji = Mock()
    payload.emoji.name = mock_config.emojis.approval
    payload.message_id = 123456

    reactor = sample_buyer
    mock_channel = Mock(spec=discord.TextChannel)

    # Mock the service call
    mock_transactions_client.service.transaction.approve_transaction = AsyncMock(
        return_value=sample_transaction
    )

    with patch(
        "ledger_bot.clients.transactions_client.generate_transaction_status_message",
        new_callable=AsyncMock,
    ) as mock_generate:
        with patch(
            "ledger_bot.clients.transactions_client.send_message",
            new_callable=AsyncMock,
        ) as mock_send:
            mock_generate.return_value = "Transaction approved"

            result = await mock_transactions_client.process_reaction_approval(
                payload=payload,
                reactor=reactor,
                target_transaction=sample_transaction,
                buyer=sample_buyer,
                seller=sample_seller,
                channel=mock_channel,
            )

            assert result is True
            mock_transactions_client.service.transaction.approve_transaction.assert_called_once()


@pytest.mark.asyncio
@patch("ledger_bot.clients.transactions_client.remove_reaction")
async def test_process_reaction_approval_cancelled_transaction(
    mock_remove_reaction,
    mock_transactions_client,
    sample_buyer,
    sample_seller,
    mock_config,
):
    """Test approval reaction on cancelled transaction."""
    from ledger_bot.errors import TransactionCancelledError
    from ledger_bot.models import Transaction

    payload = Mock()
    payload.message_id = 123456

    cancelled_transaction = Mock(spec=Transaction)
    cancelled_transaction.cancelled = True

    mock_channel = Mock(spec=discord.TextChannel)

    # Mock the service to raise error
    mock_transactions_client.service.transaction.approve_transaction = AsyncMock(
        side_effect=TransactionCancelledError(transaction=cancelled_transaction)
    )

    result = await mock_transactions_client.process_reaction_approval(
        payload=payload,
        reactor=sample_buyer,
        target_transaction=cancelled_transaction,
        buyer=sample_buyer,
        seller=sample_seller,
        channel=mock_channel,
    )

    assert result is False


@pytest.mark.asyncio
async def test_refresh_transaction_not_found(mock_transactions_client):
    """Test refreshing non-existent transaction."""
    mock_transactions_client.service.transaction.get_transaction_by_display_id = (
        AsyncMock(return_value=None)
    )

    result = await mock_transactions_client.refresh_transaction(
        display_id=99999,
        channel_id=123456,
    )

    assert result == "No transaction found."


@pytest.mark.asyncio
async def test_refresh_transaction_success(
    mock_transactions_client,
    sample_transaction,
    sample_buyer,
    sample_seller,
):
    """Test successfully refreshing a transaction message."""
    mock_channel = Mock(spec=discord.TextChannel)
    mock_channel.fetch_message = AsyncMock()

    mock_transactions_client.get_or_fetch_channel = AsyncMock(return_value=mock_channel)
    mock_transactions_client.get_or_fetch_user = AsyncMock(
        side_effect=[sample_seller, sample_buyer]
    )
    mock_transactions_client.service.transaction.get_transaction_by_display_id = (
        AsyncMock(return_value=sample_transaction)
    )
    mock_transactions_client.service.bot_message.delete_bot_message = AsyncMock()

    # Mock the bot_messages as empty list
    sample_transaction.bot_messages = []
    sample_transaction.seller.discord_id = 111222333
    sample_transaction.buyer.discord_id = 999888777

    with patch(
        "ledger_bot.clients.transactions_client.generate_transaction_status_message",
        new_callable=AsyncMock,
    ) as mock_generate:
        with patch(
            "ledger_bot.clients.transactions_client.send_message",
            new_callable=AsyncMock,
        ) as mock_send:
            mock_generate.return_value = "Transaction status"

            result = await mock_transactions_client.refresh_transaction(
                display_id=sample_transaction.display_id,
                channel_id=123456,
            )

            assert result == "Successfully refreshed message."
            mock_send.assert_called_once()


@pytest.mark.asyncio
async def test_refresh_transaction_no_channel(
    mock_transactions_client, sample_transaction
):
    """Test refreshing transaction when no channel can be determined."""
    mock_transactions_client.service.transaction.get_transaction_by_display_id = (
        AsyncMock(return_value=sample_transaction)
    )
    mock_transactions_client.get_or_fetch_channel = AsyncMock(return_value=None)

    sample_transaction.bot_messages = []

    result = await mock_transactions_client.refresh_transaction(
        display_id=sample_transaction.display_id,
        channel_id=None,
    )

    assert "couldn't calculate which channel" in result
