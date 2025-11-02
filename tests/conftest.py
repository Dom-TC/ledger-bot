"""Pytest configuration and fixtures for all tests."""

import logging
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from tests.discord_mocks import (
    MockDMChannel,
    MockGuild,
    MockMember,
    MockMessage,
    MockRole,
    MockTextChannel,
    MockUser,
)


def pytest_configure(config):
    """
    Configure pytest before running tests.

    This hook is called once at the start of the test session, before any
    tests are collected or run. It's the ideal place for global test setup.
    """
    # Suppress logging output during tests to prevent screen clutter
    # Only show CRITICAL level logs (errors will still be visible)
    for logger in logging.Logger.manager.loggerDict.values():
        # Some entries might be PlaceHolder objects, not actual loggers
        if not isinstance(logger, logging.Logger):
            continue

        logger.setLevel(logging.CRITICAL)


# Discord Mock Fixtures
# These fixtures provide fresh mock Discord objects for each test


@pytest.fixture
def mock_guild():
    """Provide a mock Discord Guild."""
    return MockGuild()


@pytest.fixture
def mock_role():
    """Provide a mock Discord Role."""
    return MockRole()


@pytest.fixture
def mock_member():
    """Provide a mock Discord Member."""
    return MockMember()


@pytest.fixture
def mock_user():
    """Provide a mock Discord User."""
    return MockUser()


@pytest.fixture
def mock_text_channel():
    """Provide a mock Discord TextChannel."""
    return MockTextChannel()


@pytest.fixture
def mock_dm_channel():
    """Provide a mock Discord DMChannel."""
    return MockDMChannel()


@pytest.fixture
def mock_message():
    """Provide a mock Discord Message."""
    return MockMessage()


# Factory Fixtures
# These fixtures return factory functions for creating multiple instances


@pytest.fixture
def guild_factory():
    """Provide a factory function for creating MockGuild instances."""

    def _create_guild(**kwargs):
        return MockGuild(**kwargs)

    return _create_guild


@pytest.fixture
def member_factory():
    """Provide a factory function for creating MockMember instances."""

    def _create_member(**kwargs):
        return MockMember(**kwargs)

    return _create_member


@pytest.fixture
def role_factory():
    """Provide a factory function for creating MockRole instances."""

    def _create_role(**kwargs):
        return MockRole(**kwargs)

    return _create_role


@pytest.fixture
def message_factory():
    """Provide a factory function for creating MockMessage instances."""

    def _create_message(**kwargs):
        return MockMessage(**kwargs)

    return _create_message


# Database and Service Fixtures


@pytest.fixture
def mock_config():
    """Provide a mock Config for testing."""
    from ledger_bot.core.config import (
        AuthenticationConfig,
        ChannelsConfig,
        Config,
        EmojiConfig,
        JobSchedule,
    )

    return Config(
        authentication=AuthenticationConfig(
            discord="test_token",
            airtable_key="test_key",
            airtable_base="test_base",
            exchangerate_api="test_api",
        ),
        emojis=EmojiConfig(
            approval="👍",
            cancel="👎",
            paid="💸",
            delivered="🚚",
            reminder="🔔",
            thinking="⏳",
            unknown_version="❓",
            status_confirmed="✅",
            status_unconfirmed="❌",
            status_part_confirmed="⚠️",
            status_cancelled="🚫",
        ),
        channels=ChannelsConfig(include=["wine-sales"], exclude=[]),
        admin_role=111222333,
        maintainer_ids=[123456789],
        run_cleanup_time=JobSchedule(hour=3, minute=0, second=0),
        reaction_role_refresh_time=JobSchedule(hour=4, minute=0, second=0),
        name="Test Bot",
        delete_previous_bot_messages=False,
    )


