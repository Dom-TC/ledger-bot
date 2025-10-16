"""Helper functions for generating messages to be sent."""

import logging
from typing import Any, Dict

import discord

from ledger_bot.core import Config

log = logging.getLogger(__name__)


def generate_reminder_status_message(
    seller: discord.User,
    buyer: discord.User,
    wine_name: str,
    wine_price: float,
    config: Config,
    is_approved: bool | None = False,
    is_marked_paid_by_buyer: bool | None = False,
    is_marked_paid_by_seller: bool | None = False,
    is_marked_delivered_by_buyer: bool | None = False,
    is_marked_delivered_by_seller: bool | None = False,
    is_cancelled: bool | None = False,
) -> str:
    """Generate a status message for use in reminders."""
    log.info("Generating transaction status message...")

    user_decleration = f"**{seller.mention} sold {wine_name} to {buyer.mention}**"
    price_decleration = f"Price: £{'{:.2f}'.format(wine_price)}"

    if is_approved:
        approved_decleration = f"Approved: {config.emojis.status_confirmed}"
    elif is_cancelled:
        approved_decleration = f"Approved: {config.emojis.status_cancelled}"
    else:
        approved_decleration = f"Approved: {config.emojis.status_unconfirmed}"

    if is_marked_paid_by_buyer and is_marked_paid_by_seller:
        # Both confirmed paid
        paid_decleration = f"Paid:           {config.emojis.status_confirmed}"
    elif is_marked_paid_by_buyer or is_marked_paid_by_seller:
        # Buyer or seller confirmed paid
        paid_decleration = f"Paid:           {config.emojis.status_part_confirmed}"
    elif is_cancelled:
        paid_decleration = f"Paid:           {config.emojis.status_cancelled}"
    elif is_approved is False:
        paid_decleration = f"Paid:           {config.emojis.status_unconfirmed}"
    else:
        paid_decleration = f"Paid:           {config.emojis.status_unconfirmed}"

    if is_marked_delivered_by_buyer and is_marked_delivered_by_seller:
        # Both confirmed delivered
        delivered_decleration = f"Delivered: {config.emojis.status_confirmed}"
    elif is_marked_delivered_by_buyer or is_marked_delivered_by_seller:
        # Buyer or seller confirmed delivered
        delivered_decleration = f"Delivered: {config.emojis.status_part_confirmed}"
    elif is_cancelled:
        delivered_decleration = f"Delivered: {config.emojis.status_cancelled}"
    elif is_approved is False:
        delivered_decleration = f"Delivered: {config.emojis.status_unconfirmed}"
    else:
        delivered_decleration = f"Delivered: {config.emojis.status_unconfirmed}"

    # Build message_contents from components
    message_contents = (
        user_decleration
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
