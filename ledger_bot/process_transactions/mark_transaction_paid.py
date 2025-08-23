"""Mark the specified transaction as paid."""

import datetime
import logging
from typing import Any, Dict

import discord

from ledger_bot.message_generators import generate_transaction_status_message
from ledger_bot.models import Transaction
from ledger_bot.storage import AirtableStorage

from .send_message import send_message

log = logging.getLogger(__name__)


async def mark_transaction_paid(
    reactor: discord.Member,
    buyer: discord.User,
    seller: discord.User,
    payload: discord.RawReactionActionEvent,
    channel: discord.abc.GuildChannel,
    target_transaction: Transaction,
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
    if target_transaction.cancelled:
        log.info(
            f"Ignoring {payload.emoji.name} from {reactor.name} on message {payload.message_id} in {channel.name} - Transaction cancelled"
        )
        return

    if reactor.id == buyer.id:
        is_buyer = True
        log.info("Processing buyer marked as paid")
    else:
        is_buyer = False
        log.info("Processing seller marked as paid")

    if is_buyer and target_transaction.buyer_marked_paid:
        log.info(
            f"Ignoring approval on transaction {target_transaction.row_id}. Buyer has aleady marked it as paid"
        )
        return
    elif is_buyer is False and target_transaction.seller_marked_paid:
        log.info(
            f"Ignoring approval on transaction {target_transaction.row_id}. Seller has aleady marked it as paid"
        )
        return

    # Start with empty list so we can add fields as we go
    transaction_fields = []

    if is_buyer:
        transaction_fields.append("buyer_marked_paid")
        target_transaction.buyer_marked_paid = True
    else:
        transaction_fields.append("seller_marked_paid")
        target_transaction.seller_marked_paid = True

    if target_transaction.buyer_marked_paid and target_transaction.seller_marked_paid:
        transaction_fields.append("paid_date")
        target_transaction.paid_date = datetime.datetime.utcnow().isoformat()

    log.debug(f"target_transaction: {target_transaction}")
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
