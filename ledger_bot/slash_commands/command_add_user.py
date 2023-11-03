"""Slash command - add_user."""

import logging

import discord

from ledger_bot.LedgerBot import LedgerBot
from ledger_bot.storage import AirtableStorage

log = logging.getLogger(__name__)


async def command_add_user(
    client: "LedgerBot",
    config: dict,
    storage: AirtableStorage,
    interaction: discord.Interaction,
):
    """Add user to Airtable."""
    log.info(f"Adding member: {interaction.user}")
    await storage.get_or_add_member(interaction.user)
    await interaction.response.send_message(
        f"You've been added to the database, {interaction.user.mention}"
    )
