"""Generate help message text."""

import logging
from typing import Any, Dict, List

from .split_message import split_message

log = logging.getLogger(__name__)


def generate_help_message(
    config: Dict[str, Any],
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

    # The sections of the message
    # Outer array is list of sections, each containing a list of commands or reactions
    # Each command is a dict, containing "command", "args", "description", "requires_dev", "requires_admin"
    # Each reaction is a dict, containing "reaction", "description", "requires_dev", "requires_admin"
    sections = {
        "Reactions": [
            {
                "reaction": config["emojis"]["approval"],
                "description": "Approve a transaction.",
                "requires_dev": False,
                "requires_admin": False,
            },
            {
                "reaction": config["emojis"]["cancel"],
                "description": "Cancel a transaction.",
                "requires_dev": False,
                "requires_admin": False,
            },
            {
                "reaction": config["emojis"]["paid"],
                "description": "Mark a transaction as paid.",
                "requires_dev": False,
                "requires_admin": False,
            },
            {
                "reaction": config["emojis"]["delivered"],
                "description": "Mark a transaction as delivered.",
                "requires_dev": False,
                "requires_admin": False,
            },
            {
                "reaction": config["emojis"]["reminder"],
                "description": "Set a reminder for a transaction.",
                "requires_dev": False,
                "requires_admin": False,
            },
        ],
        "Channel Commands": [
            {
                "command": "/new_sale",
                "args": ["wine_name", "buyer", "price"],
                "description": "Creates a new sale transaction.",
                "requires_dev": False,
                "requires_admin": False,
            },
            {
                "command": "/new_split",
                "args": [
                    "wine_name",
                    "price",
                    "buyer_1",
                    "buyer_2",
                    "buyer_3",
                    "buyer_4",
                    "buyer_5",
                    "buyer_6",
                ],
                "description": "Creates a new six bottle split.",
                "requires_dev": False,
                "requires_admin": False,
            },
            {
                "command": "/new_split_3",
                "args": [
                    "wine_name",
                    "price",
                    "buyer_1",
                    "buyer_2",
                    "buyer_3",
                ],
                "description": "Creates a new three bottle split.",
                "requires_dev": False,
                "requires_admin": False,
            },
            {
                "command": "/new_split_12",
                "args": [
                    "wine_name",
                    "price",
                    "buyer_1",
                    "buyer_2",
                    "...",
                    "buyer_11",
                    "buyer_12",
                ],
                "description": "Creates a new twelve bottle split.",
                "requires_dev": False,
                "requires_admin": False,
            },
            {
                "command": "/hello",
                "args": [],
                "description": "Says hello",
                "requires_dev": False,
                "requires_admin": False,
            },
            {
                "command": "/help",
                "args": [],
                "description": "Returns this message",
                "requires_dev": False,
                "requires_admin": False,
            },
            {
                "command": "/ping",
                "args": [],
                "description": "Returns a Pong",
                "requires_dev": False,
                "requires_admin": False,
            },
            {
                "command": "/list",
                "args": [],
                "description": "Returns a list of your transactions",
                "requires_dev": False,
                "requires_admin": False,
            },
            {
                "command": "/stats",
                "args": [],
                "description": f"Returns stats about {config['name']}",
                "requires_dev": False,
                "requires_admin": False,
            },
            {
                "command": "/add_role",
                "args": ["role", "emoji", "message_id"],
                "description": "Add a new role reaction. Emoji is the reaction users will user to add the role, message_id is the id of the message they will react against.",
                "requires_dev": False,
                "requires_admin": True,
            },
            {
                "command": "/lookup",
                "args": ["user"],
                "description": "Lookup another users transactions.",
                "requires_dev": False,
                "requires_admin": False,
            },
        ],
        "DM Commands": [
            {
                "command": "!version",
                "args": [],
                "description": f"Returns the current version of {config['name']}.",
                "requires_dev": False,
                "requires_admin": False,
            },
            {
                "command": "!dev add_reaction",
                "args": ["message_id", "reaction"],
                "description": "Applies the specified reaction to the given message",
                "requires_dev": True,
                "requires_admin": False,
            },
            {
                "command": "!help",
                "args": [],
                "description": "Returns this message",
                "requires_dev": False,
                "requires_admin": False,
            },
            {
                "command": "!dev get_jobs",
                "args": [],
                "description": "Returns a list of the currently scheduled jobs",
                "requires_dev": True,
                "requires_admin": False,
            },
            {
                "command": "!dev clean",
                "args": [],
                "description": f"Cleans completed transactions older than {config['cleanup_delay_hours']}",
                "requires_dev": True,
                "requires_admin": False,
            },
            {
                "command": "!list",
                "args": [],
                "description": "Returns a list of your transactions",
                "requires_dev": False,
                "requires_admin": False,
            },
            {
                "command": "!dev refresh_reminders",
                "args": [],
                "description": "Refreshes the scheduled reminders",
                "requires_dev": True,
                "requires_admin": False,
            },
            {
                "command": "!stats",
                "args": [],
                "description": f"Returns stats about {config['name']}",
                "requires_dev": False,
                "requires_admin": False,
            },
            {
                "command": "!dev refresh_message",
                "args": ["transaction_row_id", "optional: channel_id"],
                "description": "Deletes all existing messages for a given transaction, and posts a new status update",
                "requires_dev": True,
                "requires_admin": False,
            },
            {
                "command": "!dev shutdown",
                "args": [
                    "confirmation_token",
                ],
                "description": "Shutdown ledger_bot, requires a confirmation token that will be displayed when first run",
                "requires_dev": True,
                "requires_admin": False,
            },
            {
                "command": "!dev cancel_shutdown",
                "args": [],
                "description": "Cancels the scheduled shutdown",
                "requires_dev": True,
                "requires_admin": False,
            },
            {
                "command": "!dev welcome_back",
                "args": [],
                "description": "Posts a message saying ledger_bot is running again.",
                "requires_dev": True,
                "requires_admin": False,
            },
        ],
    }

    # Create comma seperated list, with "and" before final element
    if len(config["maintainer_ids"]) > 1:
        maintainers = (
            "<@"
            + ">, <@".join(
                str(maintainer) for maintainer in list(config["maintainer_ids"])[:-1]
            )
            + ">, and <@"
            + str(list(config["maintainer_ids"])[-1])
            + ">"
        )
    else:
        maintainers = f"<@{str(config['maintainer_ids'][0])}>"

    content = []
    prefix = f"{config['name']} allows you to track in-progress sales to other users.\nCreate a new transaction with `/new_sale`. To update a transactions status, react to the message from {config['name']}."
    suffix = f"{config['name']} was built by {maintainers} and is hosted by <https://snailedit.dev/>."

    content.append(prefix)

    for section in sections:
        body = f"\n**{section}**\n"

        # Only checking first element.  Probably not totally safe but works as long as we don't mix list types.
        if "command" in sections[section][0]:
            # Is list of commands

            # Sort by "command" key
            sections[section].sort(key=lambda d: d["command"])

            commands = sections[section]

            for command in commands:
                if command["requires_dev"] and not has_dev_commands:
                    log.info(f"Skipping dev command: {command['command']}")
                elif command["requires_admin"] and not has_admin_commands:
                    log.info(f"Skipping admin command: {command['command']}")
                else:
                    body += f"`{command['command']}"

                    for arg in command["args"]:
                        body += f" <{arg}>"

                    body += f"`: {command['description']}\n"
        elif "reaction" in sections[section][0]:
            # Is list of reactions

            reactions = sections[section]
            for reaction in reactions:
                if reaction["requires_dev"] and not has_dev_commands:
                    log.info(f"Skipping dev reaction: {reaction['reaction']}")
                else:
                    body += f"{reaction['reaction']}: {reaction['description']}\n"

        content.append(body)

    content.append(suffix)

    message = split_message(content)

    return message
