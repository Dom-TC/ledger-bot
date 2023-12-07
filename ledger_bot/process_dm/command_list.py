"""DM command - list."""

import logging
from typing import TYPE_CHECKING, List

import discord

from ledger_bot.errors import AirTableError
from ledger_bot.message_generators import generate_list_message
from ledger_bot.models import Transaction

if TYPE_CHECKING:
    from ledger_bot.LedgerBot import LedgerBot

log = logging.getLogger(__name__)


async def command_list(
    client: "LedgerBot", message: discord.Message, dm_channel: discord.DMChannel
) -> None:
    """DM command - list."""
    log.info(f"Getting transactions for user {message.author.name}")

    try:
        transactions_dict = await client.storage.get_users_transaction(
            str(message.author.id)
        )
    except AirTableError as error:
        log.error(f"There was an error processing the AirTable request: {error}")
        await dm_channel.send("An unexpected error occured.")
        return

    if transactions_dict is None:
        await dm_channel.send("You don't have any transactions.")
    else:
        transactions: List[Transaction] = []
        for transaction_record in transactions_dict:
            log.debug(transaction_record)
            transactions.append(Transaction.from_airtable(transaction_record))

        response = await generate_list_message(
            transactions=transactions, user_id=message.author.id, storage=client.storage
        )

        for transmit_message in response:
            await dm_channel.send(transmit_message)
