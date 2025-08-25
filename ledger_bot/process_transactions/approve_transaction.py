"""Approve the specified transaction."""
import datetime
import logging
from typing import Any, Dict

import discord

from ledger_bot.message_generators import generate_transaction_status_message
from ledger_bot.models import TransactionAirtable
from ledger_bot.services.transaction_service import TransactionService
from ledger_bot.storage_airtable import AirtableStorage

from .send_message import send_message

log = logging.getLogger(__name__)


async def approve_transaction(
    reactor: discord.Member,
    buyer: discord.User,
    seller: discord.User,
    payload: discord.RawReactionActionEvent,
    channel: discord.abc.GuildChannel,
    target_transaction: TransactionAirtable,
    config: Dict[str, Any],
    storage: AirtableStorage,
) -> None:
    """
    Approve the specified transaction.

    Paramaters
    ----------
    reactor : discord.Member
        The user who made the reaction
    buyer : discord.Member
        The Member object of the buyer
    seller : discord.Member
        The Member object of the seller
    payload
        The payload of the reaction
    channel
        The channel the transaction was made in
    target_transaction : Transaction
        The transaction being processed
    config : dict
        The config dictionary

    """
    transaction = TransactionService.approve_transaction()

    response_contents = generate_transaction_status_message(
        seller=seller,
        buyer=buyer,
        wine_name=target_transaction.wine,
        wine_price=target_transaction.price,
        config=config,
        transaction_id=target_transaction.row_id,
        is_update=True,
        is_approved=True,
    )

    await send_message(
        response_contents=response_contents,
        channel=channel,
        target_transaction=target_transaction,
        previous_message_id=payload.message_id,
        storage=storage,
        config=config,
    )
