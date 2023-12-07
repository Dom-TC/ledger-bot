"""DM command - list."""

import logging
from typing import TYPE_CHECKING, Any, Dict, List

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
    config: Dict[str, Any],
    storage: AirtableStorage,
    interaction: discord.Interaction[Any],
) -> None:
    """DM command - list."""
    log.info(
        f"Getting transactions for user {interaction.user.name} ({interaction.user.id})"
    )

    # Discord Interactions need to be responded to in <3s or they time out.
    # Depending on the number of transactions a user has, we could take longer, so defer the interaction.
    await interaction.response.defer(ephemeral=True)

    try:
        transactions_dict = await client.storage.get_users_transaction(
            str(interaction.user.id)
        )
    except AirTableError as error:
        log.error(f"There was an error processing the AirTable request: {error}")
        await interaction.response.send_message(
            "An unexpected error occured.", ephemeral=True
        )
        return

    if transactions_dict is None:
        await interaction.response.send_message("You don't have any transactions.")
    else:
        transactions: List[Transaction] = []
        for transaction_record in transactions_dict:
            log.debug(transaction_record)
            transactions.append(Transaction.from_airtable(transaction_record))

        response = await generate_list_message(
            transactions=transactions,
            user_id=interaction.user.id,
            storage=client.storage,
        )

        for transmit_message in response:
            await interaction.followup.send(transmit_message, ephemeral=True)
