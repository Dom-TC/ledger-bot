"""Generate help message text."""

import logging
from typing import List

from ledger_bot.core import Config, HelpManager

from .split_message import split_message

log = logging.getLogger(__name__)


def generate_help_message(
    config: Config,
    has_dev_commands: bool = False,
    has_admin_commands: bool = False,
) -> List[str]:
    """Generates help text.

    Taking into account whether someone has access to dev commands

    Parameters
    ----------
    config: Dict[str, Any]
        The config dictionary

    has_dev_commands : bool, optional
        Does the user have access to dev commands, by default False

    Returns
    -------
    str
        The message to be sent
    """
    log.info("Generating help message...")

    help_manager = HelpManager(config=config)

    # Create comma seperated list, with "and" before final element
    if len(config.maintainer_ids) > 1:
        maintainers = (
            "<@"
            + ">, <@".join(str(maintainer) for maintainer in config.maintainer_ids[:-1])
            + ">, and <@"
            + str(config.maintainer_ids[-1])
            + ">"
        )
    else:
        maintainers = f"<@{str(config.maintainer_ids[0])}>"

    prefix = f"{config.name} allows you to track in-progress sales to other users.\nCreate a new transaction with `/new_sale`. To update a transactions status, react to the message from {config.name}."
    suffix = f"{config.name} was built by {maintainers} and is hosted by <https://snailedit.dev/>."

    reactions = help_manager.get_reactions()

    reaction_body = "\n**Reactions**\n"

    for reaction_name in reactions:
        reaction = reactions[reaction_name]

        if reaction.reaction is None:
            log.error(
                f"Skipping reaction: {reaction.reaction_name}, reaction.reaction is None"
            )
            break

        if reaction.requires_dev and not has_dev_commands:
            log.debug(f"Skipping dev reaction: {reaction.reaction}")
            break

        if reaction.requires_admin and not has_admin_commands:
            log.debug(f"Skipping admin reaction: {reaction.reaction}")
            break

        reaction_body += f"{reaction.reaction}: {reaction.description}\n"

    slash_commands = help_manager.get_slash_commands()

    slash_body = "\n**Channel Commands**\n"

    for slash_name in slash_commands:
        slash_command = slash_commands[slash_name]

        if slash_command.requires_dev and not has_dev_commands:
            log.debug(f"Skipping dev slash command: {slash_command.command}")
            break

        if slash_command.requires_admin and not has_admin_commands:
            log.debug(f"Skipping admin slash command: {slash_command.command}")
            break

        slash_body += f"`{slash_command.command}"

        for arg in slash_command.args:
            slash_body += f" <{arg}>"

        slash_body += f"`: {slash_command.description}\n"

    dm_commands = help_manager.get_dm_commands()

    dm_body = "\n**DM Commands**\n"

    for dm_name in dm_commands:
        dm_command = dm_commands[dm_name]

        if dm_command.requires_dev and not has_dev_commands:
            log.debug(f"Skipping dev dm command: {dm_command.command}")
            break

        if dm_command.requires_admin and not has_admin_commands:
            log.debug(f"Skipping admin dm command: {dm_command.command}")
            break

        dm_body += f"`{dm_command.command}"

        for arg in dm_command.args:
            dm_body += f" <{arg}>"

        dm_body += f"`: {dm_command.description}\n"

    content = [prefix, reaction_body, slash_body, dm_body, suffix]

    message = split_message(content)

    return message
