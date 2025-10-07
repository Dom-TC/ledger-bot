"""DM command - help."""

import logging
from typing import TYPE_CHECKING

import discord

from ledger_bot.message_generators import generate_help_message

if TYPE_CHECKING:
    from ledger_bot.LedgerBot import LedgerBot

log = logging.getLogger(__name__)


async def command_help(
    client: "LedgerBot", message: discord.Message, dm_channel: discord.DMChannel
) -> None:
    """DM command - help."""
    has_dev_commands = message.author.id in client.config["maintainer_ids"]
    has_admin_commands = await client.is_admin_or_maintainer(message.author.id)
    response = generate_help_message(
        client.config,
        has_dev_commands=has_dev_commands,
        has_admin_commands=has_admin_commands,
    )

    for msg in response:
        await dm_channel.send(msg)
