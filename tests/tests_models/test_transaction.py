"""Tests for Transaction model."""

import pytest

from ledger_bot.models.currency import Currency
from ledger_bot.models.transaction import Transaction


class TestTransaction:
    """Test Transaction model."""

    def test_transaction_gbp_price_with_gbp_currency(self):
        """Test gbp_price property when currency is GBP."""
        transaction = Transaction()
        transaction.wine = "Test Wine"
        transaction.price = 50.0
        transaction.currency_code = "GBP"
        transaction.seller_id = 1
        transaction.buyer_id = 2
        transaction.bot_id = "test_bot"

        # When currency is GBP, gbp_price should equal price
        assert transaction.gbp_price == 50.0

    def test_transaction_gbp_price_with_conversion_rate(self):
        """Test gbp_price property with currency conversion rate."""
        # Create currency with conversion rate
        currency = Currency()
        currency.code = "USD"
        currency.symbol = "$"
        currency.rate = 0.79  # 1 USD = 0.79 GBP

        transaction = Transaction()
        transaction.wine = "Test Wine"
        transaction.price = 100.0
        transaction.currency_code = "USD"
        transaction.currency = currency
        transaction.seller_id = 1
        transaction.buyer_id = 2
        transaction.bot_id = "test_bot"

        # Price should be converted: 100 * 0.79 = 79.0
        assert transaction.gbp_price == 79.0

    def test_transaction_gbp_price_with_no_conversion_rate(self):
        """Test gbp_price property when currency has no conversion rate."""
        # Create currency without conversion rate
        currency = Currency()
        currency.code = "EUR"
        currency.symbol = "€"
        currency.rate = None

        transaction = Transaction()
        transaction.wine = "Test Wine"
        transaction.price = 100.0
        transaction.currency_code = "EUR"
        transaction.currency = currency
        transaction.seller_id = 1
        transaction.buyer_id = 2
        transaction.bot_id = "test_bot"

        # When rate is None, should return original price
        assert transaction.gbp_price == 100.0

    def test_transaction_gbp_price_with_zero_rate(self):
        """Test gbp_price property when currency has zero conversion rate."""
        # Create currency with zero rate
        currency = Currency()
        currency.code = "YEN"
        currency.symbol = "¥"
        currency.rate = 0.0

        transaction = Transaction()
        transaction.wine = "Test Wine"
        transaction.price = 1000.0
        transaction.currency_code = "YEN"
        transaction.currency = currency
        transaction.seller_id = 1
        transaction.buyer_id = 2
        transaction.bot_id = "test_bot"

        # When rate is 0 (falsy), should return original price (same as None)
        assert transaction.gbp_price == 1000.0
