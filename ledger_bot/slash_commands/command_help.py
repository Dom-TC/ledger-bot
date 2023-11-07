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
    channel_name = interaction.channel.name

    if (
        config["channels"].get("include")
        and channel_name not in config["channels"]["include"]
    ):
        log.info(
            f"Ignoring slash command from {interaction.user.name} in {channel_name}  - Channel not in include list"
        )
        await interaction.response.send_message(
            content=f"{config['name']} is not available in this channel.",
            ephemeral=True,
        )
        return
    elif channel_name in config["channels"].get("exclude", []):
        log.info(
            f"Ignoring slash command from {interaction.user.name} in {channel_name}  - Channel in exclude list"
        )
        await interaction.response.send_message(
            content=f"{config['name']} is not available in this channel.",
            ephemeral=True,
        )
        return

    has_dev_commands = interaction.user.id in client.config["maintainer_ids"]
    response = generate_help_message(client.config, has_dev_commands)
    await interaction.response.send_message(response, ephemeral=True)
