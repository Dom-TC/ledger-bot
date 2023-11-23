"""DM command - stats."""

import logging
from typing import TYPE_CHECKING

import discord

from ledger_bot.errors import AirTableError
from ledger_bot.message_generators import generate_stats_message
from ledger_bot.models import Transaction

if TYPE_CHECKING:
    from ledger_bot.LedgerBot import LedgerBot

log = logging.getLogger(__name__)


async def command_stats(
    client: "LedgerBot", message: discord.Message, dm_channel: discord.DMChannel
):
    """DM command - stats."""
    log.info(f"Getting stats for user {message.author.name} ({message.author.id})")

    try:
        transactions = await client.storage.get_all_transactions()
    except AirTableError as error:
        log.error(f"There was an error processing the AirTable request: {error}")
        await dm_channel.send("An unexpected error occured.")
        return

    if len(transactions) == 0:
        dm_channel.send("No transactions have been recorded.")

    for i, transaction in enumerate(transactions):
        transactions[i] = Transaction.from_airtable(transaction)

    response = generate_stats_message(
        transactions=transactions, user_id=message.author.id, storage=client.storage
    )

    await dm_channel.send(response)
