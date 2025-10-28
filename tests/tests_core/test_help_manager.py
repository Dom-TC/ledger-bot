import logging
import types
from typing import cast

import pytest

from ledger_bot.core import Config
from ledger_bot.core.help_manager import (
    CommandHelp,
    CommandScope,
    HelpManager,
    ReactionHelp,
    ensure_scope,
    register_help_command,
    register_help_reaction,
)


class DummyConfig:
    def __init__(self):
        self.emojis = types.SimpleNamespace(testemoji="😀")
        self.value = "example"


@pytest.fixture(autouse=True)
def clear_helpmanager_state():
    """Ensure each test starts with empty registries."""
    HelpManager._reactions.clear()
    HelpManager._slash_commands.clear()
    HelpManager._dm_commands.clear()
    yield
    HelpManager._reactions.clear()
    HelpManager._slash_commands.clear()
    HelpManager._dm_commands.clear()


def test_ensure_scope_from_enum():
    assert ensure_scope(CommandScope.DM) is CommandScope.DM
    assert ensure_scope(CommandScope.SLASH) is CommandScope.SLASH


def test_ensure_scope_from_string():
    assert ensure_scope("dm") is CommandScope.DM
    assert ensure_scope("SLASH") is CommandScope.SLASH


@pytest.mark.parametrize(
    "command, description, args, requires_dev, requires_admin",
    [
        ("test1", "test 1 description", None, False, False),
        ("test2", "test 2 description", None, True, False),
        ("test3", "test 3 description", None, False, True),
        ("test4", "test 4 description", None, True, True),
        ("test5", "test 5 description", ["1", "2"], False, False),
        ("test6", "test 6 description", ["1", "2"], True, True),
    ],
)
def test_register_command_slash(
    command, description, args, requires_dev, requires_admin
):
    HelpManager.register_command(
        command=command,
        description=description,
        args=args,
        requires_dev=requires_dev,
        requires_admin=requires_admin,
        scope=CommandScope.SLASH,
    )

    assert command in HelpManager._slash_commands

    cmd = HelpManager._slash_commands[command]

    arg_res = args or []
    assert isinstance(cmd, CommandHelp)
    assert cmd.command == f"/{command}"
    assert cmd.description == description
    assert cmd.args == arg_res
    assert cmd.requires_dev == requires_dev
    assert cmd.requires_admin == requires_admin


@pytest.mark.parametrize(
    "command, description, args, requires_dev, requires_admin",
    [
        ("test1", "test 1 description", None, False, False),
        ("test2", "test 2 description", None, True, False),
        ("test3", "test 3 description", None, False, True),
        ("test4", "test 4 description", None, True, True),
        ("test5", "test 5 description", ["1", "2"], False, False),
        ("test6", "test 6 description", ["1", "2"], True, True),
    ],
)
def test_register_command_dm(command, description, args, requires_dev, requires_admin):
    HelpManager.register_command(
        command=command,
        description=description,
        args=args,
        requires_dev=requires_dev,
        requires_admin=requires_admin,
        scope=CommandScope.DM,
    )

    assert command in HelpManager._dm_commands

    cmd = HelpManager._dm_commands[command]

    arg_res = args or []
    assert isinstance(cmd, CommandHelp)
    assert cmd.command == f"!{command}"
    assert cmd.description == description
    assert cmd.args == arg_res
    assert cmd.requires_dev == requires_dev
    assert cmd.requires_admin == requires_admin


@pytest.mark.parametrize(
    "reaction_name, description, requires_dev, requires_admin",
    [
        (
            "test1",
            "test 1 description",
            False,
            False,
        ),
        (
            "test2",
            "test 2 description",
            True,
            False,
        ),
        (
            "test3",
            "test 3 description",
            False,
            True,
        ),
        (
            "test4",
            "test 4 description",
            True,
            True,
        ),
        ("test5", "test 5 description", False, False),
    ],
)
def test_register_reaction(reaction_name, description, requires_dev, requires_admin):
    HelpManager.register_reaction(
        reaction_name=reaction_name,
        description=description,
        requires_dev=requires_dev,
        requires_admin=requires_admin,
    )

    assert reaction_name in HelpManager._reactions

    rct = HelpManager._reactions[reaction_name]

    assert isinstance(rct, ReactionHelp)
    assert rct.reaction_name == reaction_name
    assert rct.description == description
    assert rct.requires_dev == requires_dev
    assert rct.requires_admin == requires_admin


def test_parse_reaction_sets_emoji_and_formats():
    cfg = cast(Config, DummyConfig())

    HelpManager.register_reaction("testemoji", "Emoji test: {config.value}")
    manager = HelpManager(cfg)

    manager.parse_reaction()
    reaction = HelpManager._reactions["testemoji"]
    assert reaction.reaction == "😀"
    assert reaction.description == "Emoji test: example"


def test_parse_commands_slash_and_dm():
    cfg = cast(Config, DummyConfig())
    HelpManager.register_command(
        "slashcmd", "SLASH {config.value}", scope=CommandScope.SLASH
    )
    HelpManager.register_command("dmcmd", "DM {config.value}", scope=CommandScope.DM)

    manager = HelpManager(cfg)
    manager.parse_commands(CommandScope.SLASH)
    manager.parse_commands(CommandScope.DM)

    slash = HelpManager._slash_commands["slashcmd"]
    dm = HelpManager._dm_commands["dmcmd"]

    assert slash.description == "SLASH example"
    assert dm.description == "DM example"


def test_get_methods_call_parsers(monkeypatch):
    cfg = cast(Config, DummyConfig())
    manager = HelpManager(cfg)

    calls = []

    monkeypatch.setattr(manager, "parse_reaction", lambda: calls.append("reaction"))
    monkeypatch.setattr(
        manager, "parse_commands", lambda scope=None: calls.append(scope)
    )

    manager.get_reactions()
    manager.get_slash_commands()
    manager.get_dm_commands()

    assert "reaction" in calls
    assert CommandScope.SLASH in calls
    assert CommandScope.DM in calls


def test_register_help_command_decorator_registers(monkeypatch):
    monkeypatch.setattr(HelpManager, "register_command", lambda **kw: kw)

    @register_help_command("foo", "Bar description", args=["x"], requires_admin=True)
    def foo():
        return "done"

    assert foo() == "done"


def test_register_help_reaction_decorator_registers(monkeypatch):
    monkeypatch.setattr(HelpManager, "register_reaction", lambda **kw: kw)

    @register_help_reaction("like", "description", requires_dev=True)
    def func():
        return "done"

    assert func() == "done"
