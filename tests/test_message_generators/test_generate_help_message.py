"""Tests for generate_help_message."""

import pytest

from ledger_bot.core import HelpManager
from ledger_bot.core.help_manager import CommandScope
from ledger_bot.message_generators.generate_help_message import generate_help_message


def test_generate_help_message_basic(mock_config):
    """Test generating basic help message."""
    # Clear and set up test commands
    HelpManager._slash_commands = {}
    HelpManager._dm_commands = {}
    HelpManager._reactions = {}

    HelpManager.register_command(
        command="test_slash",
        description="Test slash command",
        scope=CommandScope.SLASH,
    )

    HelpManager.register_command(
        command="test_dm",
        description="Test DM command",
        scope=CommandScope.DM,
    )

    HelpManager.register_reaction(
        reaction_name="approval",
        description="Approve a transaction",
    )

    # Parse to populate emojis
    help_manager = HelpManager(mock_config)
    help_manager.parse_reaction()
    help_manager.parse_commands(CommandScope.SLASH)
    help_manager.parse_commands(CommandScope.DM)

    messages = generate_help_message(mock_config)

    # Should return a list of message strings
    assert isinstance(messages, list)
    assert len(messages) > 0

    # Combine all messages to check content
    full_message = "".join(messages)

    assert mock_config.name in full_message
    assert "allows you to track in-progress sales" in full_message
    assert "/new_sale" in full_message
    assert "**Reactions**" in full_message
    assert "**Channel Commands**" in full_message
    assert "**DM Commands**" in full_message


def test_generate_help_message_with_single_maintainer(mock_config):
    """Test help message with single maintainer."""
    mock_config.maintainer_ids = [123456789]

    HelpManager._slash_commands = {}
    HelpManager._dm_commands = {}
    HelpManager._reactions = {}

    messages = generate_help_message(mock_config)
    full_message = "".join(messages)

    assert "<@123456789>" in full_message
    assert "built by <@123456789>" in full_message


def test_generate_help_message_with_multiple_maintainers(mock_config):
    """Test help message with multiple maintainers."""
    mock_config.maintainer_ids = [111111111, 222222222, 333333333]

    HelpManager._slash_commands = {}
    HelpManager._dm_commands = {}
    HelpManager._reactions = {}

    messages = generate_help_message(mock_config)
    full_message = "".join(messages)

    assert "<@111111111>" in full_message
    assert "<@222222222>" in full_message
    assert "<@333333333>" in full_message
    assert "and <@333333333>" in full_message


def test_generate_help_message_includes_reactions(mock_config):
    """Test help message includes registered reactions."""
    HelpManager._reactions = {}

    HelpManager.register_reaction("approval", "Approve a transaction")
    HelpManager.register_reaction("cancel", "Cancel a transaction")
    HelpManager.register_reaction("paid", "Mark as paid")

    help_manager = HelpManager(mock_config)
    help_manager.parse_reaction()

    messages = generate_help_message(mock_config)
    full_message = "".join(messages)

    assert "**Reactions**" in full_message
    assert "Approve a transaction" in full_message
    assert "Cancel a transaction" in full_message
    assert "Mark as paid" in full_message


def test_generate_help_message_includes_slash_commands(mock_config):
    """Test help message includes registered slash commands."""
    HelpManager._slash_commands = {}

    HelpManager.register_command(
        command="new_sale",
        description="Create a new sale",
        args=["wine", "buyer", "price"],
        scope=CommandScope.SLASH,
    )

    HelpManager.register_command(
        command="list",
        description="List transactions",
        scope=CommandScope.SLASH,
    )

    help_manager = HelpManager(mock_config)
    help_manager.parse_commands(CommandScope.SLASH)

    messages = generate_help_message(mock_config)
    full_message = "".join(messages)

    assert "**Channel Commands**" in full_message
    assert "`/new_sale <wine> <buyer> <price>`" in full_message
    assert "Create a new sale" in full_message
    assert "`/list`" in full_message
    assert "List transactions" in full_message


def test_generate_help_message_includes_dm_commands(mock_config):
    """Test help message includes registered DM commands."""
    HelpManager._dm_commands = {}

    HelpManager.register_command(
        command="help",
        description="Show help",
        scope=CommandScope.DM,
    )

    HelpManager.register_command(
        command="stats",
        description="Show statistics",
        scope=CommandScope.DM,
    )

    help_manager = HelpManager(mock_config)
    help_manager.parse_commands(CommandScope.DM)

    messages = generate_help_message(mock_config)
    full_message = "".join(messages)

    assert "**DM Commands**" in full_message
    assert "`!help`" in full_message
    assert "Show help" in full_message
    assert "`!stats`" in full_message
    assert "Show statistics" in full_message


