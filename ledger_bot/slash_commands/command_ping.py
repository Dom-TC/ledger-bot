"""Slash command - Ping."""

import logging
from typing import Any

import discord

from ledger_bot.LedgerBot import LedgerBot

log = logging.getLogger(__name__)


async def command_ping(
    client: "LedgerBot",
    interaction: discord.Interaction[Any],
) -> None:
    """Pong."""
    if isinstance(interaction.channel, discord.channel.TextChannel):
        channel_name = interaction.channel.name
    else:
        channel_name = "DM"

    if (
        client.config["channels"].get("include")
        and channel_name not in client.config["channels"]["include"]
    ):
        log.info(
            f"Ignoring slash command from {interaction.user.name} in {channel_name}  - Channel not in include list"
        )
        await interaction.response.send_message(
            content=f"{client.config['name']} is not available in this channel.",
            ephemeral=True,
        )
        return
    elif channel_name in client.config["channels"].get("exclude", []):
        log.info(
            f"Ignoring slash command from {interaction.user.name} in {channel_name}  - Channel in exclude list"
        )
        await interaction.response.send_message(
            content=f"{client.config['name']} is not available in this channel.",
            ephemeral=True,
        )
        return

    log.info(f"Ping to {interaction.user.name}")
    await interaction.response.send_message(
        f"Pong! ({interaction.client.latency * 1000}ms)"
    )
