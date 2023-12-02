"""Helper functions for generating messages to be sent."""

# flake8: noqa

import logging
from typing import Optional

import discord

log = logging.getLogger(__name__)


def generate_transaction_status_message(
    seller: discord.Member | discord.User,
    buyer: discord.Member | discord.User,
    wine_name: str,
    wine_price: float,
    config: dict,
    is_update: Optional[bool] = False,
    is_approved: Optional[bool] = False,
    is_marked_paid_by_buyer: Optional[bool] = False,
    is_marked_paid_by_seller: Optional[bool] = False,
    is_marked_delivered_by_buyer: Optional[bool] = False,
    is_marked_delivered_by_seller: Optional[bool] = False,
    is_cancelled: Optional[bool] = False,
):
    """
    Generates the text for displaying a transaction status.

    Paramaters
    ----------
    seller : discord.Member
        The seller
    buyer : discord.Member
        The buyer
    wine_name : str,
        The name of the wine being sold
    wine_price : float
        The price of the wine being sold
    config : dict
        The config dictionary
    is_update : bool, optional
        Is this an update of an existing transaction?  If not, presume new transaction
    is_approved : bool, optional
        Has this transaction been confirmed by the buyer
    is_marked_paid_by_buyer : bool, optional
        Has the buyer marked the transaction as paid
    is_marked_paid_by_seller : bool, optional
        Has the seller marked the transaction as paid
    is_marked_delivered_by_buyer : bool, optional
        Has the buyer marked the transaction as delivered
    is_marked_delivered_by_seller : bool, optional
        Has the seller marked the transaction as delivered
    is_cancelled : bool, optional
        Has the seller marked this transaction as cancelled?

    Returns
    -------
    str
        The string of the message to be posted

    """
    log.info("Generating transaction status message...")

    is_complete = False

    if is_cancelled:
        # Cancel transaction
        title_line = "*Sale Cancelled*"
    elif (
        is_update
        and is_approved
        and is_marked_paid_by_buyer
        and is_marked_paid_by_seller
        and is_marked_delivered_by_buyer
        and is_marked_delivered_by_seller
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

    user_decleration = f"**{seller.mention} sold {wine_name} to {buyer.mention}**"
    price_decleration = f"Price: £{'{:.2f}'.format(wine_price)}"

    if is_approved:
        approved_decleration = f"Approved: {config['emojis']['status_confirmed']}"
    else:
        approved_decleration = f"Approved: {config['emojis']['status_unconfirmed']} {buyer.mention} please approve this sale by reacting with {config['emojis']['approval']}"

    if is_marked_paid_by_buyer and is_marked_paid_by_seller:
        # Both confirmed paid
        paid_decleration = f"Paid:           {config['emojis']['status_confirmed']}"
    elif is_marked_paid_by_buyer:
        # Buyer confirmed paid
        paid_decleration = f"Paid:           {config['emojis']['status_part_confirmed']} {seller.mention} please confirm this transaction has been paid by reacting with {config['emojis']['paid']}"
    elif is_marked_paid_by_seller:
        # Seller confirmed paid
        paid_decleration = f"Paid:           {config['emojis']['status_part_confirmed']} {buyer.mention} please confirm this transaction has been paid by reacting with {config['emojis']['paid']}"
    elif is_approved is False:
        paid_decleration = f"Paid:           {config['emojis']['status_unconfirmed']}"
    else:
        paid_decleration = f"Paid:           {config['emojis']['status_unconfirmed']} to mark this as paid, please react with {config['emojis']['paid']}"

    if is_marked_delivered_by_buyer and is_marked_delivered_by_seller:
        # Both confirmed delivered
        delivered_decleration = f"Delivered: {config['emojis']['status_confirmed']}"
    elif is_marked_delivered_by_buyer:
        # Buyer confirmed delivered
        delivered_decleration = f"Delivered: {config['emojis']['status_part_confirmed']} {seller.mention} please confirm this transaction has been delivered by reacting with {config['emojis']['delivered']}"
    elif is_marked_delivered_by_seller:
        # Seller confirmed delivered
        delivered_decleration = f"Delivered: {config['emojis']['status_part_confirmed']} {buyer.mention} please confirm this transaction has been delivered by reacting with {config['emojis']['delivered']}"
    elif is_approved is False:
        delivered_decleration = f"Delivered: {config['emojis']['status_unconfirmed']}"
    else:
        delivered_decleration = f"Delivered: {config['emojis']['status_unconfirmed']} to mark this as delivered, please react with {config['emojis']['delivered']}"

    # Always display as cancelled regardless of other conditions
    if is_cancelled:
        approved_decleration = f"Approved: {config['emojis']['status_cancelled']}"
        paid_decleration = f"Paid:           {config['emojis']['status_cancelled']}"
        delivered_decleration = f"Delivered: {config['emojis']['status_cancelled']}"

    if is_approved is False and is_cancelled is False:
        cancel_message = f"*To cancel this transaction, please react with {config['emojis']['cancel']}*\n"
    else:
        cancel_message = ""

    if not (is_complete or is_cancelled):
        footer_message = f"*To set a reminder for this transaction, please react with {config['emojis']['reminder']} and follow the DMed instructions.*"
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
        + footer_message
    )

    return message_contents


# **@<seller> sold <wine_name> to @<buyer>**
# Price: <price>
# <sale_link>

# **Status:**
# <approved_emoji> Approved:
# <paid_emoji> Paid:
# <delivered_emoji> Delivered:
