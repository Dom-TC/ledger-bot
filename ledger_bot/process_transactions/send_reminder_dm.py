"""Send a DM instructing how to watch the specified transaction."""
import datetime
import logging

import discord

from ledger_bot.message_generators import generate_transaction_status_message
from ledger_bot.models import Transaction
from ledger_bot.storage import AirtableStorage

from ._send_message import _send_message

log = logging.getLogger(__name__)


async def send_reminder_dm(
    reactor: discord.Member,
    buyer: discord.User,
    seller: discord.User,
    payload,
    channel: discord.abc.GuildChannel,
    target_transaction: Transaction,
    config: dict,
    storage: AirtableStorage,
):
    """
    Send a DM to the reactor, showing how to watch a given transaction.

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
    transaction_id = target_transaction.record_id

    log.info(
        f"{reactor.name} wants to watch {transaction_id}. Sending DM with instructions."
    )

    message_contents = f"To set up alerts for the sale of *{target_transaction.wine}* from {buyer.mention} to {seller.mention} for £{target_transaction.price}.\n"
    message_contents += "Please use one of the following commands:\n"
    message_contents += f"!reminder {transaction_id} <number> <days|hours>` - Recieve a reminder in the seleced number of days or hours\n"
    message_contents += f"`!reminder {transaction_id} <number> <days|hours> <approved|cancelled|paid|delivered|complete>` - Recieve a reminder in the selected number of days or hours if the given status hasn't been met"

    await reactor.send(message_contents)
