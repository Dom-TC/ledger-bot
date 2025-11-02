"""Tests for send_message."""

from unittest.mock import AsyncMock, Mock, patch

import discord
import pytest

from ledger_bot.message_generators.send_message import send_message


@pytest.mark.asyncio
async def test_send_message_success(sample_transaction, mock_config):
    """Test successfully sending a message."""
    mock_channel = Mock()
    mock_sent_message = Mock()
    mock_sent_message.id = 987654321
    mock_channel.send = AsyncMock(return_value=mock_sent_message)

    mock_service = Mock()
    mock_service.bot_message.save_transaction_bot_message = AsyncMock()

    await send_message(
        response_contents="Test message",
        channel=mock_channel,
        target_transaction=sample_transaction,
        previous_message_id=None,
        service=mock_service,
        config=mock_config,
    )

    mock_channel.send.assert_called_once_with("Test message")
    mock_service.bot_message.save_transaction_bot_message.assert_called_once_with(
        message=mock_sent_message, transaction=sample_transaction
    )


@pytest.mark.asyncio
async def test_send_message_forbidden_error(sample_transaction, mock_config):
    """Test handling Forbidden error when sending message."""
    mock_channel = Mock()
    mock_channel.send = AsyncMock(side_effect=discord.Forbidden(Mock(), "forbidden"))

    mock_service = Mock()
    mock_service.bot_message.save_transaction_bot_message = AsyncMock()

    # Should not raise, just log error
    await send_message(
        response_contents="Test message",
        channel=mock_channel,
        target_transaction=sample_transaction,
        previous_message_id=None,
        service=mock_service,
        config=mock_config,
    )

    mock_channel.send.assert_called_once()
    mock_service.bot_message.save_transaction_bot_message.assert_not_called()


@pytest.mark.asyncio
async def test_send_message_http_exception(sample_transaction, mock_config):
    """Test handling HTTPException when sending message."""
    mock_channel = Mock()
    mock_channel.send = AsyncMock(
        side_effect=discord.HTTPException(Mock(), "http error")
    )

    mock_service = Mock()
    mock_service.bot_message.save_transaction_bot_message = AsyncMock()

    await send_message(
        response_contents="Test message",
        channel=mock_channel,
        target_transaction=sample_transaction,
        previous_message_id=None,
        service=mock_service,
        config=mock_config,
    )

    mock_channel.send.assert_called_once()
    mock_service.bot_message.save_transaction_bot_message.assert_not_called()


@pytest.mark.asyncio
async def test_send_message_deletes_previous_when_configured(
    sample_transaction, mock_config
):
    """Test deleting previous message when delete_previous_bot_messages is True."""
    mock_config.delete_previous_bot_messages = True

    mock_channel = Mock()
    mock_sent_message = Mock()
    mock_channel.send = AsyncMock(return_value=mock_sent_message)

    mock_old_message = Mock()
    mock_old_message.delete = AsyncMock()
    mock_channel.fetch_message = AsyncMock(return_value=mock_old_message)

    mock_previous_bot_message = Mock()
    mock_service = Mock()
    mock_service.bot_message.save_transaction_bot_message = AsyncMock()
    mock_service.bot_message.get_bot_message_by_message_id = AsyncMock(
        return_value=mock_previous_bot_message
    )
    mock_service.bot_message.delete_bot_message = AsyncMock()

    await send_message(
        response_contents="Test message",
        channel=mock_channel,
        target_transaction=sample_transaction,
        previous_message_id=123456789,
        service=mock_service,
        config=mock_config,
    )

    mock_channel.fetch_message.assert_called_once_with(123456789)
    mock_old_message.delete.assert_called_once()
    mock_service.bot_message.get_bot_message_by_message_id.assert_called_once_with(
        123456789
    )
    mock_service.bot_message.delete_bot_message.assert_called_once_with(
        mock_previous_bot_message
    )


@pytest.mark.asyncio
async def test_send_message_does_not_delete_when_not_configured(
    sample_transaction, mock_config
):
    """Test not deleting previous message when delete_previous_bot_messages is False."""
    mock_config.delete_previous_bot_messages = False

    mock_channel = Mock()
    mock_sent_message = Mock()
    mock_channel.send = AsyncMock(return_value=mock_sent_message)
    mock_channel.fetch_message = AsyncMock()

    mock_service = Mock()
    mock_service.bot_message.save_transaction_bot_message = AsyncMock()

    await send_message(
        response_contents="Test message",
        channel=mock_channel,
        target_transaction=sample_transaction,
        previous_message_id=123456789,
        service=mock_service,
        config=mock_config,
    )

    mock_channel.fetch_message.assert_not_called()


