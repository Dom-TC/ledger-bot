"""Slash command - add_user."""

import logging
from typing import Any, Dict

import discord

from ledger_bot.LedgerBot import LedgerBot

log = logging.getLogger(__name__)


async def command_add_user(
    client: "LedgerBot",
    interaction: discord.Interaction[Any],
) -> None:
    """Add user to Airtable."""
    if isinstance(interaction.channel, discord.channel.TextChannel):
        channel_name = interaction.channel.name
    else:
        channel_name = "DM"

    if isinstance(interaction.user, discord.Member):
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

        log.info(f"Adding member: {interaction.user}")
        await client.service.member.get_or_add_member(interaction.user)
        await interaction.response.send_message(
            f"You've been added to the database, {interaction.user.mention}"
        )
