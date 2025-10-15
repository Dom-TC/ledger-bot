"""Helper functions for generating messages to be sent."""

# flake8: noqa

import logging
from typing import TYPE_CHECKING, Optional

from ledger_bot.config import Config
from ledger_bot.models import Transaction

if TYPE_CHECKING:
    from ledger_bot.clients import TransactionsClient

log = logging.getLogger(__name__)


async def generate_transaction_status_message(
    transaction: Transaction,
    client: "TransactionsClient",
    config: Config,
    is_update: Optional[bool] = False,
) -> str:
    """
    Generates the text for displaying a transaction status.

    Paramaters
    ----------
    transaction: Transaction
        The transaction
    client: TransactionsClient,
        The client posting the message
    config : dict
        The config dictionary
    is_update : bool, optional
        Is this an update of an existing transaction?  If not, presume new transaction

    Returns
    -------
    str
        The string of the message to be posted

    """
    log.info("Generating transaction status message...")

    is_complete = False

    if transaction.cancelled:
        # Cancel transaction
        title_line = "*Sale Cancelled*"
    elif (
        is_update
        and transaction.sale_approved
        and transaction.buyer_paid
        and transaction.seller_paid
        and transaction.buyer_delivered
        and transaction.seller_delivered
    ):
        # Sale completed
        title_line = "*Sale Completed*"
        is_complete = True
    elif is_update:
        # Updated transaction
        title_line = "*Sale Updated*"
    else:
        # New transaction
        title_line = "*New Sale Listed*"

    seller = await client.get_or_fetch_user(transaction.seller.discord_id)
    buyer = await client.get_or_fetch_user(transaction.buyer.discord_id)
    user_decleration = (
        f"**{seller.mention} sold {transaction.wine} to {buyer.mention}**"
    )
    price_decleration = f"Price: £{'{:.2f}'.format(transaction.price)}"

    if transaction.sale_approved:
        approved_decleration = f"Approved: {config.emojis.status_confirmed}"
    else:
        approved_decleration = f"Approved: {config.emojis.status_unconfirmed} {buyer.mention} please approve this sale by reacting with {config.emojis.approval}"

    if transaction.buyer_paid and transaction.seller_paid:
        # Both confirmed paid
        paid_decleration = f"Paid:           {config.emojis.status_confirmed}"
    elif transaction.buyer_paid:
        # Buyer confirmed paid
        paid_decleration = f"Paid:           {config.emojis.status_part_confirmed} {seller.mention} please confirm this transaction has been paid by reacting with {config.emojis.paid}"
    elif transaction.seller_paid:
        # Seller confirmed paid
        paid_decleration = f"Paid:           {config.emojis.status_part_confirmed} {buyer.mention} please confirm this transaction has been paid by reacting with {config.emojis.paid}"
    elif transaction.sale_approved is False:
        paid_decleration = f"Paid:           {config.emojis.status_unconfirmed}"
    else:
        paid_decleration = f"Paid:           {config.emojis.status_unconfirmed} to mark this as paid, please react with {config.emojis.paid}"

    if transaction.buyer_delivered and transaction.seller_delivered:
        # Both confirmed delivered
        delivered_decleration = f"Delivered: {config.emojis.status_confirmed}"
    elif transaction.buyer_delivered:
        # Buyer confirmed delivered
        delivered_decleration = f"Delivered: {config.emojis.status_part_confirmed} {seller.mention} please confirm this transaction has been delivered by reacting with {config.emojis.delivered}"
    elif transaction.seller_delivered:
        # Seller confirmed delivered
        delivered_decleration = f"Delivered: {config.emojis.status_part_confirmed} {buyer.mention} please confirm this transaction has been delivered by reacting with {config.emojis.delivered}"
    elif transaction.sale_approved is False:
        delivered_decleration = f"Delivered: {config.emojis.status_unconfirmed}"
    else:
        delivered_decleration = f"Delivered: {config.emojis.status_unconfirmed} to mark this as delivered, please react with {config.emojis.delivered}"

    # Always display as cancelled regardless of other conditions
    if transaction.cancelled:
        approved_decleration = f"Approved: {config.emojis.status_cancelled}"
        paid_decleration = f"Paid:           {config.emojis.status_cancelled}"
        delivered_decleration = f"Delivered: {config.emojis.status_cancelled}"

    log.debug(f"approved: {transaction.sale_approved}")
    log.debug(f"cancelled: {transaction.cancelled}")
    if not transaction.sale_approved and not transaction.cancelled:
        cancel_message = (
            f"*To cancel this transaction, please react with {config.emojis.cancel}*\n"
        )
    else:
        cancel_message = ""

    if not (is_complete or transaction.cancelled):
        reminder_message = f"*To set a reminder for this transaction, please react with {config.emojis.reminder} and follow the DMed instructions.*\n"
    else:
        reminder_message = ""

    if transaction.id:
        footer_message = f"-# Transaction ID: {str(transaction.id)}"
    else:
        footer_message = ""

    # Build message_contents from components
    message_contents = (
        title_line
        + "\n"
        + user_decleration
        + "\n"
        + price_decleration
        + "\n\n**Status**\n"
        + approved_decleration
        + "\n"
        + paid_decleration
        + "\n"
        + delivered_decleration
        + "\n"
        + "\n"
        + cancel_message
        + reminder_message
        + footer_message
    )

    return message_contents
