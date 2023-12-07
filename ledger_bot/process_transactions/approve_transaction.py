"""Approve the specified transaction."""
import datetime
import logging
from typing import Any, Dict

import discord

from ledger_bot.message_generators import generate_transaction_status_message
from ledger_bot.models import Transaction
from ledger_bot.storage import AirtableStorage

from .send_message import send_message

log = logging.getLogger(__name__)


async def approve_transaction(
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
    if target_transaction.cancelled:
        log.info(
            f"Ignoring {payload.emoji.name} from {reactor.name} on message {payload.message_id} in {channel.name} - Transaction cancelled"
        )
        return

    if reactor.id != buyer.id:
        log.info(
            f"Ignoring {payload.emoji.name} from {reactor.name} on message {payload.message_id} in {channel.name} - Reactor is not the buyer"
        )
        return

    if target_transaction.sale_approved:
        log.info(
            f"Ignoring approval on transaction {target_transaction.row_id}. Transaction already approved"
        )
        return

    target_transaction.sale_approved = True
    target_transaction.approved_date = datetime.datetime.utcnow().isoformat()
    transaction_fields = ["sale_approved", "approved_date"]
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
