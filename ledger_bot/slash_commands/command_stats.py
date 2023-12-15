"""Slash command - stats."""

import logging
from typing import TYPE_CHECKING, Any, Dict, List

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
    config: Dict[str, Any],
    storage: AirtableStorage,
    interaction: discord.Interaction[Any],
) -> None:
    """DM command - stats."""
    log.info(f"Getting stats for user {interaction.user.name} ({interaction.user.id})")

    # Defer interaction so we can respond to it later
    await interaction.response.defer(ephemeral=True)

    try:
        transactions_dict = await client.transaction_storage.get_all_transactions()
    except AirTableError as error:
        log.error(f"There was an error processing the AirTable request: {error}")
        await interaction.response.send_message(
            "An unexpected error occured.", ephemeral=True
        )
        return

    if transactions_dict is None:
        await interaction.response.send_message("No transactions have been recorded.")

    else:
        transactions: List[Transaction] = []
        for transaction_record in transactions_dict:
            transactions.append(Transaction.from_airtable(transaction_record))

        response = generate_stats_message(
            transactions=transactions,
            user_id=interaction.user.id,
            storage=client.transaction_storage,
        )

        await interaction.followup.send(response, ephemeral=True)
