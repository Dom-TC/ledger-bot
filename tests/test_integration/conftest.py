"""Pytest configuration specific to integration tests.

This conftest.py overrides fixtures from the parent conftest.py to provide
real service instances with database connections instead of mocks.
"""

import pytest_asyncio


@pytest_asyncio.fixture
async def member_service(db_session_factory, mock_config):
    """Override with real MemberService for integration tests."""
    from ledger_bot.services.member_service import MemberService
    from ledger_bot.storage.member_storage import MemberStorage

    storage = MemberStorage()
    return MemberService(storage, mock_config, db_session_factory)


@pytest_asyncio.fixture
async def transaction_service(db_session_factory, mock_config):
    """Override with real TransactionService for integration tests."""
    from ledger_bot.services.transaction_service import TransactionService
    from ledger_bot.storage.transaction_storage import TransactionStorage

    storage = TransactionStorage()
    return TransactionService(storage, mock_config, db_session_factory)


@pytest_asyncio.fixture
async def bot_message_service(db_session_factory, mock_config):
    """Override with real BotMessageService for integration tests."""
    from ledger_bot.services.bot_message_service import BotMessageService
    from ledger_bot.storage.bot_message_storage import BotMessageStorage

    storage = BotMessageStorage()
    return BotMessageService(storage, mock_config, db_session_factory)


@pytest_asyncio.fixture
async def currency_service(db_session_factory, mock_config):
    """Override with real CurrencyService for integration tests."""
    from ledger_bot.services.currency_service import CurrencyService
    from ledger_bot.storage.currency_storage import CurrencyStorage

    storage = CurrencyStorage()
    return CurrencyService(storage, mock_config, db_session_factory)
