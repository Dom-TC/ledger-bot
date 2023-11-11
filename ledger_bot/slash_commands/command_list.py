"""DM command - list."""

import logging
from typing import TYPE_CHECKING

import discord

from ledger_bot.errors import AirTableError
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
    log.info(
        f"Getting transactions for user {interaction.user.name} ({interaction.user.id})"
    )

    # Discord Interactions need to be responded to in <3s or they time out.
    # Depending on the number of transactions a user has, we could take longer, so defer the interaction.
    await interaction.response.defer(ephemeral=True)

    try:
        transactions = await client.storage.get_users_transaction(interaction.user.id)
    except AirTableError as error:
        log.error(f"There was an error processing the AirTable request: {error}")
        await interaction.response.send_message(
            "An unexpected error occured.", ephemeral=True
        )
        return

    if len(transactions) == 0:
        interaction.response.send_message("You don't have any open transactions.")

    for i, transaction in enumerate(transactions):
        transactions[i] = Transaction.from_airtable(transaction)

    response = await generate_list_message(
        transactions=transactions, user_id=interaction.user.id, storage=client.storage
    )

    for message in response:
        await interaction.followup.send(message, ephemeral=True)
