"""Helper functions for generating messages to be sent."""

import logging
from typing import Optional

import discord

log = logging.getLogger(__name__)


def generate_transaction_status_message(
    seller: discord.Member,
    buyer: discord.Member,
    wine_name: str,
    wine_price: float,
    config: dict,
    is_update: Optional[bool] = False,
    is_approved: Optional[bool] = False,
    is_buyer_paid: Optional[bool] = False,
    is_seller_paid: Optional[bool] = False,
    is_buyer_delivered: Optional[list] = False,
    is_seller_delivered: Optional[bool] = False,
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
    is_buyer_paid : bool, optional
        Has the buyer marked the transaction as paid
    is_seller_paid : bool, optional
        Has the buyer marked the transaction as paid
    is_buyer_delivered : bool, optional
        Has the buyer marked the transaction as delivered
    is_seller_delivered : bool, optional
        Has the buyer marked the transaction as delivered
    is_cancelled : bool, optional
        Has the seller marked this transaction as cancelled?

    Returns
    -------
    str
        The string of the message to be posted

    """
    log.info("Generating transaction status message...")

    if is_update:
        # Updated transaction
        title_line = "*Sale Updated*"
    elif is_update and is_cancelled:
        # Cancel transaction
        title_line = "*Sale Cancelled*"
    else:
        # New transaction
        title_line = "*New Sale Listed*"

    user_decleration = f"**{seller.mention} sold {wine_name} to {buyer.mention}**"
    price_decleration = f"Price: £{wine_price}"

    if is_approved:
        approved_decleration = f"Approved: {config['emojis']['status_confirmed']}"
    else:
        approved_decleration = f"Approved: {config['emojis']['status_unconfirmed']} {buyer.mention} please approve this sale by reacting with {config['emojis']['approval']}"

    if is_buyer_paid and is_seller_paid:
        # Both confirmed paid
        paid_decleration = f"Paid:           {config['emojis']['status_confirmed']}"
    elif is_buyer_paid:
        # Buyer confirmed paid
        paid_decleration = f"Paid:           {config['emojis']['status_part_confirmed']} {seller.mention} please confirm this transaction has been paid by reacting with {config['emojis']['paid']}"
    elif is_seller_paid:
        # Seller confirmed paid
        paid_decleration = f"Paid:           {config['emojis']['status_part_confirmed']} {buyer.mention} please confirm this transaction has been paid by reacting with {config['emojis']['paid']}"
    elif is_approved is False:
        paid_decleration = f"Paid:           {config['emojis']['status_unconfirmed']}"
    else:
        paid_decleration = f"Paid:           {config['emojis']['status_unconfirmed']}, to mark this as paid, please react with {config['emojis']['paid']}"

    if is_buyer_delivered and is_seller_delivered:
        # Both confirmed delivered
        delivered_decleration = f"Delivered: {config['emojis']['status_confirmed']}"
    elif is_buyer_delivered:
        # Buyer confirmed delivered
        delivered_decleration = f"Delivered: {config['emojis']['status_part_confirmed']} {seller.mention} please confirm this transaction has been delivered by reacting with {config['emojis']['delivered']}"
    elif is_seller_delivered:
        # Seller confirmed delivered
        delivered_decleration = f"Delivered: {config['emojis']['status_part_confirmed']} {buyer.mention} please confirm this transaction has been delivered by reacting with {config['emojis']['delivered']}"
    elif is_approved is False:
        delivered_decleration = f"Delivered: {config['emojis']['status_unconfirmed']}"
    else:
        delivered_decleration = f"Delivered: {config['emojis']['status_unconfirmed']}, to mark this as delivered, please react with {config['emojis']['delivered']}"

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
    )

    return message_contents


# **@<seller> sold <wine_name> to @<buyer>**
# Price: <price>
# <sale_link>

# **Status:**
# <approved_emoji> Approved:
# <paid_emoji> Paid:
# <delivered_emoji> Delivered:
