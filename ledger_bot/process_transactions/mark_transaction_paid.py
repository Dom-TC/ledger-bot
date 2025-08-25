"""Mark the specified transaction as paid."""

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


async def mark_transaction_paid(
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
    Mark the specified transaction as paid.

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
    transaction = TransactionService.mark_transaction_paid()

    response_contents = generate_transaction_status_message(
        seller=seller,
        buyer=buyer,
        wine_name=target_transaction.wine,
        wine_price=target_transaction.price,
        config=config,
        is_update=True,
        is_approved=target_transaction.sale_approved,
        is_marked_paid_by_buyer=target_transaction.buyer_marked_paid,
        is_marked_paid_by_seller=target_transaction.seller_marked_paid,
        is_marked_delivered_by_buyer=target_transaction.buyer_marked_delivered,
        is_marked_delivered_by_seller=target_transaction.seller_marked_delivered,
        transaction_id=target_transaction.row_id,
    )

    await send_message(
        response_contents=response_contents,
        channel=channel,
        target_transaction=target_transaction,
        previous_message_id=payload.message_id,
        storage=storage,
        config=config,
    )
