"""Tests for generate_transaction_status_message."""

from unittest.mock import AsyncMock, Mock

import pytest

from ledger_bot.message_generators.generate_transaction_status_message import (
    generate_transaction_status_message,
)


@pytest.mark.asyncio
async def test_generate_new_sale_message(sample_transaction, mock_config):
    """Test generating message for a new sale."""
    mock_client = Mock()
    mock_seller = Mock()
    mock_seller.mention = "<@111222333>"
    mock_buyer = Mock()
    mock_buyer.mention = "<@999888777>"

    mock_client.get_or_fetch_user = AsyncMock(side_effect=[mock_seller, mock_buyer])

    message = await generate_transaction_status_message(
        transaction=sample_transaction,
        client=mock_client,
        config=mock_config,
        is_update=False,
    )

    assert "*New Sale Listed*" in message
    assert sample_transaction.wine in message
    assert "Approved:" in message
    assert "Paid:" in message
    assert "Delivered:" in message


@pytest.mark.asyncio
async def test_generate_updated_sale_message(sample_transaction, mock_config):
    """Test generating message for an updated sale."""
    mock_client = Mock()
    mock_seller = Mock()
    mock_seller.mention = "<@111222333>"
    mock_buyer = Mock()
    mock_buyer.mention = "<@999888777>"

    mock_client.get_or_fetch_user = AsyncMock(side_effect=[mock_seller, mock_buyer])

    message = await generate_transaction_status_message(
        transaction=sample_transaction,
        client=mock_client,
        config=mock_config,
        is_update=True,
    )

    assert "*Sale Updated*" in message


@pytest.mark.asyncio
async def test_generate_completed_sale_message(approved_transaction, mock_config):
    """Test generating message for a completed sale."""
    # Make transaction fully completed
    approved_transaction.buyer_paid = True
    approved_transaction.seller_paid = True
    approved_transaction.buyer_delivered = True
    approved_transaction.seller_delivered = True

    mock_client = Mock()
    mock_seller = Mock()
    mock_seller.mention = "<@111222333>"
    mock_buyer = Mock()
    mock_buyer.mention = "<@999888777>"

    mock_client.get_or_fetch_user = AsyncMock(side_effect=[mock_seller, mock_buyer])

    message = await generate_transaction_status_message(
        transaction=approved_transaction,
        client=mock_client,
        config=mock_config,
        is_update=True,
    )

    assert "*Sale Completed*" in message
    # Should not show reminder message for completed sales
    assert (
        mock_config.emojis.reminder not in message or "To set a reminder" not in message
    )


@pytest.mark.asyncio
async def test_generate_cancelled_sale_message(sample_transaction, mock_config):
    """Test generating message for a cancelled sale."""
    sample_transaction.cancelled = True

    mock_client = Mock()
    mock_seller = Mock()
    mock_seller.mention = "<@111222333>"
    mock_buyer = Mock()
    mock_buyer.mention = "<@999888777>"

    mock_client.get_or_fetch_user = AsyncMock(side_effect=[mock_seller, mock_buyer])

    message = await generate_transaction_status_message(
        transaction=sample_transaction,
        client=mock_client,
        config=mock_config,
        is_update=False,
    )

    assert "*Sale Cancelled*" in message
    assert mock_config.emojis.status_cancelled in message


@pytest.mark.asyncio
async def test_generate_message_unapproved_sale(sample_transaction, mock_config):
    """Test message for unapproved sale shows approval prompt."""
    mock_client = Mock()
    mock_seller = Mock()
    mock_seller.mention = "<@111222333>"
    mock_buyer = Mock()
    mock_buyer.mention = "<@999888777>"

    mock_client.get_or_fetch_user = AsyncMock(side_effect=[mock_seller, mock_buyer])

    message = await generate_transaction_status_message(
        transaction=sample_transaction,
        client=mock_client,
        config=mock_config,
        is_update=False,
    )

    assert mock_config.emojis.status_unconfirmed in message
    assert "please approve this sale" in message.lower()
    assert mock_config.emojis.approval in message


@pytest.mark.asyncio
async def test_generate_message_approved_sale(approved_transaction, mock_config):
    """Test message for approved sale shows confirmed status."""
    mock_client = Mock()
    mock_seller = Mock()
    mock_seller.mention = "<@111222333>"
    mock_buyer = Mock()
    mock_buyer.mention = "<@999888777>"

    mock_client.get_or_fetch_user = AsyncMock(side_effect=[mock_seller, mock_buyer])

    message = await generate_transaction_status_message(
        transaction=approved_transaction,
        client=mock_client,
        config=mock_config,
        is_update=False,
    )

    assert f"Approved: {mock_config.emojis.status_confirmed}" in message


