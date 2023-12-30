import pytest

from ledger_bot.message_generators import generate_help_message


def test_generate_help_message_without_dev_or_admmin_commands():
    config = {
        "name": "TestBot",
        "emojis": {
            "approval": "✅",
            "cancel": "❌",
            "paid": "💰",
            "delivered": "📦",
            "reminder": "⏰",
        },
        "maintainer_ids": [123, 456],
        "cleanup_delay_hours": 48,
    }
    result = generate_help_message(config)
    assert "TestBot allows you to track in-progress sales to other users." in result
    assert "✅: Approve a transaction." in result
    assert "/new_sale" in result
    assert "!dev add_reaction" not in result  # Dev command should be skipped
    assert (
        "/add_role <role> <emoji> <message_id>" not in result
    )  # Admin command should be skipped
    assert "was built by <@123>, and <@456>" in result


def test_generate_help_message_without_maintainers():
    with pytest.raises(KeyError) as excinfo:
        config = {
            "name": "TestBot",
            "emojis": {
                "approval": "✅",
                "cancel": "❌",
                "paid": "💰",
                "delivered": "📦",
                "reminder": "⏰",
            },
            "cleanup_delay_hours": 48,
        }
        result = generate_help_message(config)
    assert str(excinfo.value) == "'maintainer_ids'"


def test_generate_help_message_with_one_maintainer():
    config = {
        "name": "TestBot",
        "emojis": {
            "approval": "✅",
            "cancel": "❌",
            "paid": "💰",
            "delivered": "📦",
            "reminder": "⏰",
        },
        "maintainer_ids": [123],
        "cleanup_delay_hours": 48,
    }
    result = generate_help_message(config)
    assert "TestBot allows you to track in-progress sales to other users." in result
    assert "✅: Approve a transaction." in result
    assert "/new_sale" in result
    assert "!dev add_reaction" not in result  # Dev command should be skipped
    assert (
        "/add_role <role> <emoji> <message_id>" not in result
    )  # Admin command should be skipped
    assert "was built by <@123>" in result


def test_generate_help_message_with_dev_commands():
    config = {
        "name": "TestBot",
        "emojis": {
            "approval": "✅",
            "cancel": "❌",
            "paid": "💰",
            "delivered": "📦",
            "reminder": "⏰",
        },
        "maintainer_ids": [123, 456],
        "cleanup_delay_hours": 48,
    }
    result = generate_help_message(
        config, has_dev_commands=True, has_admin_commands=False
    )
    assert "TestBot allows you to track in-progress sales to other users." in result
    assert "✅: Approve a transaction." in result
    assert "/new_sale" in result
    assert "!dev add_reaction" in result  # Dev command should be included
    assert (
        "/add_role <role> <emoji> <message_id>" not in result
    )  # Admin command should be skipperd
    assert "was built by <@123>, and <@456>" in result


def test_generate_help_message_with_admin_commands():
    config = {
        "name": "TestBot",
        "emojis": {
            "approval": "✅",
            "cancel": "❌",
            "paid": "💰",
            "delivered": "📦",
            "reminder": "⏰",
        },
        "maintainer_ids": [123, 456],
        "cleanup_delay_hours": 48,
    }
    result = generate_help_message(
        config, has_dev_commands=False, has_admin_commands=True
    )
    assert "TestBot allows you to track in-progress sales to other users." in result
    assert "✅: Approve a transaction." in result
    assert "/new_sale" in result
    assert "!dev add_reaction" not in result  # Dev command should be skipped
    assert (
        "/add_role <role> <emoji> <message_id>" in result
    )  # Admin command should be included
    assert "was built by <@123>, and <@456>" in result


def test_generate_help_message_with_dev_and_admin_commands():
    config = {
        "name": "TestBot",
        "emojis": {
            "approval": "✅",
            "cancel": "❌",
            "paid": "💰",
            "delivered": "📦",
            "reminder": "⏰",
        },
        "maintainer_ids": [123, 456],
        "cleanup_delay_hours": 48,
    }
    result = generate_help_message(
        config, has_dev_commands=True, has_admin_commands=True
    )
    assert "TestBot allows you to track in-progress sales to other users." in result
    assert "✅: Approve a transaction." in result
    assert "/new_sale" in result
    assert "!dev add_reaction" in result  # Dev command should be included
    assert (
        "/add_role <role> <emoji> <message_id>" in result
    )  # Admin command should be included
    assert "was built by <@123>, and <@456>" in result


def test_generate_help_message_empty_config():
    with pytest.raises(KeyError) as excinfo:
        config = {}
        result = generate_help_message(config)
    assert str(excinfo.value) == "'emojis'"