def test_generate_help_message_excludes_dev_commands_when_not_dev(mock_config):
    """Test dev commands are excluded when user is not dev."""
    HelpManager._slash_commands = {}

    HelpManager.register_command(
        command="public_cmd",
        description="Public command",
        scope=CommandScope.SLASH,
    )

    HelpManager.register_command(
        command="dev_cmd",
        description="Dev only command",
        requires_dev=True,
        scope=CommandScope.SLASH,
    )

    help_manager = HelpManager(mock_config)
    help_manager.parse_commands(CommandScope.SLASH)

    messages = generate_help_message(mock_config, has_dev_commands=False)
    full_message = "".join(messages)

    assert "Public command" in full_message
    # Dev command should not appear
    assert "Dev only command" not in full_message


def test_generate_help_message_includes_dev_commands_when_dev(mock_config):
    """Test dev commands are included when user is dev."""
    HelpManager._slash_commands = {}

    HelpManager.register_command(
        command="public_cmd",
        description="Public command",
        scope=CommandScope.SLASH,
    )

    HelpManager.register_command(
        command="dev_cmd",
        description="Dev only command",
        requires_dev=True,
        scope=CommandScope.SLASH,
    )

    help_manager = HelpManager(mock_config)
    help_manager.parse_commands(CommandScope.SLASH)

    messages = generate_help_message(mock_config, has_dev_commands=True)
    full_message = "".join(messages)

    assert "Public command" in full_message
    assert "Dev only command" in full_message


def test_generate_help_message_excludes_admin_commands_when_not_admin(mock_config):
    """Test admin commands are excluded when user is not admin."""
    HelpManager._slash_commands = {}

    HelpManager.register_command(
        command="public_cmd",
        description="Public command",
        scope=CommandScope.SLASH,
    )

    HelpManager.register_command(
        command="admin_cmd",
        description="Admin only command",
        requires_admin=True,
        scope=CommandScope.SLASH,
    )

    help_manager = HelpManager(mock_config)
    help_manager.parse_commands(CommandScope.SLASH)

    messages = generate_help_message(mock_config, has_admin_commands=False)
    full_message = "".join(messages)

    assert "Public command" in full_message
    assert "Admin only command" not in full_message


def test_generate_help_message_includes_admin_commands_when_admin(mock_config):
    """Test admin commands are included when user is admin."""
    HelpManager._slash_commands = {}

    HelpManager.register_command(
        command="public_cmd",
        description="Public command",
        scope=CommandScope.SLASH,
    )

    HelpManager.register_command(
        command="admin_cmd",
        description="Admin only command",
        requires_admin=True,
        scope=CommandScope.SLASH,
    )

    help_manager = HelpManager(mock_config)
    help_manager.parse_commands(CommandScope.SLASH)

    messages = generate_help_message(mock_config, has_admin_commands=True)
    full_message = "".join(messages)

    assert "Public command" in full_message
    assert "Admin only command" in full_message


def test_generate_help_message_excludes_dev_reactions_when_not_dev(mock_config):
    """Test dev reactions are excluded when user is not dev."""
    HelpManager._reactions = {}

    HelpManager.register_reaction("approval", "Approve")
    HelpManager.register_reaction("thinking", "Dev reaction", requires_dev=True)

    help_manager = HelpManager(mock_config)
    help_manager.parse_reaction()

    messages = generate_help_message(mock_config, has_dev_commands=False)
    full_message = "".join(messages)

    assert "Approve" in full_message
    assert "Dev reaction" not in full_message


def test_generate_help_message_includes_footer(mock_config):
    """Test help message includes footer with credits."""
    HelpManager._slash_commands = {}
    HelpManager._dm_commands = {}
    HelpManager._reactions = {}

    messages = generate_help_message(mock_config)
    full_message = "".join(messages)

    assert "built by" in full_message
    assert "hosted by <https://snailedit.dev/>" in full_message
    assert (
        "Exchange rates are provided by <https://exchangerate-api.com>" in full_message
    )


def test_generate_help_message_returns_list_of_strings(mock_config):
    """Test that help message is returned as list for splitting."""
    HelpManager._slash_commands = {}
    HelpManager._dm_commands = {}
    HelpManager._reactions = {}

    messages = generate_help_message(mock_config)

    assert isinstance(messages, list)
    for message in messages:
        assert isinstance(message, str)
        # Messages should respect Discord's 2000 character limit
        assert len(message) <= 2000