@pytest.mark.asyncio
async def test_generate_message_buyer_paid(approved_transaction, mock_config):
    """Test message when only buyer marked as paid."""
    approved_transaction.buyer_paid = True
    approved_transaction.seller_paid = False

    mock_client = Mock()
    mock_seller = Mock()
    mock_seller.mention = "<@111222333>"
    mock_buyer = Mock()
    mock_buyer.mention = "<@999888777>"

    mock_client.get_or_fetch_user = AsyncMock(side_effect=[mock_seller, mock_buyer])

    message = await generate_transaction_status_message(
        transaction=approved_transaction,
        client=mock_client,
        config=mock_config,
        is_update=True,
    )

    assert mock_config.emojis.status_part_confirmed in message
    assert mock_seller.mention in message


@pytest.mark.asyncio
async def test_generate_message_both_paid(approved_transaction, mock_config):
    """Test message when both parties marked as paid."""
    approved_transaction.buyer_paid = True
    approved_transaction.seller_paid = True

    mock_client = Mock()
    mock_seller = Mock()
    mock_seller.mention = "<@111222333>"
    mock_buyer = Mock()
    mock_buyer.mention = "<@999888777>"

    mock_client.get_or_fetch_user = AsyncMock(side_effect=[mock_seller, mock_buyer])

    message = await generate_transaction_status_message(
        transaction=approved_transaction,
        client=mock_client,
        config=mock_config,
        is_update=True,
    )

    assert f"Paid:           {mock_config.emojis.status_confirmed}" in message


@pytest.mark.asyncio
async def test_generate_message_buyer_delivered(approved_transaction, mock_config):
    """Test message when only buyer marked as delivered."""
    approved_transaction.buyer_delivered = True
    approved_transaction.seller_delivered = False

    mock_client = Mock()
    mock_seller = Mock()
    mock_seller.mention = "<@111222333>"
    mock_buyer = Mock()
    mock_buyer.mention = "<@999888777>"

    mock_client.get_or_fetch_user = AsyncMock(side_effect=[mock_seller, mock_buyer])

    message = await generate_transaction_status_message(
        transaction=approved_transaction,
        client=mock_client,
        config=mock_config,
        is_update=True,
    )

    assert mock_config.emojis.status_part_confirmed in message
    assert "delivered" in message.lower()


@pytest.mark.asyncio
async def test_generate_message_includes_price(sample_transaction, mock_config):
    """Test message includes price with currency symbol."""
    mock_client = Mock()
    mock_seller = Mock()
    mock_seller.mention = "<@111222333>"
    mock_buyer = Mock()
    mock_buyer.mention = "<@999888777>"

    mock_client.get_or_fetch_user = AsyncMock(side_effect=[mock_seller, mock_buyer])

    message = await generate_transaction_status_message(
        transaction=sample_transaction,
        client=mock_client,
        config=mock_config,
        is_update=False,
    )

    assert sample_transaction.currency.symbol in message
    assert "99.99" in message


@pytest.mark.asyncio
async def test_generate_message_includes_cancel_option(sample_transaction, mock_config):
    """Test message includes cancel option for unapproved sales."""
    mock_client = Mock()
    mock_seller = Mock()
    mock_seller.mention = "<@111222333>"
    mock_buyer = Mock()
    mock_buyer.mention = "<@999888777>"

    mock_client.get_or_fetch_user = AsyncMock(side_effect=[mock_seller, mock_buyer])

    message = await generate_transaction_status_message(
        transaction=sample_transaction,
        client=mock_client,
        config=mock_config,
        is_update=False,
    )

    assert "cancel" in message.lower()
    assert mock_config.emojis.cancel in message


@pytest.mark.asyncio
async def test_generate_message_includes_reminder_option(
    sample_transaction, mock_config
):
    """Test message includes reminder option for active sales."""
    mock_client = Mock()
    mock_seller = Mock()
    mock_seller.mention = "<@111222333>"
    mock_buyer = Mock()
    mock_buyer.mention = "<@999888777>"

    mock_client.get_or_fetch_user = AsyncMock(side_effect=[mock_seller, mock_buyer])

    message = await generate_transaction_status_message(
        transaction=sample_transaction,
        client=mock_client,
        config=mock_config,
        is_update=False,
    )

    assert mock_config.emojis.reminder in message
    assert "reminder" in message.lower()


@pytest.mark.asyncio
async def test_generate_message_includes_transaction_id(
    sample_transaction, mock_config
):
    """Test message includes transaction ID in footer."""
    mock_client = Mock()
    mock_seller = Mock()
    mock_seller.mention = "<@111222333>"
    mock_buyer = Mock()
    mock_buyer.mention = "<@999888777>"

    mock_client.get_or_fetch_user = AsyncMock(side_effect=[mock_seller, mock_buyer])

    message = await generate_transaction_status_message(
        transaction=sample_transaction,
        client=mock_client,
        config=mock_config,
        is_update=False,
    )

    assert str(sample_transaction.id) in message
