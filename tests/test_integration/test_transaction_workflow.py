"""Integration tests for full transaction workflows."""

from datetime import datetime, timezone

import pytest

from ledger_bot.models import Transaction


@pytest.mark.asyncio
async def test_complete_transaction_workflow(
    transaction_service,
    member_service,
    bot_message_service,
    sample_buyer,
    sample_seller,
    sample_currency,
    bot_id,
):
    """Test a complete transaction workflow from creation to completion."""
    # Step 1: Create transaction
    transaction = Transaction(
        wine="Integration Test Wine 2020",
        price=125.50,
        seller_id=sample_seller.id,
        buyer_id=sample_buyer.id,
        sale_approved=False,
        buyer_delivered=False,
        seller_delivered=False,
        buyer_paid=False,
        seller_paid=False,
        cancelled=False,
        bot_id=bot_id,
        currency_code=sample_currency.code,
    )

    saved_transaction = await transaction_service.save_transaction(transaction)
    assert saved_transaction.id is not None
    assert not saved_transaction.sale_approved

    # Step 2: Buyer approves transaction
    approved = await transaction_service.approve_transaction(
        saved_transaction,
        sample_buyer,
    )
    assert approved.sale_approved
    assert approved.approved_date is not None

    # Step 3: Buyer marks as paid
    buyer_paid = await transaction_service.mark_transaction_paid(
        approved,
        sample_buyer,
    )
    assert buyer_paid.buyer_paid
    assert buyer_paid.paid_date is None  # Not set until both mark it

    # Step 4: Seller marks as paid
    both_paid = await transaction_service.mark_transaction_paid(
        buyer_paid,
        sample_seller,
    )
    assert both_paid.buyer_paid
    assert both_paid.seller_paid
    assert both_paid.paid_date is not None

    # Step 5: Buyer marks as delivered
    buyer_delivered = await transaction_service.mark_transaction_delivered(
        both_paid,
        sample_buyer,
    )
    assert buyer_delivered.buyer_delivered
    assert buyer_delivered.delivered_date is None  # Not set until both mark it

    # Step 6: Seller marks as delivered
    completed = await transaction_service.mark_transaction_delivered(
        buyer_delivered,
        sample_seller,
    )
    assert completed.buyer_delivered
    assert completed.seller_delivered
    assert completed.delivered_date is not None

    # Verify transaction is fully completed
    assert completed.sale_approved
    assert completed.buyer_paid
    assert completed.seller_paid
    assert completed.buyer_delivered
    assert completed.seller_delivered
    assert not completed.cancelled


@pytest.mark.asyncio
async def test_transaction_cancellation_workflow(
    transaction_service,
    sample_buyer,
    sample_seller,
    sample_currency,
    bot_id,
):
    """Test cancelling a transaction before approval."""
    # Create unapproved transaction
    transaction = Transaction(
        wine="To Be Cancelled",
        price=50.0,
        seller_id=sample_seller.id,
        buyer_id=sample_buyer.id,
        bot_id=bot_id,
        currency_code=sample_currency.code,
    )

    saved = await transaction_service.save_transaction(transaction)

    # Seller cancels
    cancelled = await transaction_service.cancel_transaction(
        saved,
        sample_seller,
    )

    assert cancelled.cancelled
    assert cancelled.cancelled_date is not None
    assert not cancelled.sale_approved


@pytest.mark.asyncio
async def test_member_creation_and_transaction_workflow(
    member_service,
    transaction_service,
    mock_discord_seller,
    mock_discord_buyer,
    sample_currency,
):
    """Test creating members and then a transaction between them."""
    # Step 1: Create/get members
    seller = await member_service.get_or_add_member(mock_discord_seller)
    buyer = await member_service.get_or_add_member(mock_discord_buyer)

    assert seller.id is not None
    assert buyer.id is not None
    assert seller.discord_id == mock_discord_seller.id
    assert buyer.discord_id == mock_discord_buyer.id

    # Step 2: Create transaction between them
    transaction = Transaction(
        wine="Member Integration Wine",
        price=99.99,
        seller_id=seller.id,
        buyer_id=buyer.id,
        currency_code=sample_currency.code,
    )

    saved = await transaction_service.save_transaction(transaction)

    assert saved.id is not None
    assert saved.seller_id == seller.id
    assert saved.buyer_id == buyer.id

    # Step 3: Verify transaction relationships
    from sqlalchemy.orm import selectinload

    from ledger_bot.models import Transaction as TransactionModel

    refreshed = await transaction_service.get_transaction(
        saved.id,
        options=[
            selectinload(TransactionModel.buyer),
            selectinload(TransactionModel.seller),
        ],
    )

    assert refreshed.buyer.username == buyer.username
    assert refreshed.seller.username == seller.username


