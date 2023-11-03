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
    await interaction.response.send_message(f"Hi, {interaction.user.mention}")
