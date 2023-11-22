"""DM command - list."""

import logging
from typing import TYPE_CHECKING

import discord

from ledger_bot.message_generators import generate_list_message
from ledger_bot.models import Transaction

if TYPE_CHECKING:
    from ledger_bot.LedgerBot import LedgerBot

log = logging.getLogger(__name__)


async def command_list(
    client: "LedgerBot", message: discord.Message, dm_channel: discord.DMChannel
):
    """DM command - list."""
    log.info(f"Getting transactions for user {message.author.name}")

    transactions = await client.storage.get_users_transaction(str(message.author.id))

    if transactions is None:
        await dm_channel.send("You don't have any open transactions.")
    else:
        for i, transaction_record in enumerate(transactions):
            log.debug(transaction_record)
            transactions[i] = Transaction.from_airtable(transaction_record)

        response = await generate_list_message(
            transactions=transactions, user_id=message.author.id, storage=client.storage
        )

        for transmit_message in response:
            await dm_channel.send(transmit_message)
