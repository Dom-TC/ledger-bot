"""DM command - list."""

import logging
from typing import TYPE_CHECKING, List

import discord

from ledger_bot.errors import AirTableError
from ledger_bot.message_generators import generate_list_message
from ledger_bot.models import TransactionAirtable

if TYPE_CHECKING:
    from ledger_bot.LedgerBot import LedgerBot

log = logging.getLogger(__name__)


async def command_list(
    client: "LedgerBot", message: discord.Message, dm_channel: discord.DMChannel
) -> None:
    """DM command - list."""
    log.info(f"Getting transactions for user {message.author.name}")

    try:
        transactions = await client.transaction_storage.get_users_transaction(
            str(message.author.id)
        )
    except AirTableError as error:
        log.error(f"There was an error processing the AirTable request: {error}")
        await dm_channel.send("An unexpected error occured.")
        return

    if transactions is None:
        await dm_channel.send("You don't have any transactions.")
    else:
        response = await generate_list_message(
            transactions=transactions,
            user_id=message.author.id,
            storage=client.transaction_storage,
        )

        for transmit_message in response:
            await dm_channel.send(transmit_message)
