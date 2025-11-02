"""Tests for generate_list_message."""

from unittest.mock import Mock

import pytest

from ledger_bot.message_generators.generate_list_message import (
    _build_transaction_lists,
    _get_latest_message_link,
    generate_list_message,
)


@pytest.mark.asyncio
async def test_generate_list_message_empty(member_service):
    """Test generating list with no transactions."""
    result = await generate_list_message([], 123456789, member_service)

    assert isinstance(result, list)
    assert len(result) >= 1
    assert "don't have any transactions" in result[0]


@pytest.mark.asyncio
async def test_generate_list_message_with_transactions(
    sample_transaction, sample_buyer, sample_bot_message, member_service
):
    """Test generating list with transactions."""
    result = await generate_list_message(
        [sample_transaction],
        sample_buyer.discord_id,
        member_service,
    )

    assert isinstance(result, list)
    assert len(result) >= 1
    # Should contain wine name
    assert sample_transaction.wine in result[0]


@pytest.mark.asyncio
async def test_get_latest_message_link_with_message(
    sample_transaction, sample_bot_message
):
    """Test generating Discord link from bot message."""
    link = await _get_latest_message_link(sample_transaction)

    assert "https://discord.com/channels/" in link
    assert str(sample_bot_message.guild_id) in link
    assert str(sample_bot_message.channel_id) in link
    assert str(sample_bot_message.message_id) in link


@pytest.mark.asyncio
async def test_get_latest_message_link_no_message(
    sample_buyer, sample_seller, sample_currency, bot_id
):
    """Test generating link when transaction has no bot messages."""
    from ledger_bot.models import Transaction

    transaction = Transaction(
        wine="Test Wine",
        price=50.0,
        seller_id=sample_seller.id,
        buyer_id=sample_buyer.id,
        bot_id=bot_id,
        currency_code=sample_currency.code,
    )

    link = await _get_latest_message_link(transaction)
    assert link == ""


@pytest.mark.asyncio
async def test_build_transaction_lists_buyer_perspective(
    sample_transaction, sample_buyer, member_service
):
    """Test building transaction lists from buyer's perspective."""
    lists = await _build_transaction_lists(
        [sample_transaction],
        sample_buyer.discord_id,
        member_service,
    )

    assert "buying" in lists
    assert "selling" in lists
    # Transaction should be in buying list
    assert len(lists["buying"]["awaiting_approval"]) >= 1


@pytest.mark.asyncio
async def test_build_transaction_lists_seller_perspective(
    sample_transaction, sample_seller, member_service
):
    """Test building transaction lists from seller's perspective."""
    lists = await _build_transaction_lists(
        [sample_transaction],
        sample_seller.discord_id,
        member_service,
    )

    # Transaction should be in selling list
    assert len(lists["selling"]["awaiting_approval"]) >= 1


@pytest.mark.asyncio
async def test_build_transaction_lists_approved_transaction(
    approved_transaction, sample_buyer, member_service
):
    """Test that approved transactions are in correct category."""
    lists = await _build_transaction_lists(
        [approved_transaction],
        sample_buyer.discord_id,
        member_service,
    )

    # Should be in awaiting_payment_and_delivery
    assert len(lists["buying"]["awaiting_payment_and_delivery"]) >= 1


@pytest.mark.asyncio
async def test_build_transaction_lists_cancelled(
    sample_buyer, sample_seller, sample_currency, bot_id, member_service
):
    """Test that cancelled transactions are categorized correctly."""
    from unittest.mock import Mock

    from ledger_bot.models import Transaction

    cancelled = Mock(spec=Transaction)
    cancelled.id = 3
    cancelled.display_id = 102
    cancelled.wine = "Cancelled Wine"
    cancelled.price = 50.0
    cancelled.seller_id = sample_seller.id
    cancelled.buyer_id = sample_buyer.id
    cancelled.seller = sample_seller
    cancelled.buyer = sample_buyer
    cancelled.currency_code = sample_currency.code
    cancelled.currency = sample_currency
    cancelled.bot_id = bot_id
    cancelled.cancelled = True
    cancelled.sale_approved = False
    cancelled.buyer_paid = False
    cancelled.seller_paid = False
    cancelled.buyer_delivered = False
    cancelled.seller_delivered = False
    cancelled.bot_messages = []

    lists = await _build_transaction_lists(
        [cancelled],
        sample_buyer.discord_id,
        member_service,
    )

    assert len(lists["buying"]["cancelled"]) >= 1


@pytest.mark.asyncio
async def test_build_transaction_lists_completed(
    sample_buyer, sample_seller, sample_currency, bot_id, member_service
):
    """Test that completed transactions are categorized correctly."""
    from unittest.mock import Mock

    from ledger_bot.models import Transaction

    completed = Mock(spec=Transaction)
    completed.id = 4
    completed.display_id = 103
    completed.wine = "Completed Wine"
    completed.price = 100.0
    completed.seller_id = sample_seller.id
    completed.buyer_id = sample_buyer.id
    completed.seller = sample_seller
    completed.buyer = sample_buyer
    completed.currency_code = sample_currency.code
    completed.currency = sample_currency
    completed.bot_id = bot_id
    completed.cancelled = False
    completed.sale_approved = True
    completed.buyer_paid = True
    completed.seller_paid = True
    completed.buyer_delivered = True
    completed.seller_delivered = True
    completed.bot_messages = []

    lists = await _build_transaction_lists(
        [completed],
        sample_buyer.discord_id,
        member_service,
    )

    assert len(lists["buying"]["completed"]) >= 1


@pytest.mark.asyncio
async def test_generate_list_message_multiple_transactions(
    sample_transaction, approved_transaction, sample_buyer, member_service
):
    """Test generating list with multiple transactions."""
    result = await generate_list_message(
        [sample_transaction, approved_transaction],
        sample_buyer.discord_id,
        member_service,
    )

    assert isinstance(result, list)
    # Should mention both wines
    combined = "".join(result)
    assert sample_transaction.wine in combined
    assert approved_transaction.wine in combined


@pytest.mark.asyncio
async def test_generate_list_message_includes_price(
    sample_transaction, sample_buyer, member_service
):
    """Test that list message includes price and currency."""
    result = await generate_list_message(
        [sample_transaction],
        sample_buyer.discord_id,
        member_service,
    )

    combined = "".join(result)
    # Should contain price formatted to 2dp
    assert "99.99" in combined
    # Should contain currency symbol
    assert sample_transaction.currency.symbol in combined


@pytest.mark.asyncio
async def test_generate_list_message_mentions_users(
    sample_transaction, sample_buyer, sample_seller, member_service
):
    """Test that list message includes user mentions."""
    result = await generate_list_message(
        [sample_transaction],
        sample_buyer.discord_id,
        member_service,
    )

    combined = "".join(result)
    # Should mention the seller (other party)
    assert f"<@{sample_seller.discord_id}>" in combined
