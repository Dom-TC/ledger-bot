"""Tests for ExtendedClient."""

from unittest.mock import AsyncMock, Mock, patch

import discord
import pytest

from ledger_bot.clients.extended_client import ExtendedClient


@pytest.fixture
def mock_extended_client(mock_config, session_factory):
    """Create a mock ExtendedClient for testing."""
    intents = discord.Intents.default()
    client = ExtendedClient(intents=intents)
    client.config = mock_config
    client.session_factory = session_factory
    client.guild = Mock()
    client.guild.id = 123456789
    return client


@pytest.mark.asyncio
async def test_get_or_fetch_channel_from_cache(mock_extended_client):
    """Test getting channel from cache."""
    mock_channel = Mock()
    mock_channel.id = 111222333

    mock_extended_client.get_channel = Mock(return_value=mock_channel)

    result = await mock_extended_client.get_or_fetch_channel(111222333)

    assert result == mock_channel
    mock_extended_client.get_channel.assert_called_once_with(111222333)


@pytest.mark.asyncio
async def test_get_or_fetch_channel_fetch(mock_extended_client):
    """Test fetching channel when not in cache."""
    mock_channel = Mock()
    mock_channel.id = 111222333

    mock_extended_client.get_channel = Mock(return_value=None)
    mock_extended_client.fetch_channel = AsyncMock(return_value=mock_channel)

    result = await mock_extended_client.get_or_fetch_channel(111222333)

    assert result == mock_channel
    mock_extended_client.fetch_channel.assert_called_once_with(111222333)


@pytest.mark.asyncio
async def test_get_or_fetch_user_from_cache(mock_extended_client):
    """Test getting user from cache."""
    mock_user = Mock()
    mock_user.id = 999888777

    mock_extended_client.get_user = Mock(return_value=mock_user)

    result = await mock_extended_client.get_or_fetch_user(999888777)

    assert result == mock_user
    mock_extended_client.get_user.assert_called_once_with(999888777)


@pytest.mark.asyncio
async def test_get_or_fetch_user_fetch(mock_extended_client):
    """Test fetching user when not in cache."""
    mock_user = Mock()
    mock_user.id = 999888777

    mock_extended_client.get_user = Mock(return_value=None)
    mock_extended_client.fetch_user = AsyncMock(return_value=mock_user)

    result = await mock_extended_client.get_or_fetch_user(999888777)

    assert result == mock_user
    mock_extended_client.fetch_user.assert_called_once_with(999888777)


@pytest.mark.asyncio
async def test_get_or_fetch_guild_from_cache(mock_extended_client):
    """Test getting guild from cache."""
    mock_guild = Mock()
    mock_guild.id = 123456789

    mock_extended_client.get_guild = Mock(return_value=mock_guild)

    result = await mock_extended_client.get_or_fetch_guild(123456789)

    assert result == mock_guild
    mock_extended_client.get_guild.assert_called_once_with(123456789)


@pytest.mark.asyncio
async def test_get_or_fetch_guild_fetch(mock_extended_client):
    """Test fetching guild when not in cache."""
    mock_guild = Mock()
    mock_guild.id = 123456789

    mock_extended_client.get_guild = Mock(return_value=None)
    mock_extended_client.fetch_guild = AsyncMock(return_value=mock_guild)

    result = await mock_extended_client.get_or_fetch_guild(123456789)

    assert result == mock_guild
    mock_extended_client.fetch_guild.assert_called_once_with(123456789)


@pytest.mark.asyncio
async def test_get_or_fetch_member_with_user_object(mock_extended_client):
    """Test getting member with User object."""
    mock_user = Mock(spec=discord.User)
    mock_user.id = 999888777

    mock_guild = Mock()
    mock_guild.id = 123456789
    mock_guild.get_member = Mock(return_value=None)
    mock_guild.fetch_member = AsyncMock(return_value=Mock())

    mock_extended_client.get_or_fetch_guild = AsyncMock(return_value=mock_guild)

    result = await mock_extended_client.get_or_fetch_member(mock_user, 123456789)

    assert result is not None
    mock_guild.fetch_member.assert_called_once_with(999888777)


@pytest.mark.asyncio
async def test_get_or_fetch_member_with_user_id(mock_extended_client):
    """Test getting member with user ID integer."""
    mock_member = Mock()

    mock_guild = Mock()
    mock_guild.id = 123456789
    mock_guild.get_member = Mock(return_value=mock_member)

    result = await mock_extended_client.get_or_fetch_member(999888777, mock_guild)

    assert result == mock_member
    mock_guild.get_member.assert_called_once_with(999888777)