@pytest.mark.asyncio
async def test_transaction_with_bot_message_workflow(
    transaction_service,
    bot_message_service,
    sample_buyer,
    sample_seller,
    sample_currency,
):
    """Test creating transaction and saving bot message."""
    from unittest.mock import Mock

    # Create transaction
    transaction = Transaction(
        wine="Message Test Wine",
        price=75.0,
        seller_id=sample_seller.id,
        buyer_id=sample_buyer.id,
        currency_code=sample_currency.code,
    )

    saved_transaction = await transaction_service.save_transaction(transaction)

    # Create mock Discord message
    mock_message = Mock()
    mock_message.id = 123456789
    mock_message.channel = Mock()
    mock_message.channel.id = 987654321
    mock_message.guild = Mock()
    mock_message.guild.id = 111222333

    # Save bot message linked to transaction
    bot_message = await bot_message_service.save_transaction_bot_message(
        mock_message,
        saved_transaction,
    )

    assert bot_message.id is not None
    assert bot_message.transaction_id == saved_transaction.id
    assert bot_message.message_id == mock_message.id

    # Verify we can retrieve bot message by message id
    retrieved_bot_message = await bot_message_service.get_bot_message_by_message_id(
        mock_message.id
    )

    assert retrieved_bot_message is not None
    assert retrieved_bot_message.transaction_id == saved_transaction.id


@pytest.mark.asyncio
async def test_multiple_transactions_workflow(
    transaction_service,
    member_service,
    sample_buyer,
    sample_seller,
    sample_currency,
):
    """Test creating and managing multiple transactions."""
    # Create 3 transactions with different states
    transactions_data = [
        ("Wine 1", 50.0, False, False, False),
        ("Wine 2", 75.0, True, False, False),
        ("Wine 3", 100.0, True, True, True),
    ]

    created_transactions = []

    for wine, price, approved, paid, delivered in transactions_data:
        transaction = Transaction(
            wine=wine,
            price=price,
            seller_id=sample_seller.id,
            buyer_id=sample_buyer.id,
            sale_approved=approved,
            buyer_paid=paid,
            seller_paid=paid,
            buyer_delivered=delivered,
            seller_delivered=delivered,
            currency_code=sample_currency.code,
        )

        if approved:
            transaction.approved_date = datetime.now(timezone.utc)
        if paid:
            transaction.paid_date = datetime.now(timezone.utc)
        if delivered:
            transaction.delivered_date = datetime.now(timezone.utc)

        saved = await transaction_service.save_transaction(transaction)
        created_transactions.append(saved)

    # Verify all transactions were created
    assert len(created_transactions) == 3

    # Get all transactions
    all_transactions = await transaction_service.list_all_transactions()
    assert len(all_transactions) >= 3

    # Get completed transactions
    completed = await transaction_service.get_completed_transaction()
    completed_ids = [t.id for t in completed]
    assert created_transactions[2].id in completed_ids  # Wine 3 should be completed


@pytest.mark.asyncio
async def test_transaction_summary_workflow(
    transaction_service,
    member_service,
    sample_buyer,
    sample_seller,
    sample_currency,
):
    """Test getting member transaction summary after various operations."""
    # Create some transactions for the seller
    for i in range(3):
        transaction = Transaction(
            wine=f"Summary Test Wine {i}",
            price=float(i * 25),
            seller_id=sample_seller.id,
            buyer_id=sample_buyer.id,
            currency_code=sample_currency.code,
        )
        await transaction_service.save_transaction(transaction)

    # Get seller's transaction summary
    summary = await member_service.get_member_transaction_summary(sample_seller)

    assert summary is not None
    assert summary.sales_count >= 3
    assert summary.purchases_count == 0  # Seller hasn't bought anything
    assert summary.open_count >= 3  # All unapproved transactions are open


@pytest.mark.asyncio
async def test_alternate_currency_workflow(
    transaction_service,
    currency_service,
    sample_buyer,
    sample_seller,
    mock_config,
    mocker,
):
    """Test creating transaction with non-GBP currency."""
    # Mock the requests.get call to avoid real API calls
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"result": "success", "conversion_rate": 1.25}
    mocker.patch("requests.get", return_value=mock_response)

    # Create USD currency
    usd = await currency_service.get_or_add_currency("USD")
    assert usd.code == "USD"

    # Create transaction in USD
    transaction = Transaction(
        wine="USD Wine",
        price=100.0,
        seller_id=sample_seller.id,
        buyer_id=sample_buyer.id,
        currency_code=usd.code,
    )

    saved = await transaction_service.save_transaction(transaction)

    assert saved.currency_code == "USD"
    assert saved.price == 100.0

    # Verify currency relationship works
    assert saved.currency.code == "USD"
    assert saved.currency.symbol == "$"
