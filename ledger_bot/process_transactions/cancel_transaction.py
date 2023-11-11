"""Approve the specified transaction."""
import datetime
import logging

import discord

from ledger_bot.message_generators import generate_transaction_status_message
from ledger_bot.models import Transaction
from ledger_bot.storage import AirtableStorage

from ._send_message import _send_message

log = logging.getLogger(__name__)


async def cancel_transaction(
    reactor: discord.Member,
    buyer: discord.Member,
    seller: discord.Member,
    payload,
    channel,
    target_transaction: Transaction,
    config: dict,
    storage: AirtableStorage,
):
    """
    Cancel the specified transaction.

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
        The config dictionar
    """
    if target_transaction.sale_approved:
        log.info(
            f"Ignoring approval on transaction {target_transaction.row_id}. Transaction already approved"
        )
        return

    target_transaction.cancelled = True
    target_transaction.cancelled_date = datetime.datetime.utcnow().isoformat()
    transaction_fields = ["cancelled", "cancelled_date"]

    await storage.save_transaction(
        transaction=target_transaction, fields=transaction_fields
    )

    response_contents = generate_transaction_status_message(
        seller=seller,
        buyer=buyer,
        wine_name=target_transaction.wine,
        wine_price=target_transaction.price,
        config=config,
        is_update=True,
        is_cancelled=True,
    )

    await _send_message(
        response_contents=response_contents,
        channel=channel,
        target_transaction=target_transaction,
        previous_message_id=payload.message_id,
        storage=storage,
        config=config,
    )
