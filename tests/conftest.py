"""Pytest configuration and fixtures for all tests."""

import logging

import pytest

from tests.helpers import (
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
