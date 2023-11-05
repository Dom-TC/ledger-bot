"""Slash command - help."""

import logging
from typing import TYPE_CHECKING

import discord

from ledger_bot.message_generators import generate_help_message
from ledger_bot.storage import AirtableStorage

if TYPE_CHECKING:
    from ledger_bot.LedgerBot import LedgerBot

log = logging.getLogger(__name__)


async def command_help(
    client: "LedgerBot",
    config: dict,
    storage: AirtableStorage,
    interaction: discord.Interaction,
):
    """Return a help message."""
    has_dev_commands = interaction.user.id in client.config["maintainer_ids"]
    response = generate_help_message(client.config, has_dev_commands)
    await interaction.response.send_message(response, ephemeral=True)
