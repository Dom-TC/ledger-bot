"""Build help classes."""

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List

from ledger_bot.utils import debug

from .config import Config

log = logging.getLogger(__name__)


class CommandScope(Enum):
    DM = "dm"
    SLASH = "slash"


def ensure_scope(value: str | CommandScope) -> CommandScope:
    """Convert string to CommandScope."""
    if isinstance(value, CommandScope):
        return value
    return CommandScope(value.lower())


@dataclass
class ReactionHelp:
    reaction_name: str
    description: str
    requires_dev: bool = False
    requires_admin: bool = False
    reaction: str | None = None


@dataclass
class CommandHelp:
    command: str
    description: str
    args: List[str] = field(default_factory=list)
    requires_dev: bool = False
    requires_admin: bool = False


class HelpManager:
    _reactions: Dict[str, ReactionHelp] = {}
    _slash_commands: Dict[str, CommandHelp] = {}
    _dm_commands: Dict[str, CommandHelp] = {}

    def __init__(self, config: Config):
        self.config = config

    @classmethod
    def register_command(
        cls,
        command: str,
        description: str,
        args: List[str] | None = None,
        requires_dev: bool = False,
        requires_admin: bool = False,
        scope: CommandScope | str = CommandScope.SLASH,
    ) -> None:
        log.info(f"Registering command: {command}")

        scope = ensure_scope(scope)

        if scope is CommandScope.SLASH:
            cls._slash_commands[command] = CommandHelp(
                command=f"/{command}",
                args=args or [],
                description=description,
                requires_dev=requires_dev,
                requires_admin=requires_admin,
            )

        if scope is CommandScope.DM:
            cls._dm_commands[command] = CommandHelp(
                command=f"!{command}",
                args=args or [],
                description=description,
                requires_dev=requires_dev,
                requires_admin=requires_admin,
            )

    @classmethod
    def register_reaction(
        cls,
        reaction_name: str,
        description: str,
        requires_dev: bool = False,
        requires_admin: bool = False,
    ) -> None:
        log.info(f"Registering reaction: {reaction_name}")
        cls._reactions[reaction_name] = ReactionHelp(
            reaction_name=reaction_name,
            description=description,
            requires_dev=requires_dev,
            requires_admin=requires_admin,
        )

    def parse_reaction(self):
        for reaction_name in self._reactions:
            reaction = self._reactions[reaction_name]
            reaction.reaction = getattr(self.config.emojis, reaction.reaction_name)

            reaction.description = reaction.description.format(config=self.config)

    def parse_commands(self, scope: CommandScope | str = CommandScope.SLASH):
        scope = ensure_scope(scope)

        if scope is CommandScope.SLASH:
            for command_name in self._slash_commands:
                command = self._slash_commands[command_name]
                command.description = command.description.format(config=self.config)

        if scope is CommandScope.DM:
            for command_name in self._dm_commands:
                command = self._dm_commands[command_name]
                command.description = command.description.format(config=self.config)

    def get_reactions(self):
        self.parse_reaction()
        return self._reactions

    def get_slash_commands(self):
        self.parse_commands(CommandScope.SLASH)
        return self._slash_commands

    def get_dm_commands(self):
        self.parse_commands(CommandScope.DM)
        return self._dm_commands


def register_help_reaction(
    reaction_name: str,
    description: str,
    requires_dev: bool = False,
    requires_admin: bool = False,
):
    """Register a reaction to the help system.

    Parameters
    ----------
    reaction : str
        The name of the reaction emoji in the config
    description : str
        A description of what the reaction does
    requires_dev : bool, optional
        Does using the reaction require being a maintainer, by default False
    requires_admin : bool, optional
        Does using the reaction require being an admin, by default False
    """

    def decorator(func: Callable) -> Callable:
        HelpManager.register_reaction(
            reaction_name=reaction_name,
            description=description,
            requires_dev=requires_dev,
            requires_admin=requires_admin,
        )
        return func

    return decorator


def register_help_command(
    command: str,
    description: str,
    args: List[str] | None = None,
    requires_dev: bool = False,
    requires_admin: bool = False,
    scope: CommandScope | str = CommandScope.SLASH,
):
    """Register a command to the help system.

    Parameters
    ----------
    command : str
        The command the user can call
    description : str
        A description of what the command does
    args : List[str], optional
        A list of available arguments for the command, by default None
    requires_dev : bool, optional
        Does using the command require being a maintainer, by default False
    requires_admin : bool, optional
        Does using the command require being an admin, by default False
    """

    def decorator(func: Callable) -> Callable:
        HelpManager.register_command(
            command=command,
            args=args,
            description=description,
            requires_dev=requires_dev,
            requires_admin=requires_admin,
            scope=scope,
        )
        return func

    return decorator