@pytest.mark.asyncio
async def test_is_admin_or_maintainer_admin_role(mock_extended_client):
    """Test checking if user is admin via role."""
    import discord

    mock_member = Mock()
    mock_member.id = 999888777
    mock_role = Mock()
    mock_member.get_role = Mock(return_value=mock_role)

    mock_guild = Mock(spec=discord.Guild)
    mock_guild.get_member = Mock(return_value=mock_member)

    mock_extended_client.guild = mock_guild
    mock_extended_client.config.admin_role = 111222333
    mock_extended_client.config.maintainer_ids = []

    result = await mock_extended_client.is_admin_or_maintainer(999888777)

    assert result is True


@pytest.mark.asyncio
async def test_is_admin_or_maintainer_in_maintainer_list(mock_extended_client):
    """Test checking if user is in maintainer list."""
    import discord

    mock_member = Mock()
    mock_member.id = 999888777
    mock_member.get_role = Mock(return_value=None)

    mock_guild = Mock(spec=discord.Guild)
    mock_guild.get_member = Mock(return_value=mock_member)

    mock_extended_client.guild = mock_guild
    mock_extended_client.config.admin_role = 111222333
    mock_extended_client.config.maintainer_ids = [999888777]

    result = await mock_extended_client.is_admin_or_maintainer(999888777)

    assert result is True


@pytest.mark.asyncio
async def test_is_admin_or_maintainer_not_admin(mock_extended_client):
    """Test checking if user is not admin or maintainer."""
    import discord

    mock_member = Mock()
    mock_member.id = 999888777
    mock_member.get_role = Mock(return_value=None)

    mock_guild = Mock(spec=discord.Guild)
    mock_guild.get_member = Mock(return_value=mock_member)

    mock_extended_client.guild = mock_guild
    mock_extended_client.config.admin_role = 111222333
    mock_extended_client.config.maintainer_ids = []

    result = await mock_extended_client.is_admin_or_maintainer(999888777)

    assert result is False


@pytest.mark.asyncio
async def test_is_admin_or_maintainer_no_member(mock_extended_client):
    """Test checking admin when member not found."""
    import discord

    mock_guild = Mock(spec=discord.Guild)
    mock_guild.get_member = Mock(return_value=None)

    mock_extended_client.guild = mock_guild

    result = await mock_extended_client.is_admin_or_maintainer(999888777)

    assert result is False


@pytest.mark.asyncio
async def test_is_admin_or_maintainer_guild_not_ready(mock_extended_client):
    """Test checking admin when guild is not a Guild object."""
    import discord

    mock_extended_client.guild = discord.Object(id=123456789)

    result = await mock_extended_client.is_admin_or_maintainer(999888777)

    assert result is False


@pytest.mark.asyncio
@patch("os.getenv")
@patch("ledger_bot.clients.extended_client.which")
async def test_get_version_number_from_env(
    mock_which, mock_getenv, mock_extended_client, db_session
):
    """Test getting version from environment variable."""
    mock_getenv.return_value = "v1.2.3"
    mock_which.return_value = None

    # Mock alembic query
    from unittest.mock import AsyncMock, Mock

    from sqlalchemy import text

    await db_session.execute(
        text("CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR)")
    )
    await db_session.execute(
        text("INSERT INTO alembic_version (version_num) VALUES ('abc123')")
    )
    await db_session.commit()

    # Create a real session factory that uses db_session
    real_session_factory = Mock()
    real_session_factory.return_value.__aenter__ = AsyncMock(return_value=db_session)
    real_session_factory.return_value.__aexit__ = AsyncMock()
    mock_extended_client.session_factory = real_session_factory

    version = await mock_extended_client.get_version_number()

    assert "v1.2.3" in version
    assert "abc123" in version


@pytest.mark.asyncio
@patch("os.getenv")
@patch("ledger_bot.clients.extended_client.which")
@patch("ledger_bot.clients.extended_client.check_output")
async def test_get_version_number_from_git(
    mock_check_output, mock_which, mock_getenv, mock_extended_client, db_session
):
    """Test getting version from git tags."""
    mock_getenv.return_value = None
    mock_which.return_value = "/usr/bin/git"
    mock_check_output.return_value = b"v2.0.0\n"

    # Mock alembic query
    from unittest.mock import AsyncMock, Mock

    from sqlalchemy import text

    await db_session.execute(
        text("CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR)")
    )
    await db_session.execute(
        text("INSERT INTO alembic_version (version_num) VALUES ('xyz789')")
    )
    await db_session.commit()

    # Create a real session factory that uses db_session
    real_session_factory = Mock()
    real_session_factory.return_value.__aenter__ = AsyncMock(return_value=db_session)
    real_session_factory.return_value.__aexit__ = AsyncMock()
    mock_extended_client.session_factory = real_session_factory

    version = await mock_extended_client.get_version_number()

    assert "v2.0.0" in version
    assert "xyz789" in version
