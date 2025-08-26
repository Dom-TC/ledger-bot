"""Slash command - help."""

import logging
from typing import TYPE_CHECKING, Any, Dict

import discord

from ledger_bot.message_generators import generate_help_message

if TYPE_CHECKING:
    from ledger_bot.LedgerBot import LedgerBot

log = logging.getLogger(__name__)


async def command_help(
    client: "LedgerBot",
    interaction: discord.Interaction[Any],
) -> None:
    """Return a help message."""
    if isinstance(interaction.channel, discord.channel.TextChannel):
        channel_name = interaction.channel.name
    else:
        channel_name = "DM"

    if channel_name in client.config["channels"].get("exclude", []):
        log.info(
            f"Ignoring slash command from {interaction.user.name} in {channel_name}  - Channel in exclude list"
        )
        await interaction.response.send_message(
            content=f"{client.config['name']} is not available in this channel.",
            ephemeral=True,
        )
        return

    has_dev_commands = interaction.user.id in client.config["maintainer_ids"]
    has_admin_commands = await client.is_admin_or_maintainer(interaction.user.id)
    response = generate_help_message(
        client.config,
        has_dev_commands=has_dev_commands,
        has_admin_commands=has_admin_commands,
    )
    await interaction.response.send_message(response, ephemeral=True)