@pytest.mark.asyncio
async def test_send_message_does_not_delete_when_no_previous_id(
    sample_transaction, mock_config
):
    """Test not deleting when previous_message_id is None."""
    mock_config.delete_previous_bot_messages = True

    mock_channel = Mock()
    mock_sent_message = Mock()
    mock_channel.send = AsyncMock(return_value=mock_sent_message)
    mock_channel.fetch_message = AsyncMock()

    mock_service = Mock()
    mock_service.bot_message.save_transaction_bot_message = AsyncMock()

    await send_message(
        response_contents="Test message",
        channel=mock_channel,
        target_transaction=sample_transaction,
        previous_message_id=None,
        service=mock_service,
        config=mock_config,
    )

    mock_channel.fetch_message.assert_not_called()


@pytest.mark.asyncio
async def test_send_message_handles_delete_forbidden(sample_transaction, mock_config):
    """Test handling Forbidden error when deleting previous message."""
    mock_config.delete_previous_bot_messages = True

    mock_channel = Mock()
    mock_sent_message = Mock()
    mock_channel.send = AsyncMock(return_value=mock_sent_message)

    mock_old_message = Mock()
    mock_old_message.delete = AsyncMock(
        side_effect=discord.Forbidden(Mock(), "forbidden")
    )
    mock_channel.fetch_message = AsyncMock(return_value=mock_old_message)

    mock_service = Mock()
    mock_service.bot_message.save_transaction_bot_message = AsyncMock()

    # Should not raise, just log error
    await send_message(
        response_contents="Test message",
        channel=mock_channel,
        target_transaction=sample_transaction,
        previous_message_id=123456789,
        service=mock_service,
        config=mock_config,
    )

    mock_old_message.delete.assert_called_once()


@pytest.mark.asyncio
async def test_send_message_handles_delete_not_found(sample_transaction, mock_config):
    """Test handling NotFound error when deleting previous message."""
    mock_config.delete_previous_bot_messages = True

    mock_channel = Mock()
    mock_sent_message = Mock()
    mock_channel.send = AsyncMock(return_value=mock_sent_message)

    mock_old_message = Mock()
    mock_old_message.delete = AsyncMock(
        side_effect=discord.NotFound(Mock(), "not found")
    )
    mock_channel.fetch_message = AsyncMock(return_value=mock_old_message)

    mock_service = Mock()
    mock_service.bot_message.save_transaction_bot_message = AsyncMock()

    await send_message(
        response_contents="Test message",
        channel=mock_channel,
        target_transaction=sample_transaction,
        previous_message_id=123456789,
        service=mock_service,
        config=mock_config,
    )

    mock_old_message.delete.assert_called_once()


@pytest.mark.asyncio
async def test_send_message_handles_delete_http_exception(
    sample_transaction, mock_config
):
    """Test handling HTTPException when deleting previous message."""
    mock_config.delete_previous_bot_messages = True

    mock_channel = Mock()
    mock_sent_message = Mock()
    mock_channel.send = AsyncMock(return_value=mock_sent_message)

    mock_old_message = Mock()
    mock_old_message.delete = AsyncMock(
        side_effect=discord.HTTPException(Mock(), "http error")
    )
    mock_channel.fetch_message = AsyncMock(return_value=mock_old_message)

    mock_service = Mock()
    mock_service.bot_message.save_transaction_bot_message = AsyncMock()

    await send_message(
        response_contents="Test message",
        channel=mock_channel,
        target_transaction=sample_transaction,
        previous_message_id=123456789,
        service=mock_service,
        config=mock_config,
    )

    mock_old_message.delete.assert_called_once()


@pytest.mark.asyncio
async def test_send_message_handles_delete_record_not_found(
    sample_transaction, mock_config
):
    """Test handling when previous bot message record is not found."""
    mock_config.delete_previous_bot_messages = True

    mock_channel = Mock()
    mock_sent_message = Mock()
    mock_channel.send = AsyncMock(return_value=mock_sent_message)

    mock_old_message = Mock()
    mock_old_message.delete = AsyncMock()
    mock_channel.fetch_message = AsyncMock(return_value=mock_old_message)

    mock_service = Mock()
    mock_service.bot_message.save_transaction_bot_message = AsyncMock()
    mock_service.bot_message.get_bot_message_by_message_id = AsyncMock(
        return_value=None
    )
    mock_service.bot_message.delete_bot_message = AsyncMock()

    await send_message(
        response_contents="Test message",
        channel=mock_channel,
        target_transaction=sample_transaction,
        previous_message_id=123456789,
        service=mock_service,
        config=mock_config,
    )

    mock_old_message.delete.assert_called_once()
    # Should not attempt to delete database record if not found
    mock_service.bot_message.delete_bot_message.assert_not_called()