@pytest_asyncio.fixture
async def db_session():
    """Provide an in-memory async database session for testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    from ledger_bot.models.base import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest.fixture
def session_factory():
    """Provide a mock session factory for testing."""
    # Create a mock that supports async context manager protocol
    mock_result = Mock()
    mock_result.scalar_one_or_none = Mock(return_value="test_version")

    mock_session = Mock()
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.commit = AsyncMock()

    mock_factory = Mock()
    mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_factory.return_value.__aexit__ = AsyncMock()

    return mock_factory


@pytest.fixture
def member_service():
    """Provide a mock MemberService for testing."""
    service = Mock()
    service.get_or_add_member = AsyncMock()
    service.get_member_from_record_id = AsyncMock()
    return service


@pytest.fixture
def transaction_service():
    """Provide a mock TransactionService for testing."""
    service = Mock()
    service.get_transaction = AsyncMock()
    service.get_transaction_by_display_id = AsyncMock()
    service.get_transaction_by_bot_message_id = AsyncMock()
    service.approve_transaction = AsyncMock()
    service.mark_transaction_paid = AsyncMock()
    service.mark_transaction_delivered = AsyncMock()
    service.cancel_transaction = AsyncMock()
    return service


@pytest.fixture
def bot_message_service():
    """Provide a mock BotMessageService for testing."""
    service = Mock()
    service.get_bot_messages_by_transaction_id = AsyncMock()
    service.delete_bot_message = AsyncMock()
    return service


@pytest.fixture
def sample_buyer():
    """Provide a sample buyer Member for testing."""
    from ledger_bot.models import Member

    buyer = Mock(spec=Member)
    buyer.id = 1
    buyer.discord_id = 999888777
    buyer.username = "buyer_user"
    return buyer


@pytest.fixture
def sample_seller():
    """Provide a sample seller Member for testing."""
    from ledger_bot.models import Member

    seller = Mock(spec=Member)
    seller.id = 2
    seller.discord_id = 111222333
    seller.username = "seller_user"
    return seller


@pytest.fixture
def bot_id():
    """Provide a bot ID for testing."""
    return "123456789012345678"


@pytest.fixture
def sample_currency():
    """Provide a sample Currency for testing."""
    from ledger_bot.models import Currency

    currency = Mock(spec=Currency)
    currency.code = "GBP"
    currency.symbol = "£"
    currency.rate = 1.0
    return currency


@pytest.fixture
def sample_bot_message(sample_transaction):
    """Provide a sample BotMessage for testing."""
    from ledger_bot.models import BotMessage

    bot_message = Mock(spec=BotMessage)
    bot_message.id = 1
    bot_message.message_id = 111222333444555666
    bot_message.channel_id = 999888777666555444
    bot_message.guild_id = 777666555444333222
    bot_message.transaction_id = sample_transaction.id
    bot_message.transaction = sample_transaction
    # Add this bot message to the transaction's bot_messages list
    sample_transaction.bot_messages = [bot_message]
    return bot_message


@pytest.fixture
def sample_transaction(sample_buyer, sample_seller, sample_currency, bot_id):
    """Provide a sample Transaction for testing."""
    from ledger_bot.models import Transaction

    transaction = Mock(spec=Transaction)
    transaction.id = 1
    transaction.display_id = 100
    transaction.buyer_id = sample_buyer.id
    transaction.seller_id = sample_seller.id
    transaction.buyer = sample_buyer
    transaction.seller = sample_seller
    transaction.wine = "Test Wine"
    transaction.price = 99.99
    transaction.currency_code = sample_currency.code
    transaction.currency = sample_currency
    transaction.bot_id = bot_id
    transaction.cancelled = False
    transaction.sale_approved = False
    transaction.buyer_paid = False
    transaction.seller_paid = False
    transaction.buyer_delivered = False
    transaction.seller_delivered = False
    transaction.bot_messages = []
    return transaction


@pytest.fixture
def approved_transaction(sample_buyer, sample_seller, sample_currency, bot_id):
    """Provide an approved Transaction for testing."""
    from ledger_bot.models import Transaction

    transaction = Mock(spec=Transaction)
    transaction.id = 2
    transaction.display_id = 101
    transaction.buyer_id = sample_buyer.id
    transaction.seller_id = sample_seller.id
    transaction.buyer = sample_buyer
    transaction.seller = sample_seller
    transaction.wine = "Approved Wine"
    transaction.price = 149.99
    transaction.currency_code = sample_currency.code
    transaction.currency = sample_currency
    transaction.bot_id = bot_id
    transaction.cancelled = False
    transaction.sale_approved = True
    transaction.buyer_paid = False
    transaction.seller_paid = False
    transaction.buyer_delivered = False
    transaction.seller_delivered = False
    transaction.bot_messages = []
    return transaction


@pytest.fixture
def sample_member():
    """Provide a sample Member for general testing."""
    from ledger_bot.models import Member

    member = Mock(spec=Member)
    member.id = 3
    member.discord_id = 555666777
    member.discord_name = "test_user"
    member.display_name = "Test User"
    return member
