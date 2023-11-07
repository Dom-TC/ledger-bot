"""Slash command - hello."""

import logging

import discord

from ledger_bot.LedgerBot import LedgerBot
from ledger_bot.storage import AirtableStorage

log = logging.getLogger(__name__)


async def command_hello(
    client: "LedgerBot",
    config: dict,
    storage: AirtableStorage,
    interaction: discord.Interaction,
):
    """Says hello."""
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

    await interaction.response.send_message(f"Hi, {interaction.user.mention}")
