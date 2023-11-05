"""Generate help message text."""

import logging

log = logging.getLogger(__name__)


def generate_help_message(config: dict, has_dev_commands: bool = False) -> str:
    """Generates help text.

    Taking into account whether someone has access to dev commands

    Parameters
    ----------
    config: dict
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
    # Each command is a dict, containing "command", "args", "description", "requires_dev"
    # Each reaction is a dict, containing "reaction", "description", "requires_dev"
    sections = {
        "Reactions": [
            {
                "reaction": config["emojis"]["approval"],
                "description": "Approve a transaction.",
                "requires_dev": False,
            },
            {
                "reaction": config["emojis"]["paid"],
                "description": "Mark a transaction as paid.",
                "requires_dev": False,
            },
            {
                "reaction": config["emojis"]["delivered"],
                "description": "Mark a transaction as delivered.",
                "requires_dev": False,
            },
        ],
        "Channel Commands": [
            {
                "command": "/new_sale",
                "args": ["wine_name", "buyer", "price"],
                "description": "Creates a new sale transaction.",
                "requires_dev": False,
            },
            {
                "command": "/hello",
                "args": [],
                "description": "Says hello",
                "requires_dev": False,
            },
            {
                "command": "/add_user",
                "args": [],
                "description": "Adds you to the table",
                "requires_dev": False,
            },
            {
                "command": "/help",
                "args": [],
                "description": "Returns this message",
                "requires_dev": False,
            },
        ],
        "DM Commands": [
            {
                "command": "!version",
                "args": [],
                "description": f"Returns the current version of {config['name']}.",
                "requires_dev": False,
            },
            {
                "command": "!dev add_reaction",
                "args": ["message_id", "reaction"],
                "description": "Applies the specified reaction to the given message",
                "requires_dev": True,
            },
            {
                "command": "!help",
                "args": [],
                "description": "Returns this message",
                "requires_dev": False,
            },
        ],
    }

    # Create comma seperated list, with "and" before final element
    maintainers = (
        "<@"
        + ">, <@".join(
            str(maintainer) for maintainer in list(config["maintainer_ids"])[:-1]
        )
        + ">, and <@"
        + str(list(config["maintainer_ids"])[-1])
        + ">"
    )

    prefix = f"{config['name']} allows you to track in-progress sales to other users.\nCreate a new transaction with `/new_sale`. To update a transactions status, react to the message from {config['name']}."
    suffix = f"{config['name']} was built by {maintainers}."

    body = ""
    for section in sections:
        body += f"\n**{section}**\n"

        # Only checking first element.  Probably not totally safe but works as long as we don't mix list types.
        if "command" in sections[section][0]:
            # Is list of commands

            # Sort by "command" key
            sections[section].sort(key=lambda d: d["command"])

            commands = sections[section]

            for command in commands:
                if command["requires_dev"] and not has_dev_commands:
                    log.info(f"Skipping dev command: {command['command']}")
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
                    log.info(f"Skipping dev reaction: {reaction['command']}")
                else:
                    body += f"{reaction['reaction']}: {reaction['description']}\n"

    response = prefix + "\n" + body + "\n" + suffix
    return response
