"""Tests for ReactionRolesClient."""

from unittest.mock import AsyncMock, Mock, PropertyMock, patch

import discord
import pytest


@pytest.fixture
def mock_reaction_roles_client(mock_config, session_factory):
    """Create a mock ReactionRolesClient for testing."""
    from apscheduler.schedulers.asyncio import AsyncIOScheduler

    from ledger_bot.clients.reaction_roles_client import ReactionRolesClient

    scheduler = AsyncIOScheduler()

    service = Mock()
    service.reaction_role = Mock()
    service.reaction_role.watched_message_ids = []
    service.reaction_role.list_watched_message_ids = AsyncMock(return_value=[])

    intents = discord.Intents.default()
    client = ReactionRolesClient(
        config=mock_config,
        scheduler=scheduler,
        service=service,
        session_factory=session_factory,
        intents=intents,
    )

    return client


@pytest.mark.asyncio
async def test_refresh_reaction_role_caches(mock_reaction_roles_client):
    """Test refreshing reaction role watched messages."""
    mock_reaction_roles_client.service.reaction_role.list_watched_message_ids = (
        AsyncMock(return_value=[123456, 789012])
    )

    await mock_reaction_roles_client.refresh_reaction_role_caches()

    mock_reaction_roles_client.service.reaction_role.list_watched_message_ids.assert_called_once()


@pytest.mark.asyncio
async def test_handle_role_reaction_not_watched(mock_reaction_roles_client):
    """Test that reactions on non-watched messages are ignored."""
    payload = Mock()
    payload.message_id = 999999  # Not in watched list

    mock_reaction_roles_client.service.reaction_role.watched_message_ids = [123456]

    result = await mock_reaction_roles_client.handle_role_reaction(payload)

    assert result is False


@pytest.mark.asyncio
async def test_handle_role_reaction_from_self(mock_reaction_roles_client):
    """Test that reactions from the bot itself are ignored."""
    payload = Mock()
    payload.message_id = 123456
    payload.user_id = 999888777

    mock_reaction_roles_client.service.reaction_role.watched_message_ids = [123456]
    # Mock get_or_fetch_user to return the same user as client.user
    bot_user = Mock()
    with patch.object(
        type(mock_reaction_roles_client),
        "user",
        new_callable=PropertyMock,
        return_value=bot_user,
    ):
        mock_reaction_roles_client.get_or_fetch_user = AsyncMock(return_value=bot_user)

        result = await mock_reaction_roles_client.handle_role_reaction(payload)

    assert result is False


@pytest.mark.asyncio
async def test_handle_role_reaction_no_mapping(mock_reaction_roles_client):
    """Test reaction when no role mapping exists."""
    payload = Mock()
    payload.message_id = 123456
    payload.user_id = 999888777
    payload.guild_id = 111222333
    payload.emoji = Mock()
    payload.emoji.__str__ = Mock(return_value="👍")
    payload.member = Mock()

    mock_reaction_roles_client.service.reaction_role.watched_message_ids = [123456]

    bot_user = Mock()
    bot_user.id = 111111111
    different_user = Mock()
    different_user.id = 999888777

    with patch.object(
        type(mock_reaction_roles_client),
        "user",
        new_callable=PropertyMock,
        return_value=bot_user,
    ):
        mock_reaction_roles_client.get_or_fetch_user = AsyncMock(
            return_value=different_user
        )
        mock_reaction_roles_client.service.reaction_role.get_reaction_role_by_reaction = AsyncMock(
            return_value=None
        )

        result = await mock_reaction_roles_client.handle_role_reaction(payload)

    assert result is False


@pytest.mark.asyncio
async def test_handle_role_reaction_add_role(mock_reaction_roles_client):
    """Test successfully adding role via reaction."""
    payload = Mock()
    payload.message_id = 123456
    payload.user_id = 999888777
    payload.guild_id = 111222333
    payload.emoji = Mock()
    payload.emoji.__str__ = Mock(return_value="👍")
    payload.member = Mock()
    payload.member.roles = []
    payload.member.add_roles = AsyncMock()

    mock_reaction_role = Mock()
    mock_reaction_role.role_id = "555666777"

    mock_role = Mock()
    mock_role.id = 555666777

    mock_guild = Mock()
    mock_guild.get_role = Mock(return_value=mock_role)

    mock_reaction_roles_client.service.reaction_role.watched_message_ids = [123456]

    bot_user = Mock()
    bot_user.id = 111111111
    different_user = Mock()
    different_user.id = 999888777

    with patch.object(
        type(mock_reaction_roles_client),
        "user",
        new_callable=PropertyMock,
        return_value=bot_user,
    ):
        mock_reaction_roles_client.get_or_fetch_user = AsyncMock(
            return_value=different_user
        )
        mock_reaction_roles_client.get_guild = Mock(return_value=mock_guild)
        mock_reaction_roles_client.service.reaction_role.get_reaction_role_by_reaction = AsyncMock(
            return_value=mock_reaction_role
        )

        result = await mock_reaction_roles_client.handle_role_reaction(payload)

    assert result is True
    payload.member.add_roles.assert_called_once()


