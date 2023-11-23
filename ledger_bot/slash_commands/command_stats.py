"""Slash command - stats."""

import logging
from typing import TYPE_CHECKING

import discord

from ledger_bot.errors import AirTableError
from ledger_bot.message_generators import generate_stats_message
from ledger_bot.models import Transaction
from ledger_bot.storage import AirtableStorage

if TYPE_CHECKING:
    from ledger_bot.LedgerBot import LedgerBot

log = logging.getLogger(__name__)


async def command_stats(
    client: "LedgerBot",
    config: dict,
    storage: AirtableStorage,
    interaction: discord.Interaction,
):
    """DM command - stats."""
    log.info(f"Getting stats for user {interaction.user.name} ({interaction.user.id})")

    # Defer interaction so we can respond to it later
    await interaction.response.defer(ephemeral=True)

    try:
        transactions = await client.storage.get_all_transactions()
    except AirTableError as error:
        log.error(f"There was an error processing the AirTable request: {error}")
        await interaction.response.send_message(
            "An unexpected error occured.", ephemeral=True
        )
        return

    if len(transactions) == 0:
        interaction.response.send_message("No transactions have been recorded.")

    for i, transaction in enumerate(transactions):
        transactions[i] = Transaction.from_airtable(transaction)

    response = generate_stats_message(
        transactions=transactions, user_id=interaction.user.id, storage=client.storage
    )

    await interaction.followup.send(response, ephemeral=True)
