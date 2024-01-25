"""Slash command - add_user."""

import logging
from typing import Any, Dict

import discord

from ledger_bot.LedgerBot import LedgerBot
from ledger_bot.storage import TransactionStorage

log = logging.getLogger(__name__)


async def command_add_user(
    client: "LedgerBot",
    config: Dict[str, Any],
    storage: TransactionStorage,
    interaction: discord.Interaction[Any],
) -> None:
    """Add user to Airtable."""
    if isinstance(interaction.channel, discord.channel.TextChannel):
        channel_name = interaction.channel.name
    else:
        channel_name = "DM"

    if isinstance(interaction.user, discord.Member):
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

        log.info(f"Adding member: {interaction.user}")
        await storage.get_or_add_member(interaction.user)
        await interaction.response.send_message(
            f"You've been added to the database, {interaction.user.mention}"
        )