@pytest.mark.asyncio
async def test_handle_role_reaction_role_already_assigned(mock_reaction_roles_client):
    """Test reaction when member already has the role."""
    payload = Mock()
    payload.message_id = 123456
    payload.user_id = 999888777
    payload.guild_id = 111222333
    payload.emoji = Mock()
    payload.emoji.__str__ = Mock(return_value="👍")

    mock_role = Mock()
    mock_role.id = 555666777

    payload.member = Mock()
    payload.member.roles = [mock_role]  # Already has the role
    payload.member.add_roles = AsyncMock()

    mock_reaction_role = Mock()
    mock_reaction_role.role_id = "555666777"

    mock_guild = Mock()
    mock_guild.get_role = Mock(return_value=mock_role)

    mock_reaction_roles_client.service.reaction_role.watched_message_ids = [123456]

    bot_user = Mock()
    bot_user.id = 111111111
    different_user = Mock()
    different_user.id = 999888777

    with patch.object(
        type(mock_reaction_roles_client),
        "user",
        new_callable=PropertyMock,
        return_value=bot_user,
    ):
        mock_reaction_roles_client.get_or_fetch_user = AsyncMock(
            return_value=different_user
        )
        mock_reaction_roles_client.get_guild = Mock(return_value=mock_guild)
        mock_reaction_roles_client.service.reaction_role.get_reaction_role_by_reaction = AsyncMock(
            return_value=mock_reaction_role
        )

        result = await mock_reaction_roles_client.handle_role_reaction(payload)

    assert result is True
    # Should not call add_roles since already has role
    payload.member.add_roles.assert_not_called()


@pytest.mark.asyncio
async def test_handled_role_reaction_removal_success(mock_reaction_roles_client):
    """Test successfully removing role via reaction removal."""
    payload = Mock()
    payload.message_id = 123456
    payload.user_id = 999888777
    payload.guild_id = 111222333
    payload.emoji = Mock()
    payload.emoji.__str__ = Mock(return_value="👍")

    mock_role = Mock()
    mock_role.id = 555666777

    mock_member = Mock()
    mock_member.roles = [mock_role]
    mock_member.remove_roles = AsyncMock()

    mock_reaction_role = Mock()
    mock_reaction_role.role_id = "555666777"

    mock_guild = Mock()
    mock_guild.get_role = Mock(return_value=mock_role)
    mock_guild.get_member = Mock(return_value=mock_member)

    mock_reaction_roles_client.service.reaction_role.watched_message_ids = [123456]

    bot_user = Mock()
    bot_user.id = 111111111
    different_user = Mock()
    different_user.id = 999888777

    with patch.object(
        type(mock_reaction_roles_client),
        "user",
        new_callable=PropertyMock,
        return_value=bot_user,
    ):
        mock_reaction_roles_client.get_or_fetch_user = AsyncMock(
            return_value=different_user
        )
        mock_reaction_roles_client.get_guild = Mock(return_value=mock_guild)
        mock_reaction_roles_client.service.reaction_role.get_reaction_role_by_reaction = AsyncMock(
            return_value=mock_reaction_role
        )

        result = await mock_reaction_roles_client.handled_role_reaction_removal(payload)

    assert result is True
    mock_member.remove_roles.assert_called_once()


@pytest.mark.asyncio
async def test_handled_role_reaction_removal_not_watched(mock_reaction_roles_client):
    """Test that reaction removals on non-watched messages are ignored."""
    payload = Mock()
    payload.message_id = 999999  # Not in watched list

    mock_reaction_roles_client.service.reaction_role.watched_message_ids = [123456]

    result = await mock_reaction_roles_client.handled_role_reaction_removal(payload)

    assert result is False


@pytest.mark.asyncio
async def test_handled_role_reaction_removal_from_self(mock_reaction_roles_client):
    """Test that reaction removals from bot are ignored."""
    payload = Mock()
    payload.message_id = 123456
    payload.user_id = 999888777

    mock_reaction_roles_client.service.reaction_role.watched_message_ids = [123456]

    bot_user = Mock()
    with patch.object(
        type(mock_reaction_roles_client),
        "user",
        new_callable=PropertyMock,
        return_value=bot_user,
    ):
        mock_reaction_roles_client.get_or_fetch_user = AsyncMock(return_value=bot_user)

        result = await mock_reaction_roles_client.handled_role_reaction_removal(payload)

    assert result is False


@pytest.mark.asyncio
async def test_handled_role_reaction_removal_no_role_mapping(
    mock_reaction_roles_client,
):
    """Test reaction removal when no role mapping exists."""
    payload = Mock()
    payload.message_id = 123456
    payload.user_id = 999888777
    payload.guild_id = 111222333
    payload.emoji = Mock()
    payload.emoji.__str__ = Mock(return_value="👍")

    mock_guild = Mock()

    mock_reaction_roles_client.service.reaction_role.watched_message_ids = [123456]

    bot_user = Mock()
    bot_user.id = 111111111
    different_user = Mock()
    different_user.id = 999888777

    with patch.object(
        type(mock_reaction_roles_client),
        "user",
        new_callable=PropertyMock,
        return_value=bot_user,
    ):
        mock_reaction_roles_client.get_or_fetch_user = AsyncMock(
            return_value=different_user
        )
        mock_reaction_roles_client.get_guild = Mock(return_value=mock_guild)
        mock_reaction_roles_client.service.reaction_role.get_reaction_role_by_reaction = AsyncMock(
            return_value=None
        )

        result = await mock_reaction_roles_client.handled_role_reaction_removal(payload)

    assert result is False
