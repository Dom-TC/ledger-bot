"""DM command - list."""

import logging
from typing import TYPE_CHECKING

import discord

from ledger_bot.message_generators import generate_list_message
from ledger_bot.models import Transaction
from ledger_bot.storage import AirtableStorage

if TYPE_CHECKING:
    from ledger_bot.LedgerBot import LedgerBot

log = logging.getLogger(__name__)


async def command_list(
    client: "LedgerBot",
    config: dict,
    storage: AirtableStorage,
    interaction: discord.Interaction,
):
    """DM command - list."""
    log.info(f"Getting transactions for user {interaction.name}")

    transactions = await client.storage.get_users_transaction(interaction.id)

    if len(transactions) == 0:
        interaction.response.send_message("You don't have any open transactions.")

    for i, transaction in enumerate(transactions):
        transactions[i] = Transaction.from_airtable(transaction)

    response = await generate_list_message(
        transactions=transactions, user_id=interaction.id, storage=client.storage
    )

    await interaction.response.send_message(response, ephemeral=True)
